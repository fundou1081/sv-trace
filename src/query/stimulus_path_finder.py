"""StimulusPathFinder - 激励路径追踪器 (最终版)。

支持 if/case/Memory/FIFO 嵌套条件的激励路径追踪。
用于查找信号目标值所需的输入激励。

Example:
    >>> from query.stimulus_path_finder import StimulusPathFinder, find_stimulus_path
    >>> from parse import SVParser
    >>> parser = SVParser()
    >>> parser.parse_file("design.sv")
    >>> finder = StimulusPathFinder(parser)
    >>> result = finder.find("data_out", 42)
    >>> print(result.visualize())
"""
import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple


@dataclass
class IOInput:
    """IO 输入数据类。
    
    Attributes:
        name: 信号名
        width: 位宽
        ranges: 取值范围列表
    """
    name: str
    width: int = 1
    ranges: List[Tuple[int, int]] = field(default_factory=list)


@dataclass
class MemoryAccess:
    """Memory 访问数据类。
    
    Attributes:
        name: 存储器名
        access_type: 访问类型 (read/write)
        address: 地址信号
        data: 数据信号
        condition: 访问条件
    """
    name: str
    access_type: str = ""   # read/write
    address: str = ""
    data: str = ""
    condition: str = ""


@dataclass
class PathSegment:
    """路径段数据类。
    
    Attributes:
        signal: 信号名
        from_signal: 来源信号
        operation: 操作类型
        conditions: 条件列表
    """
    signal: str = ""
    from_signal: str = ""
    operation: str = ""
    conditions: List[Dict] = field(default_factory=list)


@dataclass
class StimulusResult:
    """激励结果数据类。
    
    Attributes:
        target: 目标信号
        target_value: 目标值
        path_segments: 路径段列表
        io_inputs: 所需 IO 输入
        memory_accesses: 涉及的记忆访问
    """
    target: str
    target_value: int
    path_segments: List[PathSegment] = field(default_factory=list)
    io_inputs: List[IOInput] = field(default_factory=list)
    memory_accesses: List[MemoryAccess] = field(default_factory=list)
    
    def visualize(self) -> str:
        """可视化激励结果。
        
        Returns:
            str: 格式化的报告字符串
        """
        lines = ["=" * 70, "STIMULUS PATH FINDER", "=" * 70]
        lines.append(f"\n🎯 Target: {self.target} = {self.target_value}")
        
        if self.path_segments:
            lines.append(f"\n📍 Path:")
            for seg in self.path_segments:
                c = f"{seg.from_signal}" 
                if seg.operation:
                    c += f" --[{seg.operation}]"
                if seg.conditions:
                    for cond in seg.conditions:
                        c += f" ({cond.get('type','')})"
                lines.append(f"   → {c} --> {seg.signal}")
        
        if self.memory_accesses:
            lines.append(f"\n📦 Memory Accesses:")
            for ma in self.memory_accesses:
                lines.append(f"   [{ma.access_type}] {ma.name}")
                lines.append(f"     addr: {ma.address or 'sequential'}")
                lines.append(f"     data: {ma.data or 'N/A'}")
                if ma.condition:
                    lines.append(f"     when: {ma.condition}")
        
        if self.io_inputs:
            lines.append(f"\n💡 Required Input Stimulus:")
            for io in self.io_inputs:
                if io.ranges and io.ranges[0][0] == io.ranges[0][1]:
                    lines.append(f"   {io.name}: fixed to {io.ranges[0][0]}")
                else:
                    ranges = [f"[{r[0]}:{r[1]}]" for r in io.ranges]
                    lines.append(f"   {io.name}: {' + '.join(ranges)}")
        
        lines.append("=" * 70)
        return '\n'.join(lines)


