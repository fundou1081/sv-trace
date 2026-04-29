"""
ClockTreeAnalyzer - 时钟树结构分析器
分析时钟的生成、分配、缓冲网络
"""
import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
from collections import defaultdict


@dataclass
class ClockSource:
    """时钟源"""
    name: str
    type: str           # "input", "internal", "pll", "oscillator"
    source_file: str = ""
    line_number: int = 0
    
    # 连接信息
    frequency: str = ""     # 如 "100MHz"
    period_ns: float = 0.0


@dataclass
class ClockBuffer:
    """时钟缓冲"""
    name: str
    cell_type: str     # "bufg", "bufh", "bufio", etc
    input_clock: str   # 输入时钟
    output_clock: str  # 输出时钟
    fanout: int = 0    # 驱动多少负载
    
    line_number: int = 0


@dataclass
class ClockDivider:
    """时钟分频器"""
    name: str
    input_clock: str        # 输入时钟
    output_clock: str       # 输出时钟
    division_factor: int = 1  # 分频系数
    
    line_number: int = 0


@dataclass
class ClockNet:
    """时钟网络"""
    name: str
    source: str         # 源头时钟
    type: str         # "global", "regional", "io"
    loads: List[str] = field(default_factory=list)  # 负载列表


@dataclass
class ClockTreeStats:
    """统计"""
    num_sources: int = 0
    num_buffers: int = 0
    num_dividers: int = 0
    num_nets: int = 0
    max_fanout: int = 0
    
    # 时钟域
    domains: List[str] = field(default_factory=list)


@dataclass
class ClockTreeResult:
    """结果"""
    sources: List[ClockSource] = field(default_factory=list)
    buffers: List[ClockBuffer] = field(default_factory=list)
    dividers: List[ClockDivider] = field(default_factory=list)
    nets: List[ClockNet] = field(default_factory=list)
    stats: ClockTreeStats = field(default_factory=ClockTreeStats)
    
    def visualize(self) -> str:
        lines = ["=" * 60, "CLOCK TREE ANALYSIS", "=" * 60]
        
        lines.append(f"\n📊 Summary:")
        lines.append(f"  Sources: {self.stats.num_sources}")
        lines.append(f"  Buffers: {self.stats.num_buffers}")
        lines.append(f"  Dividers: {self.stats.num_dividers}")
        lines.append(f"  Nets: {self.stats.num_nets}")
        lines.append(f"  Max Fanout: {self.stats.max_fanout}")
        
        if self.stats.domains:
            lines.append(f"  Domains: {', '.join(self.stats.domains)}")
        
        # 时钟源
        if self.sources:
            lines.append(f"\n🔔 Clock Sources:")
            for s in self.sources:
                lines.append(f"  {s.name} ({s.type})")
                if s.frequency:
                    lines.append(f"    freq: {s.frequency}")
        
        # 时钟分频
        if self.dividers:
            lines.append(f"\n🔀 Clock Dividers:")
            for d in self.dividers:
                lines.append(f"  {d.name}: {d.input_clock} -> {d.output_clock}")
                lines.append(f"    div: {d.division_factor}x")
        
        # 时钟缓冲
        if self.buffers:
            lines.append(f"\n🧊 Clock Buffers:")
            for b in self.buffers:
                lines.append(f"  {b.name} ({b.cell_type})")
                lines.append(f"    {b.input_clock} -> {b.output_clock}")
                lines.append(f"    fanout: {b.fanout}")
        
        # 时钟网络
        if self.nets:
            lines.append(f"\n🌐 Clock Nets:")
            for n in self.nets[:5]:
                loads_str = ", ".join(n.loads[:3])
                if len(n.loads) > 3:
                    loads_str += f"... +{len(n.loads)-3}"
                lines.append(f"  {n.name}: {n.source} -> [{loads_str}]")
        
        lines.append("=" * 60)
        return "\n".join(lines)


