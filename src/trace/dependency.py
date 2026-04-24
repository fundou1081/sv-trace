"""
DependencyAnalyzer - 信号依赖分析
分析信号的前向依赖（影响它的）和后向依赖（它影响的）
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
import re


@dataclass
class SignalDependency:
    """信号依赖关系"""
    signal: str                  # 信号名
    depends_on: List[str] = field(default_factory=list)  # 前向依赖（影响它的）
    influences: List[str] = field(default_factory=list)   # 后向依赖（它影响的）
    source_signals: List[str] = field(default_factory=list)  # 源头信号（无依赖）
    sink_signals: List[str] = field(default_factory=list)    # 汇信号（无后向）


class DependencyAnalyzer:
    """信号依赖分析器"""
    
    def __init__(self, parser):
        self.parser = parser
        self._driver_cache: Dict[str, List[str]] = {}
        self._load_cache: Dict[str, List[str]] = {}
    
    def analyze(self, signal_name: str, module_name: str = None) -> SignalDependency:
        """分析信号的依赖关系"""
        
        # 1. 找前向依赖（驱动这个信号的信号）
        forward_deps = self._find_forward_dependencies(signal_name, module_name)
        
        # 2. 找后向依赖（这个信号影响的信号）
        backward_deps = self._find_backward_dependencies(signal_name, module_name)
        
        # 3. 找源头信号（没有前向依赖的）
        source_signals = self._find_source_signals(signal_name, module_name, forward_deps)
        
        # 4. 找汇信号（没有后向依赖的）
        sink_signals = backward_deps  # 简化处理
        
        return SignalDependency(
            signal=signal_name,
            depends_on=forward_deps,
            influences=backward_deps,
            source_signals=source_signals,
            sink_signals=sink_signals
        )
    
    def _find_forward_dependencies(self, signal_name: str, module_name: str = None) -> List[str]:
        """找前向依赖 - 驱动这个信号的信号"""
        from .driver import DriverTracer
        
        tracer = DriverTracer(self.parser)
        drivers = tracer.find_driver(signal_name, module_name)
        
        forward_deps = set()
        
        for driver in drivers:
            # 从驱动表达式中提取信号
            signals = self._extract_signals(driver.sources)
            # 排除自身
            signals.discard(signal_name)
            forward_deps.update(signals)
        
        return list(forward_deps)
    
    def _find_backward_dependencies(self, signal_name: str, module_name: str = None) -> List[str]:
        """找后向依赖 - 这个信号影响的信号（负载）"""
        from .load import LoadTracer
        
        tracer = LoadTracer(self.parser)
        loads = tracer.find_load(signal_name, module_name)
        
        backward_deps = set()
        
        for load in loads:
            # 负载信号名
            if hasattr(load, 'signal_name') and load.signal_name:
                if load.signal_name != signal_name:
                    backward_deps.add(load.signal_name)
            # 从上下文中提取信号
            if load.context:
                signals = self._extract_signals(load.context)
                signals.discard(signal_name)
                backward_deps.update(signals)
        
        return list(backward_deps)
    
    def _find_source_signals(self, signal_name: str, module_name: str, 
                            forward_deps: List[str], max_depth: int = 5) -> List[str]:
        """递归查找源头信号（无前向依赖）"""
        sources = set()
        visited = set()
        
        def find_sources(sig, depth):
            if depth > max_depth or sig in visited:
                return
            
            visited.add(sig)
            
            deps = self._find_forward_dependencies(sig, module_name)
            
            if not deps:
                # 没有前向依赖，是源头
                sources.add(sig)
            else:
                for d in deps:
                    find_sources(d, depth + 1)
        
        # 只从已知的前向依赖开始
        for dep in forward_deps:
            find_sources(dep, 0)
        
        return list(sources)
    
    def _extract_signals(self, expr: str) -> Set[str]:
        """从表达式中提取信号"""
        if not expr:
            return set()
        
        signals = set()
        
        # 排除关键字
        keywords = {
            'if', 'else', 'case', 'endcase', 'begin', 'end',
            'for', 'while', 'do', 'repeat', 'always', 'assign',
            'module', 'endmodule', 'input', 'output', 'inout',
            'wire', 'reg', 'logic', 'supply0', 'supply1',
            'posedge', 'negedge', 'or', 'and', 'not', 'xor',
            'null', 'this', 'super', 'return',
            '1', '0', '1\'b0', '1\'b1', 'true', 'false',
            '0x0', '0x1', '8\'h00', '8\'hFF',
        }
        
        pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'
        
        for match in re.finditer(pattern, expr):
            name = match.group()
            if name not in keywords:
                signals.add(name)
        
        return signals
    
    def analyze_chain(self, signal_name: str, max_depth: int = 5) -> Dict:
        """递归分析依赖链"""
        chain = {
            "root": signal_name,
            "forward": {},
            "backward": {},
            "depth": 0
        }
        
        visited = set()
        
        def build_chain(sig, depth, direction):
            if depth > max_depth or sig in visited:
                return
            
            visited.add(sig)
            
            if direction == "forward":
                deps = self._find_forward_dependencies(sig)
                chain["forward"][sig] = deps
                for d in deps:
                    build_chain(d, depth + 1, "forward")
            else:
                deps = self._find_backward_dependencies(sig)
                chain["backward"][sig] = deps
                for d in deps:
                    build_chain(d, depth + 1, "backward")
        
        build_chain(signal_name, 0, "forward")
        
        chain["depth"] = max(
            len(chain["forward"]), 
            len(chain["backward"])
        )
        
        return chain
    
    def visualize(self, signal_name: str) -> str:
        """生成依赖关系可视化"""
        dep = self.analyze(signal_name)
        
        lines = [f"Signal: {signal_name}"]
        lines.append("=" * 40)
        
        # 前向依赖
        if dep.depends_on:
            lines.append(f"\n[Depends on] ({len(dep.depends_on)} signals)")
            for s in dep.depends_on:
                lines.append(f"  → {s}")
        else:
            lines.append(f"\n[Depends on] None (constant/parameter)")
        
        # 后向依赖
        if dep.influences:
            lines.append(f"\n[Influences] ({len(dep.influences)} signals)")
            for s in dep.influences:
                lines.append(f"  → {s}")
        else:
            lines.append(f"\n[Influences] None (unused)")
        
        # 源头
        if dep.source_signals:
            lines.append(f"\n[Source signals] ({len(dep.source_signals)})")
            for s in dep.source_signals:
                lines.append(f"  ● {s}")
        
        return "\n".join(lines)
    
    def find_path(self, from_signal: str, to_signal: str, max_depth: int = 10) -> List[List[str]]:
        """查找两个信号之间的所有路径"""
        paths = []
        
        def dfs(current, target, path, depth):
            if depth > max_depth:
                return
            if current == target:
                paths.append(path + [current])
                return
            
            # 继续前向查找
            deps = self._find_forward_dependencies(current)
            for d in deps:
                if d not in path:  # 避免循环
                    dfs(d, target, path + [current], depth + 1)
        
        dfs(from_signal, to_signal, [], 0)
        
        return paths
