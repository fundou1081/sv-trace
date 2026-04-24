"""
PerformanceEstimation - 性能估算统一入口
整合资源利用率 + 吞吐量的完整性能分析
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import Optional, Dict
import re


@dataclass
class PerformanceReport:
    """完整性能报告"""
    module_name: str
    
    # 资源利用
    lut_count: int = 0
    ff_count: int = 0
    dsp_count: int = 0
    
    # 吞吐量
    clock_freq_mhz: float = 100.0
    pipeline_depth: int = 0
    max_throughput: float = 0.0
    bandwidth_gbps: float = 0.0
    
    # 效率
    resource_efficiency: float = 0.0
    pipeline_efficiency: float = 0.0
    
    def visualize(self) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append(f"⚡ PERFORMANCE REPORT: {self.module_name}")
        lines.append("=" * 60)
        
        lines.append(f"\n📊 Resources:")
        lines.append(f"  LUT: {self.lut_count:,}")
        lines.append(f"  FF:  {self.ff_count:,}")
        lines.append(f"  DSP: {self.dsp_count:,}")
        
        lines.append(f"\n⏱️ Timing:")
        lines.append(f"  Clock: {self.clock_freq_mhz:.1f} MHz")
        
        lines.append(f"\n🔄 Pipeline:")
        lines.append(f"  Depth: {self.pipeline_depth}")
        
        lines.append(f"\n📈 Throughput:")
        lines.append(f"  Max: {self.max_throughput:.2f}/cycle")
        lines.append(f"  Bandwidth: {self.bandwidth_gbps:.2f} Gbps")
        
        lines.append("=" * 60)
        return "\n".join(lines)


class PerformanceEstimator:
    """性能估算器 - 统一入口"""
    
    def __init__(self, parser):
        self.parser = parser
    
    def analyze(self, module_name: str = None,
              clock_freq_mhz: float = 100.0) -> PerformanceReport:
        
        # 获取模块名
        if not module_name:
            module_name = self._get_default_module()
        
        report = PerformanceReport(
            module_name=module_name,
            clock_freq_mhz=clock_freq_mhz
        )
        
        # 分析代码获取统计数据
        stats = self._analyze_code(module_name)
        
        # 填充报告
        report.lut_count = stats.get('lut', 0)
        report.ff_count = stats.get('ff', 0)
        report.dsp_count = stats.get('dsp', 0)
        report.pipeline_depth = stats.get('pipeline_depth', 0)
        
        # 吞吐量计算
        if report.pipeline_depth > 0:
            report.max_throughput = 1.0
            report.pipeline_efficiency = 1.0 / report.pipeline_depth
        else:
            report.max_throughput = 1.0
            report.pipeline_efficiency = 0.0
        
        # 带宽
        data_width = stats.get('data_width', 8)
        report.bandwidth_gbps = report.max_throughput * data_width * clock_freq_mhz / 1000.0
        
        return report
    
    def _get_default_module(self) -> str:
        import pyslang
        for fname, tree in self.parser.trees.items():
            if tree and hasattr(tree, 'root'):
                members = list(tree.root.members) if hasattr(tree.root, 'members') else []
                for m in members:
                    if m.kind == pyslang.SyntaxKind.ModuleDeclaration:
                        if hasattr(m, 'header') and hasattr(m.header, 'name'):
                            return str(m.header.name).strip()
        return "unknown"
    
    def _analyze_code(self, module_name: str) -> Dict:
        stats = {
            'lut': 0,
            'ff': 0,
            'dsp': 0,
            'pipeline_depth': 0,
            'data_width': 8,
            'operators': [],
        }
        
        LUT_COST = {'+': 1.0, '-': 1.0, '*': 5.0, '/': 12.0}
        MUX_COST = 0.25
        
        for fname, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            # 读取源码
            source = ""
            try:
                source = tree.source if hasattr(tree, 'source') else ""
            except:
                pass
            
            if not source:
                try:
                    with open(fname) as f:
                        source = f.read()
                except:
                    continue
            
            in_module = False
            in_always_ff = False
            
            for line in source.split('\n'):
                stripped = line.strip()
                
                if stripped.startswith('module '):
                    in_module = module_name in stripped
                    continue
                elif stripped.startswith('endmodule'):
                    in_module = False
                    continue
                
                if not in_module:
                    continue
                
                # 统计 always_ff 块 -> FF 和 pipeline stage
                if 'always_ff' in stripped:
                    in_always_ff = True
                    stats['ff'] += 1
                    stats['pipeline_depth'] += 1
                
                # 运算符
                for op in ['*', '/']:
                    if op in stripped:
                        count = stripped.count(op) * (1 if op != '*' else 1)
                        stats['lut'] += count * 5 * 8  # 简化估算
                        if op == '*':
                            stats['dsp'] += count
                
                for op in ['+', '-']:
                    if op in stripped:
                        count = stripped.count(op)
                        stats['lut'] += count * 1 * 8
                
                # 位宽
                w = self._extract_width(stripped)
                if w > 0:
                    stats['data_width'] = max(stats['data_width'], w)
            
            # MUX 估算
            if (in_always_ff and stats['ff'] > 1):
                stats['lut'] += stats['ff'] * MUX_COST * 4
        
        return stats
    
    def _extract_width(self, line: str) -> int:
        match = re.search(r'\[(\d+):0\]', line)
        if match:
            return int(match.group(1)) + 1
        return 0


def analyze_performance(parser, module_name: str = None,
                   clock_freq_mhz: float = 100.0) -> PerformanceReport:
    est = PerformanceEstimator(parser)
    return est.analyze(module_name, clock_freq_mhz)
