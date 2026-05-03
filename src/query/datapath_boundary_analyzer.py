"""DataPathBoundaryAnalyzer - Data Path 边界值推导。

根据信号定义的值域和运算，推导出边界和特征点。
用于 coverage bin 生成和边界测试。

Example:
    >>> from query.datapath_boundary_analyzer import DataPathBoundaryAnalyzer
    >>> from parse import SVParser
    >>> parser = SVParser()
    >>> parser.parse_file("design.sv")
    >>> analyzer = DataPathBoundaryAnalyzer(parser)
    >>> result = analyzer.analyze("data_out", "data_out = a + b")
    >>> print(result.visualize())
"""
import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from dataclasses import dataclass, field
from typing import List


@dataclass
class BoundaryBin:
    """边界 bin 数据类。
    
    Attributes:
        name: bin 名称
        range_expr: 范围表达式
        value: 边界值
        is_edge: 是否为边界点
    """
    name: str
    range_expr: str
    value: int = 0
    is_edge: bool = False


@dataclass
class BoundaryResult:
    """边界分析结果数据类。
    
    Attributes:
        signal: 信号名
        width: 信号位宽
        signed: 是否有符号
        bins: 边界 bin 列表
    """
    signal: str
    width: int = 0
    signed: bool = False
    bins: List[BoundaryBin] = field(default_factory=list)
    
    def visualize(self) -> str:
        """可视化边界分析结果。
        
        Returns:
            str: 格式化的报告字符串
        """
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
    
    @staticmethod
    def extract_from_text(source: str):
        """从源码文本提取 datapath 边界。
        
        Args:
            source: SystemVerilog 源代码字符串
        
        Returns:
            DataPathBoundaryAnalyzer: 分析器实例
        """
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
    """Data Path 边界分析器。
    
    分析数据通路的信号边界，生成 coverage bins。

    Attributes:
        parser: SVParser 实例
    
    Example:
        >>> analyzer = DataPathBoundaryAnalyzer(parser)
        >>> result = analyzer.analyze("data_out", "data_out = a + b")
    """
    
    def __init__(self, parser):
        """初始化分析器。
        
        Args:
            parser: SVParser 实例
        """
        self.parser = parser
    
    def analyze(self, signal: str, assignment_expr: str = "") -> BoundaryResult:
        """分析信号的边界。
        
        Args:
            signal: 信号名
            assignment_expr: 可选的赋值表达式
        
        Returns:
            BoundaryResult: 边界分析结果
        """
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
        """解析信号宽度。
        
        Args:
            signal: 信号名或信号定义
        
        Returns:
            int: 位宽值
        """
        # 查找 [N:M]
        match = re.search(r'\[(\d+):', signal)
        if match:
            return int(match.group(1)) + 1
        return 8
    
    def _parse_operation(self, expr: str) -> str:
        """解析运算类型。
        
        Args:
            expr: 表达式字符串
        
        Returns:
            str: 运算类型 (add/sub/mul/shift_left/shift_right/pass)
        """
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
        """根据运算生成 bins。
        
        Args:
            width: 位宽
            signed: 是否有符号
            operation: 运算类型
        
        Returns:
            List[BoundaryBin]: 边界 bin 列表
        """
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
        """生成默认 bins。
        
        Args:
            width: 位宽
            signed: 是否有符号
        
        Returns:
            List[BoundaryBin]: 边界 bin 列表
        """
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
    """便捷函数：分析信号边界。
    
    Args:
        parser: SVParser 实例
        signal: 信号名
    
    Returns:
        BoundaryResult: 边界分析结果
    """
    analyzer = DataPathBoundaryAnalyzer(parser)
    return analyzer.analyze(signal)
