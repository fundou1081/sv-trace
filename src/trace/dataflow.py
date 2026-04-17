"""
DataFlowTracer - 数据流分析
连接 Driver 和 Load，构建完整数据流
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.models import Driver, Load, Connection
from .driver import DriverTracer
from .load import LoadTracer
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class DataFlow:
    """数据流"""
    signal_name: str
    drivers: List[Driver] = field(default_factory=list)
    loads: List[Load] = field(default_factory=list)
    paths: List[Dict] = field(default_factory=list)


class DataFlowTracer:
    """数据流分析器"""
    
    def __init__(self, parser):
        self.parser = parser
        self.driver_tracer = DriverTracer(parser)
        self.load_tracer = LoadTracer(parser)
    
    def find_flow(self, signal_name: str, module_name: str = None) -> DataFlow:
        """查找信号的数据流"""
        # 找驱动
        drivers = self.driver_tracer.find_driver(signal_name, module_name)
        
        # 找加载点
        loads = self.load_tracer.find_load(signal_name, module_name)
        
        # 构建路径
        paths = self._build_paths(signal_name, drivers, loads)
        
        return DataFlow(
            signal_name=signal_name,
            drivers=drivers,
            loads=loads,
            paths=paths,
        )
    
    def find_flow_chain(self, signal_name: str, max_depth: int = 5) -> List[Dict]:
        """查找信号的数据流链（递归）"""
        chain = []
        visited = set()
        
        def dfs(signal, depth):
            if depth > max_depth or signal in visited:
                return
            
            visited.add(signal)
            
            flow = self.find_flow(signal)
            
            for d in flow.drivers:
                # 尝试从驱动表达式提取使用的信号
                src_signals = self._extract_signals(d.source_expr)
                
                for src in src_signals:
                    chain.append({
                        "from": src,
                        "to": signal,
                        "driver": d.driver_kind.name,
                    })
                    dfs(src, depth + 1)
        
        dfs(signal_name, 0)
        
        return chain
    
    def _build_paths(self, signal_name: str, 
                   drivers: List[Driver], loads: List[Load]) -> List[Dict]:
        """构建驱动→载荷路径"""
        paths = []
        
        for d in drivers:
            for l in loads:
                paths.append({
                    "driver_expr": d.source_expr,
                    "driver_line": d.line,
                    "load_context": l.context,
                    "load_line": l.line,
                })
        
        return paths
    
    def _extract_signals(self, expr: str) -> List[str]:
        """从表达式中提取信号名（简单实现）"""
        if not expr:
            return []
        
        signals = []
        
        # 简单的标识符提取
        import re
        # 匹配字母开头，字母数字下划线
        pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'
        
        for match in re.finditer(pattern, expr):
            name = match.group()
            # 排除关键字
            if name not in ['if', 'else', 'case', 'endcase', 'begin', 'end',
                          'for', 'while', 'do', 'repeat', 'always', 'assign',
                          'module', 'endmodule', 'input', 'output', 'inout',
                          'wire', 'reg', 'logic', 'supply0', 'supply1',
                          'posedge', 'negedge', 'or', 'and', 'not', 'xor',
                          'new', 'null', 'this', 'super', 'return']:
                signals.append(name)
        
        return signals
    
    def visualize(self, signal_name: str) -> str:
        """生成可读的数据流描述"""
        flow = self.find_flow(signal_name)
        
        lines = [f"Signal: {signal_name}"]
        
        if flow.drivers:
            lines.append(f"  Drivers ({len(flow.drivers)}):")
            for d in flow.drivers:
                lines.append(f"    - {d.driver_kind.name}: {d.source_expr}")
        
        if flow.loads:
            lines.append(f"  Loads ({len(flow.loads)}):")
            for l in flow.loads:
                lines.append(f"    - {l.context}")
        
        if flow.paths:
            lines.append(f"  Paths ({len(flow.paths)}):")
            for p in flow.paths[:3]:
                lines.append(f"    {p['driver_expr']} → {p['load_context']}")
        
        return "\n".join(lines)
