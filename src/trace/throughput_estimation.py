"""
ThroughputEstimation - 吞吐量估算器
基于流水线结构和数据路径分析估算吞吐能力
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import re


@dataclass
class ThroughputMetrics:
    max_throughput: float = 0.0
    avg_throughput: float = 0.0
    clock_period_ns: float = 0.0
    clock_freq_mhz: float = 0.0
    pipeline_depth: int = 0
    data_width_bits: int = 0
    data_bandwidth_gbps: float = 0.0
    pipeline_efficiency: float = 0.0
    
    def visualize(self) -> str:
        lines = []
        lines.append(f"  ⏱️ Clock: {self.clock_freq_mhz:.1f} MHz ({self.clock_period_ns:.2f} ns)")
        lines.append(f"  📊 Throughput: {self.max_throughput:.2f}/cycle")
        if self.pipeline_depth > 0:
            lines.append(f"  🔄 Pipeline: {self.pipeline_depth} stages")
        if self.data_width_bits > 0:
            lines.append(f"  📺 Bandwidth: {self.data_bandwidth_gbps:.2f} Gbps")
        return "\n".join(lines)


@dataclass
class ThroughputResult:
    module_name: str
    metrics: ThroughputMetrics = field(default_factory=ThroughputMetrics)
    data_path: List[str] = field(default_factory=list)
    
    def visualize(self) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append(f"📈 THROUGHPUT: {self.module_name}")
        lines.append("=" * 60)
        lines.append(self.metrics.visualize())
        lines.append("=" * 60)
        return "\n".join(lines)


class ThroughputEstimation:
    def __init__(self, parser):
        self.parser = parser
    
    def analyze(self, module_name: str = None, clock_freq_mhz: float = 100.0) -> ThroughputResult:
        modules = self._get_all_modules()
        
        if module_name:
            target = module_name
        else:
            target = modules[0] if modules else "unknown"
        
        result = ThroughputResult(module_name=target)
        
        # 分析代码结构
        stats = self._analyze_code(target)
        
        # 计算指标
        result.metrics = self._calculate_metrics(stats, clock_freq_mhz)
        result.data_path = stats.get('data_path', [])
        
        return result
    
    def _get_all_modules(self) -> List[str]:
        modules = []
        import pyslang
        for fname, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            members = list(tree.root.members) if hasattr(tree.root, 'members') else []
            for m in members:
                if m.kind == pyslang.SyntaxKind.ModuleDeclaration:
                    if hasattr(m, 'header') and hasattr(m.header, 'name'):
                        modules.append(str(m.header.name))
        return modules
    
    def _analyze_code(self, module_name: str) -> Dict:
        stats = {
            'pipeline_depth': 0,
            'pipeline_stages': [],
            'handshakes': [],
            'data_path': [],
            'data_width': 8,
            'stages': [],
        }
        
        for fname, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            # 读取源码
            try:
                source = tree.source if hasattr(tree, 'source') else ""
            except:
                source = ""
            
            if not source:
                try:
                    with open(fname) as f:
                        source = f.read()
                except:
                    continue
            
            in_module = False
            stages = []
            
            lines = source.split('\n')
            for line in lines:
                stripped = line.strip()
                
                if stripped.startswith('module '):
                    in_module = module_name in stripped
                    continue
                elif stripped.startswith('endmodule'):
                    in_module = False
                    continue
                
                if not in_module:
                    continue
                
                # 检测 always_ff 块 -> 流水线 stage
                if 'always_ff' in stripped:
                    stages.append(stripped)
                
                # 检测 valid/ready 握手
                if 'valid' in stripped.lower():
                    stats['handshakes'].append('valid')
                if 'ready' in stripped.lower():
                    stats['handshakes'].append('ready')
                
                # 提取位宽
                w = self._extract_width(stripped)
                if w > 0:
                    stats['data_width'] = max(stats['data_width'], w)
            
            stats['pipeline_depth'] = len(stages)
            stats['stages'] = stages
        
        return stats
    
    def _extract_width(self, line: str) -> int:
        match = re.search(r'\[(\d+):0\]', line)
        if match:
            return int(match.group(1)) + 1
        return 0
    
    def _calculate_metrics(self, stats: Dict, clock_freq_mhz: float) -> ThroughputMetrics:
        m = ThroughputMetrics()
        
        m.clock_freq_mhz = clock_freq_mhz
        m.clock_period_ns = 1000.0 / clock_freq_mhz if clock_freq_mhz > 0 else 10.0
        
        m.pipeline_depth = stats.get('pipeline_depth', 0)
        m.data_width_bits = stats.get('data_width', 8)
        
        if m.pipeline_depth > 0:
            m.max_throughput = 1.0
            m.avg_throughput = 1.0 / m.pipeline_depth
            m.pipeline_efficiency = 1.0
        else:
            m.max_throughput = 1.0
        
        m.data_bandwidth_gbps = m.max_throughput * m.data_width_bits * m.clock_freq_mhz / 1000.0
        
        return m


def estimate_throughput(parser, module_name: str = None, clock_freq_mhz: float = 100.0) -> ThroughputResult:
    est = ThroughputEstimation(parser)
    return est.analyze(module_name, clock_freq_mhz)
