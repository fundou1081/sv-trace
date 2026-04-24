"""
NestedConditionExpander - 嵌套条件完全展开
将嵌套if展开到最底层
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from dataclasses import dataclass, field
from typing import List


@dataclass
class ExpandedCondition:
    """展开后的条件"""
    expression: str
    level: int = 0
    is_leaf: bool = False


@dataclass
class ExpandedResult:
    """展开结果"""
    original: str
    expanded: List[ExpandedCondition] = field(default_factory=list)
    total_bins: int = 0
    
    def visualize(self) -> str:
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
    """嵌套条件展开器"""
    
    def __init__(self, parser):
        self.parser = parser
    
    def expand(self, condition_expr: str) -> ExpandedResult:
        """展开嵌套条件"""
        
        result = ExpandedResult(original=condition_expr)
        
        # 简单展开: 递归展开嵌套的组合逻辑
        expanded = self._expand_recursive(condition_expr, level=0)
        
        result.expanded = expanded
        result.total_bins = len(expanded)
        
        return result
    
    def _expand_recursive(self, expr: str, level: int) -> List[ExpandedCondition]:
        """递归展开"""
        
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
        """展开单个表达式"""
        
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
    expander = NestedConditionExpander(parser)
    return expander.expand(condition)
