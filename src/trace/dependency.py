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
            # driver.sources 已经是 List[str]，直接使用
            for src in driver.sources:
                if src and src != signal_name:
                    forward_deps.add(src)
        
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


# =============================================================================
# Fanin/Fanout 增强功能
# =============================================================================

from collections import deque
from typing import Tuple


@dataclass
class FanoutInfo:
    """Fanout信息"""
    signal: str
    direct_fanout: int = 0       # 直接驱动的信号数
    total_fanout: int = 0         # 总扇出（含多级）
    max_depth: int = 0            # 最大深度
    driven_signals: List[str] = field(default_factory=list)
    high_fanout: bool = False
    critical: bool = False


@dataclass
class FaninInfo:
    """Fanin信息"""
    signal: str
    direct_fanin: int = 0         # 直接驱动的信号数
    total_fanin: int = 0          # 总扇入（含多级）
    source_signals: List[str] = field(default_factory=list)
    is_primary_input: bool = False  # 是否是原始输入


class FanoutAnalyzer:
    """Fanout分析器 - 精确计算信号扇出"""
    
    def __init__(self, parser):
        self.parser = parser
        self._fanout_cache: Dict[str, FanoutInfo] = {}
    
    def analyze_signal(self, signal_name: str) -> FanoutInfo:
        """分析单个信号的扇出"""
        if signal_name in self._fanout_cache:
            return self._fanout_cache[signal_name]
        
        info = self._calculate_fanout(signal_name)
        self._fanout_cache[signal_name] = info
        return info
    
    def _calculate_fanout(self, signal_name: str) -> FanoutInfo:
        """计算扇出"""
        from .load import LoadTracer
        
        tracer = LoadTracer(self.parser)
        loads = tracer.find_load(signal_name)
        
        # 直接扇出
        direct = set()
        for load in loads:
            if hasattr(load, 'signal_name') and load.signal_name:
                direct.add(load.signal_name)
            # 从context中提取
            if load.context:
                # 简单提取所有标识符
                tokens = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', load.context)
                for t in tokens:
                    if t != signal_name and not t.startswith('clk') and not t.startswith('rst'):
                        direct.add(t)
        
        # 计算总扇出（多级追溯）
        total_fanout = len(direct)
        max_depth = 0
        all_directed = set(direct)
        
        # BFS追溯
        queue = deque([(s, 1) for s in direct])
        visited = set([signal_name])
        
        while queue:
            current, depth = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            
            # 找当前信号驱动的信号
            sub_loads = tracer.find_load(current)
            sub_direct = set()
            for load in sub_loads:
                if hasattr(load, 'signal_name') and load.signal_name:
                    sub_direct.add(load.signal_name)
            
            for sd in sub_direct:
                if sd not in visited:
                    all_directed.add(sd)
                    total_fanout += 1
                    max_depth = max(max_depth, depth + 1)
                    queue.append((sd, depth + 1))
        
        info = FanoutInfo(
            signal=signal_name,
            direct_fanout=len(direct),
            total_fanout=total_fanout,
            max_depth=max_depth,
            driven_signals=list(all_directed),
            high_fanout=len(direct) > 10,
            critical=len(direct) > 20
        )
        
        return info
    
    def find_high_fanout_signals(self, threshold: int = 10) -> List[FanoutInfo]:
        """找出高扇出信号"""
        from .driver import DriverCollector
        
        collector = DriverCollector(self.parser)
        signals = collector.get_all_signals()
        
        results = []
        for sig in signals:
            info = self.analyze_signal(sig)
            if info.direct_fanout >= threshold:
                results.append(info)
        
        return sorted(results, key=lambda x: -x.direct_fanout)
    
    def get_fanout_report(self, top_n: int = 20) -> List[FanoutInfo]:
        """获取扇出报告"""
        results = self.find_high_fanout_signals(2)  # 从2开始
        return results[:top_n]


class FaninAnalyzer:
    """Fanin分析器 - 精确计算信号扇入"""
    
    def __init__(self, parser):
        self.parser = parser
    
    def analyze_signal(self, signal_name: str) -> FaninInfo:
        """分析单个信号的扇入"""
        from .driver import DriverTracer
        
        tracer = DriverTracer(self.parser)
        drivers = tracer.find_driver(signal_name)
        
        # 直接扇入
        direct = set()
        for driver in drivers:
            for src in driver.sources:
                if src:
                    direct.add(src)
        
        # 判断是否原始输入（没有前向依赖）
        is_input = len(direct) == 0
        
        return FaninInfo(
            signal=signal_name,
            direct_fanin=len(direct),
            total_fanin=len(direct),
            source_signals=list(direct),
            is_primary_input=is_input
        )
    
    def find_source_signals(self) -> List[str]:
        """找出所有源头信号（无扇入）"""
        from .driver import DriverCollector
        
        collector = DriverCollector(self.parser)
        signals = collector.get_all_signals()
        
        sources = []
        for sig in signals:
            info = self.analyze_signal(sig)
            if info.is_primary_input:
                sources.append(sig)
        
        return sources


