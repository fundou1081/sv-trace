"""
ProjectAnalyzer - 项目分析器 (基于pyslang)
"""

import os
import sys
from typing import Dict, List, Tuple
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from parse import SVParser
from debug.analyzers.code_metrics_analyzer import CodeMetricsAnalyzer
from trace.driver import DriverCollector


@dataclass
class ModuleMetrics:
    name: str
    path: str
    
    # Basic metrics
    signals: int = 0
    io_count: int = 0
    total_lines: int = 0
    comment_lines: int = 0
    
    # Design metrics
    always_ff: int = 0
    always_comb: int = 0
    always_latch: int = 0
    if_count: int = 0
    case_count: int = 0
    parameter_count: int = 0
    localparam_count: int = 0
    
    # Complexity metrics
    complexity_score: int = 0
    
    # CDC metrics
    multi_clock: int = 0
    no_reset: int = 0
    
    # Compute metrics
    and_count: int = 0
    or_count: int = 0
    add_count: int = 0
    mul_count: int = 0
    div_count: int = 0
    
    # Signal width
    max_reg_width: int = 0
    max_io_width: int = 0
    
    # Fanout metrics
    max_fanout: int = 0
    high_fanout_signals: List[str] = field(default_factory=list)
    
    # Verification metrics
    assert_count: int = 0
    cover_count: int = 0
    rand_count: int = 0
    tb_exists: bool = False
    
    # Quality metrics
    comment_ratio: float = 0.0