class ClockTreeAnalyzer:
    """时钟树结构分析器"""
    
    # 时钟缓冲器类型
    BUFFER_CELLS = {'bufg', 'bufh', 'bufio', 'bufmr', 'bufxr', 'buf'}
    
    # 时钟输入端口模式
    CLOCK_INPUT_PATTERNS = [
        r'input\s+(?:logic\s+)?(\w*clk\w*)',
        r'input\s+\[(\d+):0\]?\s*(\w*clk\w*)',
        r'input\s+(?:\w+\s+)?(\w*[Cc]lock\w*)',
        r'input\s+(?:\w+\s+)?(\w*\[',
    ]
    
    def __init__(self, parser):
        self.parser = parser
        self.result = ClockTreeResult()
        self._analyze()
    
    def _analyze(self):
        """分析时钟树"""
        
        # 从 parser 获取代码
        for fname, tree in self.parser.trees.items():
            code = self._get_code(fname)
            if not code:
                continue
            
            lines = code.split('\n')
            
            # 1. 提取时钟输入端口
            self._extract_clock_inputs(lines, fname)
            
            # 2. 提取 always_ff 时钟
            self._extract_ff_clocks(lines, fname)
            
            # 3. 提取时钟分频
            self._extract_clock_dividers(lines, fname)
            
            # 4. 提取时钟缓冲
            self._extract_clock_buffers(lines, fname)
        
        # 计算统计
        self._calculate_stats()
    
    def _get_code(self, fname: str) -> str:
        """获取代码"""
        # 从 parser trees 获取
        if fname in self.parser.trees:
            tree = self.parser.trees[fname]
            if hasattr(tree, 'source') and tree.source:
                return tree.source
        
        # 从文件读取
        try:
            with open(fname) as f:
                return f.read()
        except:
            return ""
    
    def _extract_clock_inputs(self, lines: List[str], fname: str):
        """提取时钟输入端口"""
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # 跳过注释
            if stripped.startswith('//'):
                continue
            
            # 检查 input 声明
            # input clk, input clk_100m, input [1:0] clk
            if stripped.startswith('input'):
                # 检查是否像时钟
                if any(kw in stripped.lower() for kw in ['clk', 'clock', 'osc']):
                    # 提取信号名
                    match = re.search(r'input\s+(?:\[\d+:\d+\]\s+)?(\w+)', stripped)
                    if match:
                        name = match.group(1)
                        
                        # 检查频率
                        freq = ""
                        period = 0.0
                        if '100' in name:
                            freq = "100MHz"
                            period = 10.0
                        elif '50' in name:
                            freq = "50MHz"
                            period = 20.0
                        elif '200' in name:
                            freq = "200MHz"
                            period = 5.0
                        
                        self.result.sources.append(ClockSource(
                            name=name,
                            type="input",
                            source_file=fname,
                            line_number=i,
                            frequency=freq,
                            period_ns=period
                        ))
    
    def _extract_ff_clocks(self, lines: List[str], fname: str):
        """从 always_ff 提取时钟"""
        
        for i, line in enumerate(lines, 1):
            if 'always_ff' in line or '@(posedge' in line or '@(negedge' in line:
                # 提取时钟信号
                match = re.search(r'@\(pos?edge\s+(\w+)', line)
                if match:
                    clock = match.group(1)
                    
                    # 检查是否已存在
                    existing = [s for s in self.result.sources if s.name == clock]
                    if not existing:
                        self.result.sources.append(ClockSource(
                            name=clock,
                            type="ff_clock",
                            source_file=fname,
                            line_number=i
                        ))
    
    def _extract_clock_dividers(self, lines: List[str], fname: str):
        """提取时钟分频器"""
        
        # 模式1: always_ff 中的除法
        # 模式2: clock_divider 模块实例
        # 模式3: assign clk_out = clk_in >> 1;
        
        in_always = False
        clock_in = ""
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # 检查 always_ff 块
            if stripped.startswith('always_ff'):
                in_always = True
                continue
            
            if stripped.startswith('endmodule') or stripped.startswith('end'):
                in_always = False
                continue
            
            if in_always and '>>' in stripped:
                # 时钟分频
                match = re.search(r'(\w+)\s*>>\s*(\d+)', stripped)
                if match:
                    output = match.group(1)
                    div = int(match.group(2))
                    
                    self.result.dividers.append(ClockDivider(
                        name=output,
                        input_clock=clock_in or "unknown",
                        output_clock=output,
                        division_factor=div,
                        line_number=i
                    ))
            
            # 从 always_ff 提取时钟
            if '@(posedge' in stripped:
                match = re.search(r'@\(pos?edge\s+(\w+)', stripped)
                if match:
                    clock_in = match.group(1)
    
    def _extract_clock_buffers(self, lines: List[str], fname: str):
        """提取时钟缓冲器实例"""
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # 模块实例: BUFG inst (.I(clk), .O(clk_buf));
            for buf_type in self.BUFFER_CELLS:
                if buf_type in line.lower() and stripped.startswith(buf_type):
                    # 提取实例名
                    match = re.search(rf'{buf_type}\s+(\w+)', stripped)
                    if match:
                        name = match.group(1)
                        
                        # 提取 I/O
                        i_match = re.search(r'\.I\s*\(\s*(\w+)', stripped)
                        o_match = re.search(r'\.O\s*\(\s*(\w+)', stripped)
                        
                        if i_match and o_match:
                            self.result.buffers.append(ClockBuffer(
                                name=name,
                                cell_type=buf_type,
                                input_clock=i_match.group(1),
                                output_clock=o_match.group(1),
                                line_number=i
                            ))
    
    def _calculate_stats(self):
        """计算统计"""
        stats = self.result.stats
        
        stats.num_sources = len(self.result.sources)
        stats.num_buffers = len(self.result.buffers)
        stats.num_dividers = len(self.result.dividers)
        
        # 收集域名
        domains = set()
        for s in self.result.sources:
            if s.type == "input":
                domains.add(s.name)
        
        stats.domains = list(domains)
        
        # 计算 fanout
        for b in self.result.buffers:
            # 简化: 估算
            b.fanout = 1
        
        if self.result.buffers:
            stats.max_fanout = max(b.fanout for b in self.result.buffers)
    
    def get_clock_sources(self) -> List[ClockSource]:
        return self.result.sources
    
    def get_clock_dividers(self) -> List[ClockDivider]:
        return self.result.dividers
    
    def get_all_domains(self) -> List[str]:
        return self.result.stats.domains
    
    def find_clock_path(self, clock: str) -> List[str]:
        """查找时钟路径"""
        path = []
        
        # 从源头开始
        for src in self.result.sources:
            if src.name == clock:
                path.append(f"source:{src.name}")
        
        # 通过分频器
        for div in self.result.dividers:
            if div.input_clock == clock:
                path.append(f"divider:{div.name}")
        
        return path