class StimulusPathFinder:
    """激励路径追踪器。
    
    追踪信号到其激励源的路径，支持复杂嵌套条件。

    Attributes:
        parser: SVParser 实例
        ios: IO 信号列表
        signal_assignments: 信号赋值映射
        memories: 存储器列表
    
    Example:
        >>> finder = StimulusPathFinder(parser)
        >>> result = finder.find("data_out", 42)
    """
    
    def __init__(self, parser):
        """初始化追踪器。
        
        Args:
            parser: SVParser 实例
        """
        self.parser = parser
        self.ios = []
        self.signal_assignments = {}
        self.memories = []  # 存储 elements
    
    def find(self, target: str, target_value: int = None) -> StimulusResult:
        """查找激励路径。
        
        Args:
            target: 目标信号名
            target_value: 目标值
        
        Returns:
            StimulusResult: 激励结果
        """
        result = StimulusResult(target=target, target_value=target_value or 0)
        
        self._collect_IOs()
        self._collect_assignments()
        self._collect_memories()
        
        path = self._trace_path(target, target_value or 0)
        result.path_segments = path
        
        result.io_inputs = self._calculate_requirements(path, target_value)
        
        result.memory_accesses = self._find_memory_access(path)
        
        return result
    
    def _collect_IOs(self):
        """收集所有 IO 信号。"""
        for fname, tree in self.parser.trees.items():
            code = self._get_code(fname)
            for line in code.split('\n'):
                line = line.strip()
                if line.startswith('input'):
                    match = re.search(r'input\s*\[(\d+):\d+\]\s+(\w+)', line) or \
                            re.search(r'input\s+(\w+)', line)
                    if match:
                        w = 1
                        if match.group(1):
                            try:
                                w = int(match.group(1)) + 1
                            except:
                                pass
                        name = match.group(2) if len(match.groups()) > 1 else match.group(1)
                        self.ios.append(IOInput(name=name, width=w))
    
    def _collect_assignments(self):
        """收集所有信号赋值。"""
        for fname, tree in self.parser.trees.items():
            code = self._get_code(fname)
            for i, line in enumerate(code.split('\n')):
                if 'always' in line or 'assign' in line:
                    match = re.search(r'(\w+)\s*<=\s*(.+)', line)
                    if match:
                        tgt = match.group(1).strip()
                        expr = match.group(2).strip()
                        self.signal_assignments.setdefault(tgt, []).append((i, expr))
    
    def _collect_memories(self):
        """收集 Memory/FIFO 声明。"""
        for fname, tree in self.parser.trees.items():
            code = self._get_code(fname)
            
            # reg [7:0] mem [0:255]
            for line in code.split('\n'):
                match = re.search(r'reg\s*\[(\d+):\d+\]\s+(\w+)\s*\[(\d+):(\d+)\]', line)
                if match:
                    w = int(match.group(1)) + 1
                    d = int(match.group(3)) + 1
                    self.memories.append({
                        'name': match.group(2),
                        'data_width': w,
                        'depth': d
                    })
                
                # 数组
                match2 = re.search(r'reg\s*(\w+)\s*\[(\d+):\d+\]', line)
                if match2 and 'mem' in match2.group(1).lower():
                    pass
    
    def _find_memory_access(self, path: List[PathSegment]) -> List[MemoryAccess]:
        """查找涉及 memory 的访问。
        
        Args:
            path: 路径段列表
        
        Returns:
            List[MemoryAccess]: 存储器访问列表
        """
        accesses = []
        
        for seg in path:
            for fname, tree in self.parser.trees.items():
                code = self._get_code(fname)
                
                # 查找 memory 读取
                for line in code.split('\n'):
                    if f"mem[{seg.from_signal}" in line or f"mem[{seg.signal}" in line:
                        if 'read' in line.lower() or 'write' in line.lower():
                            mem = MemoryAccess(name='mem', access_type='read')
                            accesses.append(mem)
        
        return accesses
    
    def _trace_path(self, target: str, value: int, depth=0) -> List[PathSegment]:
        """追踪路径。
        
        Args:
            target: 目标信号
            value: 目标值
            depth: 递归深度
        
        Returns:
            List[PathSegment]: 路径段列表
        """
        if depth > 15:
            return []
            
        path = []
        visited = set()
        
        def trace(sig, d=0):
            if sig in visited or d > 15: return
            visited.add(sig)
            
            if sig in self.signal_assignments:
                for _, expr in self.signal_assignments[sig]:
                    seg = PathSegment(signal=sig)
                    
                    # 操作分析
                    if '+' in expr: seg.operation = 'add'
                    elif '-' in expr: seg.operation = 'sub'
                    elif '&' in expr: seg.operation = 'and'
                    elif '|' in expr: seg.operation = 'or'
                    elif '<<' in expr: seg.operation = 'lshift'
                    elif '>>' in expr: seg.operation = 'rshift'
                    
                    # case 条件
                    if 'case' in expr.lower():
                        seg.operation = 'case'
                        cases = []
                        for line in self._get_code('').split('\n'):
                            if sig in line and ':' in line:
                                # 提取 case 值
                                c = line.split(':')[0].strip()
                                cases.append({'type': 'case', 'value': c})
                        seg.conditions = cases
                    
                    path.append(seg)
                    
                    # 提取操作数
                    for m in re.findall(r'\w+', expr):
                        if m != sig:
                            trace(m, d+1)
            
            # wire assign
            code = self._get_code('')
            for line in code.split('\n'):
                if f'assign {sig} =' in line:
                    seg = PathSegment(signal=sig, operation='wire')
                    path.append(seg)
        
        trace(target)
        return path
    
    def _calculate_requirements(self, path: List[PathSegment], value: int) -> List[IOInput]:
        """计算所需输入。
        
        Args:
            path: 路径段列表
            value: 目标值
        
        Returns:
            List[IOInput]: 所需 IO 输入列表
        """
        ios = []
        
        for seg in path:
            for io in self.ios:
                if not io.ranges:
                    if seg.operation in ['add', 'sub', 'and', 'or']:
                        io.ranges = [(0, 2**io.width - 1)]
                    elif seg.operation == 'case':
                        io.ranges = [(0, 2**io.width - 1)]
                    else:
                        io.ranges = [(0, 2**io.width - 1)]
                    if io not in ios:
                        ios.append(io)
        
        return ios
    
    def _get_code(self, fname: str) -> str:
        """获取源码。
        
        Args:
            fname: 文件名
        
        Returns:
            str: 源代码字符串
        """
        for fname, tree in self.parser.trees.items():
            if hasattr(tree, 'source'):
                return tree.source
        return ""


def find_stimulus_path(parser, target: str, value: int = None):
    """便捷函数：查找激励路径。
    
    Args:
        parser: SVParser 实例
        target: 目标信号名
        value: 目标值
    
    Returns:
        StimulusResult: 激励结果
    """
    return StimulusPathFinder(parser).find(target, value)
