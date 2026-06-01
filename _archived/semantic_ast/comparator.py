"""semantic_ast.comparator - 新旧架构输出对比工具

用于验证 semantic_ast 模块与旧架构输出的一致性。

Usage:
    from semantic_ast.comparator import compare_outputs
    result = compare_outputs(sv_code, verbose=True)
"""

import pyslang
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# 旧架构
from scope.builder import ScopeBuilder
from scope.symbol_table import SymbolTable
from extractors import SemanticGraph, DriverExtractor, LoadExtractor


@dataclass
class DriverPointOld:
    """旧架构 DriverPoint"""
    signal: str
    driver: str  # 驱动源
    kind: str
    line: int = 0
    clock: str = ""
    reset: str = ""


@dataclass
class DiffResult:
    """对比结果"""
    passed: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    old_signals: set = field(default_factory=set)
    new_signals: set = field(default_factory=set)
    missing_signals: set = field(default_factory=set)
    extra_signals: set = field(default_factory=set)
    driver_diff: Dict[str, Tuple[List, List]] = field(default_factory=dict)  # signal -> (old_drivers, new_drivers)


def _run_old_flow(sv_code: str) -> Dict[str, List[DriverPointOld]]:
    """运行旧架构 3-Pass 流程"""
    tree = pyslang.SyntaxTree.fromText(sv_code)
    
    # Pass 1: ScopeBuilder
    builder = ScopeBuilder()
    scope_tree, symbol_table = builder.build(tree)
    
    # Pass 2: SemanticGraph + Extractors
    graph = SemanticGraph(scope_tree, symbol_table)
    driver_extractor = DriverExtractor(scope_tree, symbol_table, graph)
    driver_extractor.extract(tree)
    
    load_extractor = LoadExtractor(scope_tree, symbol_table, graph)
    load_extractor.extract(tree)
    
    # 转换为兼容格式
    drivers = {}
    for sig, driver_points in graph.drivers.items():
        drivers[sig] = [
            DriverPointOld(
                signal=sig,
                driver=getattr(dp, 'driver', str(dp)),
                kind=getattr(dp, 'kind', 'unknown'),
                clock=getattr(dp, 'clock', ''),
                reset=getattr(dp, 'reset', ''),
            )
            for dp in driver_points
        ]
    
    return drivers


def _run_new_flow(sv_code: str) -> Dict[str, List[DriverPointOld]]:
    """运行新架构 semantic_ast 流程"""
    from semantic_ast import SemanticASTBuilder, SemanticRelationGraph
    
    tree = pyslang.SyntaxTree.fromText(sv_code)
    builder = SemanticASTBuilder()
    sem_ast = builder.build(tree)
    graph = SemanticRelationGraph(sem_ast)
    
    # 转换为兼容格式
    drivers = {}
    for sig in sem_ast.all_signals:
        drivers[sig.name] = [
            DriverPointOld(
                signal=sig.name,
                source=drv.source_expr,
                kind=drv.kind,
                clock=drv.clock,
                reset=drv.reset,
            )
            for drv in sig.drivers
        ]
    
    return drivers


def _normalize_driver_source(source: str) -> str:
    """规范化驱动源表达式用于比较"""
    if not source:
        return ""
    # 移除空白
    normalized = ' '.join(source.split())
    return normalized


def _compare_drivers(
    old_drivers: List[DriverPointOld],
    new_drivers: List[DriverPointOld]
) -> Tuple[bool, List[str]]:
    """比较两组 driver"""
    errors = []
    
    if len(old_drivers) != len(new_drivers):
        errors.append(
            f"  Driver count mismatch: old={len(old_drivers)}, new={len(new_drivers)}"
        )
    
    # 按 source 排序比较
    old_sources = sorted([_normalize_driver_source(d.source) for d in old_drivers])
    new_sources = sorted([_normalize_driver_source(d.source) for d in new_drivers])
    
    if old_sources != new_sources:
        errors.append(f"  Old sources: {old_sources}")
        errors.append(f"  New sources: {new_sources}")
    
    # 比较 clock/reset
    old_clocks = set([d.clock for d in old_drivers if d.clock])
    new_clocks = set([d.clock for d in new_drivers if d.clock])
    if old_clocks != new_clocks:
        errors.append(f"  Clock mismatch: old={old_clocks}, new={new_clocks}")
    
    old_resets = set([d.reset for d in old_drivers if d.reset])
    new_resets = set([d.reset for d in new_drivers if d.reset])
    if old_resets != new_resets:
        errors.append(f"  Reset mismatch: old={old_resets}, new={new_resets}")
    
    return len(errors) == 0, errors


