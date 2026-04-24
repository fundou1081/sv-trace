"""
CoverageGenerator - 智能覆盖率生成器 (v2)
基于 DUT I/O 自动生成 Coverage、智能 sample 条件、自动 Cross
"""
import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class IOSignal:
    name: str
    direction: str
    width: int = 1
    is_valid: bool = False
    is_ready: bool = False
    is_data: bool = False


@dataclass
class CoverageBin:
    name: str
    value: str


@dataclass
class CoveragePoint:
    name: str
    signal: str
    width: int = 1
    bins: List[CoverageBin] = field(default_factory=list)
    is_valid: bool = False


@dataclass
class CoverGroup:
    name: str
    sample_clock: str = "clk"
    sample_event: str = ""  # 智能 sample 条件
    points: List[CoveragePoint] = field(default_factory=list)
    
    def generate_code(self) -> str:
        lines = []
        event = self.sample_event if self.sample_event else f"@{self.sample_clock}"
        
        lines.append(f"covergroup {self.name} {event} {{")
        
        for pt in self.points:
            if pt.bins:
                lines.append(f"    {pt.name}: coverpoint {pt.signal} {{")
                for b in pt.bins:
                    lines.append(f"        bins {b.name} = {b.value};")
                lines.append("    }")
        
        lines.append("}")
        lines.append("endgroup")
        
        return '\n'.join(lines)


@dataclass
class CoverageCross:
    name: str
    points: List[str]


@dataclass
class Result:
    ios: List[IOSignal] = field(default_factory=list)
    groups: List[CoverGroup] = field(default_factory=list)
    
    def visualize(self) -> str:
        lines = ["=" * 60, "COVERAGE GENERATION (v2)", "=" * 60]
        
        valid_signals = [io.name for io in self.ios if io.is_valid]
        data_signals = [io.name for io in self.ios if io.is_data]
        
        lines.append(f"\n📊 Signals:")
        lines.append(f"  Data: {data_signals}")
        lines.append(f"  Valid: {valid_signals}")
        
        lines.append(f"\n📊 Sample Event:")
        
        for g in self.groups:
            if g.sample_event:
                lines.append(f"  {g.name}: {g.sample_event}")
        
        lines.append("=" * 60)
        return '\n'.join(lines)