class ProjectAnalyzer:
    """项目分析器"""
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.modules: List[ModuleMetrics] = []
    
    def analyze(self) -> 'ProjectAnalyzer':
        """分析整个项目"""
        rtl_files = self._find_rtl_files()
        
        print(f"Found {len(rtl_files)} RTL files")
        
        for f in rtl_files:
            try:
                m = self._analyze_file(f)
                self.modules.append(m)
            except Exception as e:
                print(f"Error {os.path.basename(f)}: {e}")
        
        return self
    
    def _find_rtl_files(self) -> List[str]:
        """查找RTL文件"""
        files = []
        
        skip_dirs = {'dv', 'doc', 'fpv', 'spec', '.git', 'tb', 'testbench', 'bench', 'verif'}
        
        for root, dirs, filenames in os.walk(self.project_path):
            # 跳过特定目录
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            for f in filenames:
                # 排除pkg和_reg文件
                if f.endswith('.sv') and 'pkg' not in f and '_reg_' not in f and '_assert' not in f:
                    files.append(os.path.join(root, f))
        
        return files[:100]  # 限制数量
    
    def _analyze_file(self, f: str) -> ModuleMetrics:
        """分析单个文件"""
        name = os.path.basename(f).replace('.sv', '')
        m = ModuleMetrics(name=name, path=f)
        
        # 读取内容
        with open(f, 'r') as fp:
            content = fp.read()
        
        lines = content.split('\n')
        m.total_lines = len([l for l in lines if l.strip()])
        m.comment_lines = len([l for l in lines if l.strip().startswith('//')])
        
        if m.total_lines > 0:
            m.comment_ratio = m.comment_lines / m.total_lines * 100
        
        # 解析
        parser = SVParser()
        parser.parse_file(f)
        
        # 使用CodeMetricsAnalyzer
        try:
            cm = CodeMetricsAnalyzer(parser)
            report = cm.analyze()
            
            m.signals = report.control.total_signals
            m.always_ff = report.structure.always_ff_count
            m.always_comb = report.structure.always_comb_count
            m.if_count = report.structure.if_count
            m.case_count = report.structure.case_count
            m.parameter_count = report.reusability.parameter_count
            
            m.complexity_score = report.maintainability.cyclomatic_complexity
            
            m.and_count = report.computation.and_count
            m.or_count = report.computation.or_count
            m.add_count = report.computation.add_count
            m.mul_count = report.computation.mul_count
            
            m.max_fanout = report.control.max_fanout
            m.high_fanout_signals = report.control.high_fanout_signals[:5]
            
            # Width from IO
            if report.control.reg_widths:
                m.max_reg_width = max(report.control.reg_widths.keys())
        
        except Exception as e:
            print(f"Analyzer error for {name}: {e}")
        
        # 额外验证指标
        m.assert_count = content.count('assert')
        m.cover_count = content.count('cover')
        m.rand_count = content.count('rand')
        
        # TB检测
        tb_path = f.replace('/rtl/', '/tb/').replace('.sv', '_tb.sv')
        if os.path.exists(tb_path):
            m.tb_exists = True
        
        # IO count
        m.io_count = content.count('input ') + content.count('output ')
        
        return m
    
    def _sort_by(self, key: str, reverse: bool = True) -> List[Tuple]:
        """排序"""
        if key == 'lines':
            return [(m.name, m.total_lines) for m in self.modules]
        elif key == 'signals':
            return [(m.name, m.signals) for m in self.modules]
        elif key == 'complexity':
            return [(m.name, m.complexity_score) for m in self.modules]
        elif key == 'fanout':
            return [(m.name, m.max_fanout) for m in self.modules]
        elif key == 'assert':
            return [(m.name, m.assert_count) for m in self.modules]
        elif key == 'comment':
            return [(m.name, m.comment_ratio) for m in self.modules]
        return []
    
    def print_report(self, view: str = 'summary'):
        """打印报告
        
        Views:
        - summary: 总览
        - design: 设计质量
        - verification: 验证覆盖
        - management: 管理指标
        """
        print("="*70)
        print(f"Project Analysis: {len(self.modules)} modules")
        print("="*70)
        
        if view == 'summary':
            total = sum(m.total_lines for m in self.modules)
            total_sigs = sum(m.signals for m in self.modules)
            total_params = sum(m.parameter_count for m in self.modules)
            
            print(f"\n[Basic Statistics]")
            print(f"  Total modules: {len(self.modules)}")
            print(f"  Total lines: {total:,}")
            print(f"  Total signals: {total_sigs}")
            print(f"  Total parameters: {total_params}")
            
            # 聚合
            total_and = sum(m.and_count for m in self.modules)
            total_add = sum(m.add_count for m in self.modules)
            total_mul = sum(m.mul_count for m in self.modules)
            
            print(f"\n[Operations]")
            print(f"  AND: {total_and:,}")
            print(f"  ADD: {total_add:,}")
            print(f"  MUL: {total_mul:,}")
            
            # FF统计
            total_ff = sum(m.always_ff for m in self.modules)
            total_comb = sum(m.always_comb for m in self.modules)
            print(f"\n[Logic Blocks]")
            print(f"  always_ff: {total_ff}")
            print(f"  always_comb: {total_comb}")
        
        elif view == 'design':
            print("\n=== DESIGN QUALITY ===")
            
            print("\n[Top 15 - Complexity]")
            items = sorted(self.modules, key=lambda x: x.complexity_score, reverse=True)[:15]
            for i, m in enumerate(items, 1):
                print(f"{i:2}. {m.name:30} complexity={m.complexity_score}, if={m.if_count}, case={m.case_count}")
            
            print("\n[Top 10 - High Fanout]")
            items = sorted(self.modules, key=lambda x: x.max_fanout, reverse=True)[:10]
            for i, m in enumerate(items, 1):
                print(f"{i:2}. {m.name:30} fanout={m.max_fanout}")
            
            print("\n[Top 10 - Large Width]")
            items = sorted(self.modules, key=lambda x: x.max_reg_width, reverse=True)[:10]
            for i, m in enumerate(items, 1):
                if m.max_reg_width > 0:
                    print(f"{i:2}. {m.name:30} width={m.max_reg_width}bit")
        
        elif view == 'verification':
            print("\n=== VERIFICATION COVERAGE ===")
            
            with_tb = sum(1 for m in self.modules if m.tb_exists)
            with_assert = sum(1 for m in self.modules if m.assert_count > 0)
            with_cover = sum(1 for m in self.modules if m.cover_count > 0)
            
            print(f"\n[Summary]")
            print(f"  Modules with TB: {with_tb}/{len(self.modules)} ({with_tb*100//len(self.modules)}%)")
            print(f"  Modules with assert: {with_assert}/{len(self.modules)} ({with_assert*100//len(self.modules)}%)")
            print(f"  Modules with cover: {with_cover}/{len(self.modules)} ({with_cover*100//len(self.modules)}%)")
            
            print("\n[Top 10 - Assertions]")
            items = sorted(self.modules, key=lambda x: x.assert_count, reverse=True)[:10]
            for i, m in enumerate(items, 1):
                if m.assert_count > 0:
                    print(f"{i:2}. {m.name:30} assert={m.assert_count}, cover={m.cover_count}")
        
        elif view == 'management':
            print("\n=== MANAGEMENT METRICS ===")
            
            print("\n[Top 15 - Largest Modules]")
            items = sorted(self.modules, key=lambda x: x.total_lines, reverse=True)[:15]
            for i, m in enumerate(items, 1):
                print(f"{i:2}. {m.name:30} lines={m.total_lines}, signals={m.signals}")
            
            print("\n[Top 10 - Well Documented]")
            items = sorted(self.modules, key=lambda x: x.comment_ratio, reverse=True)[:10]
            for i, m in enumerate(items, 1):
                if m.comment_ratio > 0:
                    print(f"{i:2}. {m.name:30} comments={m.comment_ratio:.1f}%")
            
            print("\n[Top 10 - Parameterized]")
            items = sorted(self.modules, key=lambda x: x.parameter_count, reverse=True)[:10]
            for i, m in enumerate(items, 1):
                if m.parameter_count > 0:
                    print(f"{i:2}. {m.name:30} params={m.parameter_count}")
        
        print("="*70)


__all__ = ['ProjectAnalyzer']