class ConnectivityMatrix:
    """连接矩阵 - 分析模块间连接"""
    
    def __init__(self, parser):
        self.parser = parser
        self._module_signals: Dict[str, Set[str]] = {}
        self._signal_modules: Dict[str, str] = {}
    
    def build(self):
        """构建连接矩阵"""
        from .driver import DriverCollector
        from .load import LoadTracer
        
        driver_collector = DriverCollector(self.parser)
        load_tracer = LoadTracer(self.parser)
        
        all_signals = driver_collector.get_all_signals()
        
        for sig in all_signals:
            # 确定信号所属模块（简化处理）
            module = self._find_signal_module(sig)
            if module:
                if module not in self._module_signals:
                    self._module_signals[module] = set()
                self._module_signals[module].add(sig)
                self._signal_modules[sig] = module
    
    def _find_signal_module(self, signal: str) -> Optional[str]:
        """确定信号所属模块"""
        # TODO: 实现模块确定
        return "top"
    
    def get_module_inputs(self, module: str) -> Set[str]:
        """获取模块的输入信号"""
        if module not in self._module_signals:
            return set()
        
        signals = self._module_signals[module]
        inputs = set()
        
        from .driver import DriverTracer
        tracer = DriverTracer(self.parser)
        
        for sig in signals:
            drivers = tracer.find_driver(sig)
            for d in drivers:
                for src in d.sources:
                    if src not in signals:
                        inputs.add(src)
        
        return inputs
    
    def get_module_outputs(self, module: str) -> Set[str]:
        """获取模块的输出信号"""
        if module not in self._module_signals:
            return set()
        return self._module_signals[module]


# 添加便捷方法到DependencyAnalyzer
def get_fanin(self, signal_name: str, module_name: str = None) -> FaninInfo:
    """获取信号的扇入信息"""
    analyzer = FaninAnalyzer(self.parser)
    return analyzer.analyze_signal(signal_name)


def get_fanout(self, signal_name: str, module_name: str = None) -> FanoutInfo:
    """获取信号的扇出信息"""
    analyzer = FanoutAnalyzer(self.parser)
    return analyzer.analyze_signal(signal_name)


def get_connectivity(self) -> ConnectivityMatrix:
    """获取连接矩阵"""
    matrix = ConnectivityMatrix(self.parser)
    matrix.build()
    return matrix


DependencyAnalyzer.get_fanin = get_fanin
DependencyAnalyzer.get_fanout = get_fanout
DependencyAnalyzer.get_connectivity = get_connectivity


__all__ = [
    'DependencyAnalyzer', 
    'SignalDependency',
    'FanoutAnalyzer',
    'FaninAnalyzer',
    'FanoutInfo',
    'FaninInfo',
    'ConnectivityMatrix',
]


# =============================================================================
# 使用改进版LoadTracer的FanoutAnalyzer
# =============================================================================

class FanoutAnalyzerWithImprovedLoad(FanoutAnalyzer):
    """使用改进版LoadTracer的FanoutAnalyzer"""
    
    def __init__(self, parser):
        super().__init__(parser)
        # 使用改进版的LoadTracer
        from .load_improved import LoadTracerImproved
        self._load_tracer = LoadTracerImproved(parser)
    
    def analyze_signal(self, signal_name: str):
        """分析单个信号的扇出"""
        loads = self._load_tracer.find_load(signal_name)
        
        direct = len(loads)
        
        return FanoutInfo(
            signal=signal_name,
            direct_fanout=direct,
            total_fanout=direct,
            max_depth=1,
            driven_signals=[],
            high_fanout=direct > 10,
            critical=direct > 20
        )
    
    def find_high_fanout_signals(self, threshold: int = 10):
        """查找高扇出信号"""
        from .driver import DriverCollector
        from .load_improved import LoadTracerImproved
        
        # 使用改进版LoadTracer
        improved_tracer = LoadTracerImproved(self.parser)
        
        # 获取所有信号
        signals = set()
        keywords = {'if', 'else', 'case', 'for', 'while', 'do', 'begin', 'end', 'always', 
                   'assign', 'logic', 'wire', 'reg', 'input', 'output', 'inout', 'module',
                   'parameter', 'localparam', 'typedef', 'enum', 'struct', 'interface',
                   'posedge', 'negedge', 'or', 'and', 'not', 'xor', 'assign', 'force'}
        for fname, tree in self.parser.trees.items():
            code = ""
            # 尝试从parser.sources获取
            if hasattr(self.parser, 'sources') and fname in self.parser.sources:
                code = self.parser.sources[fname]
            elif hasattr(tree, 'source') and tree.source:
                code = tree.source
            if code:
                import re
                sigs = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', code)
                for s in sigs:
                    if s not in keywords and not s.startswith('_'):
                        signals.add(s)
        
        results = []
        for sig in signals:
            if sig.startswith('_'):
                continue
            fo = improved_tracer.get_fanout(sig)
            if fo >= threshold:
                results.append(FanoutInfo(
                    signal=sig,
                    direct_fanout=fo,
                    total_fanout=fo,
                    max_depth=1,
                    driven_signals=[],
                    high_fanout=fo > 10,
                    critical=fo > 20
                ))
        
        return sorted(results, key=lambda x: -x.direct_fanout)


# 添加便捷方法
def get_fanout_improved(self, signal_name: str, module_name: str = None) -> FanoutInfo:
    """获取信号的扇出信息 - 使用改进版"""
    analyzer = FanoutAnalyzerWithImprovedLoad(self.parser)
    return analyzer.analyze_signal(signal_name)

DependencyAnalyzer.get_fanout_improved = get_fanout_improved


__all__ = [
    'DependencyAnalyzer', 
    'SignalDependency',
    'FanoutAnalyzer',
    'FaninAnalyzer',
    'FanoutInfo',
    'FaninInfo',
    'ConnectivityMatrix',
    'FanoutAnalyzerWithImprovedLoad',
]