class CoverageGenerator:
    VALID_KW = ['valid', 'vld', 'v']
    READY_KW = ['ready', 'rdy']
    DATA_KW = ['data', 'din', 'pkt', 'payload']
    
    def __init__(self, parser):
        self.parser = parser
    
    def generate(self, module_name: str = None) -> Result:
        ios = self._extract_ios()
        
        if not ios:
            return Result()
        
        # 分析 sample 条件
        sample_event = self._compute_sample_event(ios)
        
        # 创建 covergroup
        cg = CoverGroup(
            name="dut_io_cov",
            sample_clock="posedge clk",
            sample_event=sample_event
        )
        
        # 生成 data coverpoints
        for io in ios:
            if io.is_data and io.direction == 'input':
                pt = self._generate_datapt(io)
                cg.points.append(pt)
        
        # 生成 valid coverpoints
        for io in ios:
            if io.is_valid and io.direction == 'input':
                pt = CoveragePoint(
                    name=f"{io.name}_cov",
                    signal=io.name,
                    is_valid=True
                )
                pt.bins = [
                    CoverageBin(name="low", value="{0}"),
                    CoverageBin(name="high", value="{1}")
                ]
                cg.points.append(pt)
        
        result = Result(ios=ios, groups=[cg])
        
        return result
    
    def _extract_ios(self) -> List[IOSignal]:
        ios = []
        
        for fname, tree in self.parser.trees.items():
            code = self._get_code(fname)
            if not code:
                continue
            
            in_mod = False
            for line in code.split('\n'):
                line = line.strip()
                
                if line.startswith('module '):
                    in_mod = True
                    continue
                if line.startswith('endmodule'):
                    in_mod = False
                    continue
                if not in_mod:
                    continue
                
                # input
                if line.startswith('input'):
                    io = self._parse_io(line, 'input')
                    if io:
                        ios.append(io)
                # output
                elif line.startswith('output'):
                    io = self._parse_io(line, 'output')
                    if io:
                        ios.append(io)
            
            break
        
        return self._link_signals(ios)
    
    def _parse_io(self, line: str, direction: str) -> Optional[IOSignal]:
        # [7:0] data
        m = re.search(rf'{direction}\s*\[(\d+):(\d+)\]\s+(\w+)', line)
        if m:
            w = int(m.group(1)) + 1
            name = m.group(3)
            return IOSignal(
                name=name, direction=direction, width=w,
                is_valid=any(k in name.lower() for k in self.VALID_KW),
                is_data=any(k in name.lower() for k in self.DATA_KW),
                is_ready=any(k in name.lower() for k in self.READY_KW)
            )
        
        # 1-bit
        m = re.search(rf'{direction}\s+(\w+)', line)
        if m:
            name = m.group(1)
            return IOSignal(
                name=name, direction=direction, width=1,
                is_valid=any(k in name.lower() for k in self.VALID_KW),
                is_data=any(k in name.lower() for k in self.DATA_KW),
                is_ready=any(k in name.lower() for k in self.READY_KW)
            )
        
        return None
    
    def _link_signals(self, ios: List[IOSignal]) -> List[IOSignal]:
        for io in ios:
            if io.is_valid:
                for other in ios:
                    if other != io and other.direction == io.direction:
                        base1 = re.sub(r'(valid|ready|vld|rdy)$', '', io.name, flags=re.IGNORECASE)
                        base2 = re.sub(r'(valid|ready|vld|rdy)$', '', other.name, flags=re.IGNORECASE)
                        if base1 == base2:
                            other.is_data = True
        return ios
    
    def _compute_sample_event(self, ios: List[IOSignal]) -> str:
        """计算智能 sample 条件"""
        
        # 找 valid 信号
        valid_signals = [io.name for io in ios if io.is_valid and io.direction == 'input']
        ready_signals = [io.name for io in ios if io.is_ready and io.direction == 'output']
        
        if valid_signals:
            # 模式1: valid 有效时 sample
            v = valid_signals[0]
            
            # 检查是否 active_low
            if v.endswith('_n'):
                return f"@(negedge {v})"
            else:
                return f"@(posedge {v})"
        
        if ready_signals:
            # 模式2: ready 握手完成时 sample
            r = ready_signals[0]
            if valid_signals:
                return f"@{valid_signals[0]} and {r}"
        
        # 默认: 时钟上升沿且 valid=1
        if valid_signals:
            return f"@(posedge clk) iff ({valid_signals[0]} == 1)"
        
        return "@(posedge clk)"
    
    def _generate_datapt(self, io: IOSignal) -> CoveragePoint:
        pt = CoveragePoint(name=f"{io.name}_cov", signal=io.name, width=io.width)
        
        w = io.width
        if w == 1:
            pt.bins = [
                CoverageBin(name="zero", value="{0}"),
                CoverageBin(name="one", value="{1}")
            ]
        elif w <= 4:
            for i in range(min(8, 2**w)):
                pt.bins.append(CoverageBin(name=f"v{i}", value=f"{{{i}}}"))
            pt.bins.append(CoverageBin(name="others", value="default"))
        else:
            pt.bins = [
                CoverageBin(name="zero", value="{0}"),
                CoverageBin(name="low", value="{[1:31]}"),
                CoverageBin(name="mid", value="{[32:127]}"),
                CoverageBin(name="high", value="{[128:223]}"),
                CoverageBin(name="max", value="default")
            ]
        
        return pt


    def _get_code(self, fname):
        if fname in self.parser.trees:
            t = self.parser.trees[fname]
            if hasattr(t, 'source') and t.source:
                return t.source
        try:
            with open(fname) as f:
                return f.read()
        except:
            return ""

def generate_coverage(parser, module_name: str = None) -> Result:
    gen = CoverageGenerator(parser)
    return gen.generate(module_name)
