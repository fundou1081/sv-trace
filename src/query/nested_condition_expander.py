"""NestedConditionExpander - 嵌套条件完全展开。

将嵌套 if 展开到最底层，生成独立的条件组合。
用于 coverage bin 生成。

Example:
    >>> from query.nested_condition_expander import NestedConditionExpander
    >>> expander = NestedConditionExpander(parser)
    >>> result = expander.expand("a && (b || c)")
    >>> print(result.visualize())
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from dataclasses import dataclass, field
from typing import List


@dataclass
class ExpandedCondition:
    """展开后的条件数据类。
    
    Attributes:
        expression: 完整表达式
        level: 嵌套层级
        is_leaf: 是否为叶子条件
    """
    expression: str
    level: int = 0
    is_leaf: bool = False


@dataclass
class ExpandedResult:
    """展开结果数据类。
    
    Attributes:
        original: 原始表达式
        expanded: 展开后的条件列表
        total_bins: 总 bin 数
    """
    original: str
    expanded: List[ExpandedCondition] = field(default_factory=list)
    total_bins: int = 0
    
    def visualize(self) -> str:
        """可视化展开结果。
        
        Returns:
            str: 格式化的报告字符串
        """
        lines = []
        lines.append("=" * 60)
        lines.append(f"NESTED IF EXPANSION")
        lines.append("=" * 60)
        lines.append(f"\nOriginal: {self.original}")
        lines.append(f"\n📋 Expanded to {self.total_bins} bins:")
        
        for e in self.expanded:
            indent = "  " * e.level
            lines.append(f"{indent}{e.expression}")
        
        lines.append("=" * 60)
        return '\n'.join(lines)


class NestedConditionExpander:
    """嵌套条件展开器。
    
    将嵌套的条件表达式展开为独立的条件组合。

    Attributes:
        parser: SVParser 实例
    
    Example:
        >>> expander = NestedConditionExpander(parser)
        >>> result = expander.expand("a && (b || c)")
    """
    
    def __init__(self, parser):
        """初始化展开器。
        
        Args:
            parser: SVParser 实例
        """
        self.parser = parser
    
    def expand(self, condition_expr: str) -> ExpandedResult:
        """展开嵌套条件。
        
        Args:
            condition_expr: 条件表达式字符串
        
        Returns:
            ExpandedResult: 展开结果
        """
        result = ExpandedResult(original=condition_expr)
        
        # 简单展开: 递归展开嵌套的组合逻辑
        expanded = self._expand_recursive(condition_expr, level=0)
        
        result.expanded = expanded
        result.total_bins = len(expanded)
        
        return result
    
    def _expand_recursive(self, expr: str, level: int) -> List[ExpandedCondition]:
        """递归展开。
        
        Args:
            expr: 表达式字符串
            level: 当前层级
        
        Returns:
            List[ExpandedCondition]: 展开后的条件列表
        """
        results = []
        
        # 1. 检测嵌套的 &&
        if '&&' in expr:
            parts = expr.split('&&')
            combined = []
            current = parts[0].strip()
            
            for p in parts[1:]:
                p = p.strip()
                # 展开每个部分
                sub = self._expand_single(p, level+1)
                for s in sub:
                    new_expr = f"{current} && {s.expression}"
                    combined.append(ExpandedCondition(
                        expression=new_expr,
                        level=level,
                        is_leaf=True
                    ))
            
            results.extend(combined)
        
        # 2. 检测嵌套的 ||
        elif '||' in expr:
            parts = expr.split('||')
            for p in parts:
                p = p.strip()
                sub = self._expand_single(p, level+1)
                results.extend(sub)
        
        # 3. 简单表达式
        else:
            results = self._expand_single(expr, level)
        
        return results
    
    def _expand_single(self, expr: str, level: int) -> List[ExpandedCondition]:
        """展开单个表达式。
        
        Args:
            expr: 表达式字符串
            level: 当前层级
        
        Returns:
            List[ExpandedCondition]: 展开后的条件列表
        """
        results = []
        
        # 移除括号
        expr = expr.strip('()')
        
        # 展开 == 值为多个可能值
        match_eq = expr.split('==')
        if len(match_eq) == 2:
            lhs = match_eq[0].strip()
            rhs = match_eq[1].strip()
            
            # 检测是否是组合逻辑
            if '(' in rhs:
                # 展开组合逻辑
                inner = rhs.strip('()')
                results.append(ExpandedCondition(
                    expression=f"{lhs}=={inner}",
                    level=level,
                    is_leaf=True
                ))
            else:
                results.append(ExpandedCondition(
                    expression=expr,
                    level=level,
                    is_leaf=True
                ))
        else:
            results.append(ExpandedCondition(
                expression=expr,
                level=level,
                is_leaf=True
            ))
        
        return results


def expand_nested_condition(parser, condition: str) -> ExpandedResult:
    """便捷函数：展开嵌套条件。
    
    Args:
        parser: SVParser 实例
        condition: 条件表达式
    
    Returns:
        ExpandedResult: 展开结果
    """
    expander = NestedConditionExpander(parser)
    return expander.expand(condition)
