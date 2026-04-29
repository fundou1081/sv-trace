"""
DataPathBoundaryAnalyzer - Data Path 边界值推导
根据信号定义的值域和运算，推导出边界和特征点
"""
import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from dataclasses import dataclass, field
from typing import List


@dataclass
class BoundaryBin:
    """边界bin"""
    name: str
    range_expr: str
    value: int = 0
    is_edge: bool = False


@dataclass
class BoundaryResult:
    """边界分析结果"""
    signal: str
    width: int = 0
    signed: bool = False
    bins: List[BoundaryBin] = field(default_factory=list)
    
    def visualize(self) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append(f"BOUNDARY ANALYSIS: {self.signal}")
        lines.append("=" * 60)
        
        lines.append(f"\nSignal: {self.signal}[{self.width}:0]" + ("(signed)" if self.signed else ""))
        
        lines.append(f"\n📋 Generated bins:")
        for b in self.bins:
            star = "★" if b.is_edge else " "
            lines.append(f"  {star} {b.name}: {b.range_expr} (value={b.value})")
        
        lines.append("=" * 60)
        return '\n'.join(lines)


    def extract_from_text(source: str):
        """从源码文本提取datapath边界"""
        try:
            tree = pyslang.SyntaxTree.fromText(source)
            
            class TextParser:
                def __init__(self, tree):
                    self.trees = {"input.sv": tree}
                    self.compilation = tree
            
            return DataPathBoundaryAnalyzer(TextParser(tree))
        except Exception as e:
            print(f"DataPath error: {e}")
            return None

class DataPathBoundaryAnalyzer:
    """Data Path 边界分析"""
    
    def __init__(self, parser):
        self.parser = parser
    
    def analyze(self, signal: str, assignment_expr: str = "") -> BoundaryResult:
        """分析信号的边界"""
        
        result = BoundaryResult(signal=signal)
        
        # 1. 解析信号宽度
        width = self._parse_width(signal)
        result.width = width if width else 8
        result.signed = 'signed' in signal.lower() if signal else False
        
        # 2. 从赋值表达式推断
        if assignment_expr:
            operation = self._parse_operation(assignment_expr)
            
            # 生成bins
            result.bins = self._generate_bins(
                result.width,
                result.signed,
                operation
            )
        else:
            # 默认bins (基于宽度)
            result.bins = self._generate_default_bins(result.width, result.signed)
        
        return result
    
    def _parse_width(self, signal: str) -> int:
        """解析信号宽度"""
        # 查找 [N:M]
        match = re.search(r'\[(\d+):', signal)
        if match:
            return int(match.group(1)) + 1
        return 8
    
    def _parse_operation(self, expr: str) -> str:
        """解析运算类型"""
        if '+' in expr and '=' in expr:
            return 'add'
        elif '-' in expr and '=' in expr:
            return 'sub'
        elif '*' in expr and '=' in expr:
            return 'mul'
        elif '<<' in expr:
            return 'shift_left'
        elif '>>' in expr:
            return 'shift_right'
        return 'pass'
    
    def _generate_bins(self, width: int, signed: bool, operation: str) -> List[BoundaryBin]:
        """根据运算生成bins"""
        
        bins = []
        w = width
        
        # 基础边界值
        max_val = (2 ** w) - 1
        min_val = 0 if not signed else -(2 ** (w-1))
        
        if operation == 'add':
            bins.append(BoundaryBin(
                name="zero",
                range_expr="{0}",
                value=0,
                is_edge=True
            ))
            bins.append(BoundaryBin(
                name="min",
                range_expr=f"{min_val}",
                value=min_val,
                is_edge=True
            ))
            bins.append(BoundaryBin(
                name="max",
                range_expr=f"{max_val}",
                value=max_val,
                is_edge=True
            ))
            # 进位溢出
            if signed:
                bins.append(BoundaryBin(
                    name="overflow_pos",
                    range_expr=f"[{max_val-1}:{max_val}]",
                    value=max_val,
                    is_edge=False
                ))
                bins.append(BoundaryBin(
                    name="overflow_neg",
                    range_expr=f"[{min_val}:{min_val+1}]",
                    value=min_val,
                    is_edge=False
                ))
        
        elif operation == 'sub':
            # 类似add但方向相反
            bins.append(BoundaryBin(name="zero", range_expr="{0}", value=0, is_edge=True))
            bins.append(BoundaryBin(name="max", range_expr=f"{max_val}", value=max_val, is_edge=True))
            bins.append(BoundaryBin(name="min", range_expr=f"{min_val}", value=min_val, is_edge=True))
        
        elif operation == 'shift_left':
            bins.append(BoundaryBin(name="zero", range_expr="{0}", value=0, is_edge=True))
            bins.append(BoundaryBin(name="one_bit_set", range_expr="1", value=1, is_edge=True))
            bins.append(BoundaryBin(name="all_bits_set", range_expr=f"{max_val}", value=max_val, is_edge=True))
        
        else:
            # 默认
            bins = self._generate_default_bins(width, signed)
        
        return bins
    
    def _generate_default_bins(self, width: int, signed: bool) -> List[BoundaryBin]:
        """生成默认bins"""
        
        bins = []
        w = width
        max_val = (2 ** w) - 1
        min_val = 0 if not signed else -(2 ** (w-1))
        
        # 常用边界
        bins.append(BoundaryBin(name="zero", range_expr="{0}", value=0, is_edge=True))
        bins.append(BoundaryBin(name="max", range_expr=f"{max_val}", value=max_val, is_edge=True))
        bins.append(BoundaryBin(name="mid", range_expr=f"{max_val//2}", value=max_val//2, is_edge=False))
        
        if signed:
            bins.append(BoundaryBin(name="min", range_expr=f"{min_val}", value=min_val, is_edge=True))
        
        return bins


def analyze_datapath_boundary(parser, signal: str) -> BoundaryResult:
    analyzer = DataPathBoundaryAnalyzer(parser)
    return analyzer.analyze(signal)