def analyze_clock_tree(parser) -> ClockTreeResult:
    """便捷函数"""
    analyzer = ClockTreeAnalyzer(parser)
    return analyzer.result


# === pyslang 版本方法 (2026-04-29) ===

def extract_clock_signals_from_text(code: str) -> List[dict]:
    """从源码提取时钟信号 (使用 pyslang)"""
    import pyslang
    from pyslang import SyntaxKind
    
    results = []
    
    def collect(node):
        kind_name = node.kind.name
        
        # 提取时钟 input 端口
        if kind_name == 'ImplicitAnsiPort':
            header = getattr(node, 'header', None)
            if header:
                direction = getattr(header, 'direction', None)
                if direction and 'Input' in direction.kind.name:
                    decl = getattr(node, 'declarator', None)
                    if decl:
                        name = str(decl.name).strip()
                        if 'clk' in name.lower() or 'clock' in name.lower():
                            results.append({
                                'name': name,
                                'kind': 'clock_input',
                                'type': 'input'
                            })
        
        # 提取 always_ff 时钟
        if kind_name == 'EventControlWithExpression':
            edge = 'posedge'
            clock_name = ''
            
            for child in node:
                if child.kind.name == 'ParenthesizedEventExpression':
                    for c2 in child:
                        if c2.kind.name == 'SignalEventExpression':
                            for c3 in c2:
                                if 'Edge' in c3.kind.name:
                                    edge = 'posedge' if 'Pos' in c3.kind.name else 'negedge'
                                if c3.kind.name == 'IdentifierName':
                                    clock_name = str(c3).strip()
            
            if clock_name:
                results.append({
                    'name': clock_name,
                    'kind': 'ff_clock',
                    'edge': edge
                })
        
        return pyslang.VisitAction.Advance
    
    try:
        tree = pyslang.SyntaxTree.fromText(code)
        tree.root.visit(collect)
    except Exception as e:
        pass
    
    return results