def compare_outputs(sv_code: str, verbose: bool = False) -> DiffResult:
    """对比新旧架构的输出差异
    
    Args:
        sv_code: SystemVerilog 代码
        verbose: 是否打印详细信息
    
    Returns:
        DiffResult: 对比结果
    """
    result = DiffResult()
    
    try:
        old_drivers = _run_old_flow(sv_code)
        new_drivers = _run_new_flow(sv_code)
    except Exception as e:
        result.passed = False
        result.errors.append(f"Execution error: {e}")
        return result
    
    # 信号集合对比
    result.old_signals = set(old_drivers.keys())
    result.new_signals = set(new_drivers.keys())
    result.missing_signals = result.old_signals - result.new_signals
    result.extra_signals = result.new_signals - result.old_signals
    
    if result.missing_signals:
        result.warnings.append(f"Missing signals in new: {result.missing_signals}")
    if result.extra_signals:
        result.warnings.append(f"Extra signals in new: {result.extra_signals}")
    
    # 共同信号的 driver 对比
    common_signals = result.old_signals & result.new_signals
    for sig in sorted(common_signals):
        old_list = old_drivers[sig]
        new_list = new_drivers[sig]
        
        matched, errors = _compare_drivers(old_list, new_list)
        if not matched:
            result.passed = False
            result.driver_diff[sig] = (old_list, new_list)
            result.errors.append(f"Signal '{sig}':")
            result.errors.extend(errors)
    
    if verbose:
        if result.passed:
            count = len(common_signals)
            print(f"PASSED ({count} signals)")
        else:
            err_count = len(result.errors)
            print(f"FAILED ({err_count} errors)")
            for err in result.errors[:10]:
                print(f"  {err}")
            if len(result.errors) > 10:
                excess = len(result.errors) - 10
                print(f"  ... and {excess} more errors")

    return result


def run_benchmark_comparison(benchmark_dir: str = "benchmarks", limit: int = None) -> Dict[str, DiffResult]:
    """运行多个基准测试文件的对比
    
    Args:
        benchmark_dir: 基准测试文件目录
        limit: 最多处理文件数
    
    Returns:
        Dict[str, DiffResult]: 文件名 -> 对比结果
    """
    import os
    import glob
    
    results = {}
    sv_files = glob.glob(f"{benchmark_dir}/*.sv")[:limit]
    
    for sv_file in sv_files:
        filename = os.path.basename(sv_file)
        print(f"Testing {filename}...", end=" ")
        
        try:
            with open(sv_file) as f:
                code = f.read()
            
            result = compare_outputs(code, verbose=False)
            results[filename] = result
            
            if result.passed:
                print(f"✅")
            else:
                err_count = len(result.errors)
                print(f"FAILED ({err_count} errors)")
        except Exception as e:
            print(f"⚠️ {e}")
            results[filename] = DiffResult(passed=False, errors=[str(e)])
    
    return results


if __name__ == "__main__":
    # 运行基准测试对比
    print("=" * 60)
    print("Running benchmark comparison...")
    print("=" * 60)
    
    results = run_benchmark_comparison(limit=10)
    
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    passed = sum(1 for r in results.values() if r.passed)
    failed = sum(1 for r in results.values() if not r.passed)
    
    print(f"Passed: {passed}/{len(results)}")
    print(f"Failed: {failed}/{len(results)}")
    
    if failed > 0:
        print()
        print("Failed benchmarks:")
        for name, result in results.items():
            if not result.passed:
                print(f"  - {name}")
                for err in result.errors[:3]:
                    print(f"      {err}")