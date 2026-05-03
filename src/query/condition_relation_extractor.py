"""ConditionRelationExtractor - if/case 条件关系自动提取。

用户在写 data path coverage 时，需要知道信号的条件关系。
自动提取条件表达式和嵌套关系。

Example:
    >>> from query.condition_relation_extractor import ConditionRelationExtractor
    >>> from parse import SVParser
    >>> parser = SVParser()
    >>> parser.parse_file("design.sv")
    >>> extractor = ConditionRelationExtractor(parser)
    >>> relation = extractor.extract("data_out")
    >>> print(relation.visualize())
"""
import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from dataclasses import dataclass, field
from typing import List, Dict, Set


@dataclass
class Condition:
    """条件数据类。
    
    Attributes:
        type: 条件类型 (if/else if/case/literal/assignment)
        condition: 条件表达式
        depth: 嵌套深度
        value: case 值
        children: 子条件列表
    """
    type: str = ""           # if/else if/case
    condition: str = ""       # 条件表达式
    depth: int = 0           # 嵌套深度
    value: str = ""          # case值
    children: List['Condition'] = field(default_factory=list)


@dataclass
class ConditionRelation:
    """条件关系数据类。
    
    Attributes:
        target_signal: 目标信号名
        conditions: 条件列表
        cross_bins: 交叉区间列表
    """
    target_signal: str
    conditions: List[Condition] = field(default_factory=list)
    cross_bins: List[str] = field(default_factory=list)
    
    def visualize(self) -> str:
        """可视化条件关系。
        
        Returns:
            str: 格式化的报告字符串
        """
        lines = []
        lines.append("=" * 60)
        lines.append(f"CONDITION RELATION: {self.target_signal}")
        lines.append("=" * 60)
        
        # 显示条件树
        lines.append("\n📋 Condition Tree:")
        for c in self.conditions:
            prefix = "  " * c.depth
            if c.type == "if":
                lines.append(f"{prefix}if ({c.condition})")
            elif c.type == "else if":
                lines.append(f"{prefix}else if ({c.condition})")
            elif c.type == "case":
                lines.append(f"{prefix}case ({c.condition})")
                for v in c.value.split(','):
                    lines.append(f"{prefix}  - {v.strip()}")
        
        # 显示cross bins
        if self.cross_bins:
            lines.append(f"\n📋 Cross Bins:")
            for b in self.cross_bins:
                lines.append(f"  - {b}")
        
        lines.append("=" * 60)
        return '\n'.join(lines)


class ConditionRelationExtractor:
    """条件关系提取器。
    
    从代码中提取信号的条件关系，支持 if/case 嵌套。

    Attributes:
        parser: SVParser 实例
    
    Example:
        >>> extractor = ConditionRelationExtractor(parser)
        >>> relation = extractor.extract("data_out")
    """
    
    def __init__(self, parser):
        """初始化提取器。
        
        Args:
            parser: SVParser 实例
        """
        self.parser = parser
    
    def extract(self, signal: str, module: str = None) -> ConditionRelation:
        """提取信号的条件关系。
        
        Args:
            signal: 目标信号名
            module: 可选的模块名过滤
        
        Returns:
            ConditionRelation: 条件关系对象
        """
        result = ConditionRelation(target_signal=signal)
        
        # 从代码中查找该信号的所有赋值
        for fname, tree in self.parser.trees.items():
            code = self._get_code(fname)
            if not code:
                continue
            
            # 查找信号的所有赋值语句
            assignments = self._find_assignments(code, signal)
            
            # 提取条件 (pass full code for case value extraction)
            conditions = self._extract_conditions(assignments, code)
            result.conditions.extend(conditions)
        
        # 生成cross bins
        result.cross_bins = self._generate_cross_bins(result.conditions)
        
        return result
    
    def _find_assignments(self, code: str, signal: str) -> List[str]:
        """查找信号的所有赋值。
        
        Args:
            code: 源代码
            signal: 信号名
        
        Returns:
            List[str]: 赋值表达式列表
        """
        assignments = []
        
        # 查找 signal <= xxx 或 signal = xxx
        pattern = rf'{signal}\s*(?:<=|=)\s*([^;]+)'
        
        for line in code.split('\n'):
            if re.search(pattern, line):
                # 提取赋值内容
                match = re.search(pattern, line)
                if match:
                    assignments.append(match.group(1))
        
        return assignments
    
    def _extract_conditions(self, assignments: List[str], full_code: str = None) -> List[Condition]:
        """提取条件。
        
        Args:
            assignments: 赋值表达式列表
            full_code: 完整源代码
        
        Returns:
            List[Condition]: 条件列表
        """
        conditions = []
        
        for assign in assignments:
            assign = assign.strip()
            
            # Skip if assign looks like a literal (number)
            if assign.isdigit() or assign.isnumeric():
                # This is a simple assignment value
                # Create condition from it
                cond = Condition(type="literal", condition=assign)
                conditions.append(cond)
                continue
            
            cond = Condition(type="assignment", condition=assign)
            
            # 查找if条件
            if 'if' in assign:
                if_match = re.search(r'if\s*\(\s*(.+?)\)', assign)
                if if_match:
                    cond.type = "if"
                    cond.condition = if_match.group(1).strip()
                    conditions.append(cond)
            
            # 查找else if条件
            if 'else if' in assign:
                elif_match = re.search(r'else\s+if\s*\(\s*(.+?)\)', assign)
                if elif_match:
                    cond = Condition(type="else if", condition=elif_match.group(1).strip())
                    conditions.append(cond)
            
            # For case statements, extract the case expression
            if full_code and 'case' in full_code:
                # Extract case values
                case_values = re.findall(r"2'b(\d+)", full_code)
                if case_values:
                    # Create condition for each case value
                    for cv in set(case_values):
                        cond = Condition(type="case", condition=f"2'b{cv}")
                        cond.value = cv
                        conditions.append(cond)
            
            # For nested ifs, extract conditions from full_code
            if full_code and 'if' in full_code:
                if_conditions = re.findall(r'if\s*\(\s*(\w+)\s*\)', full_code)
                for ic in if_conditions:
                    if ic and ic != 'else':
                        cond = Condition(type="if", condition=ic)
                        conditions.append(cond)
        
        return conditions
    
    def _generate_cross_bins(self, conditions: List[Condition]) -> List[str]:
        """生成 cross bins。
        
        Args:
            conditions: 条件列表
        
        Returns:
            List[str]: 交叉区间列表
        """
        bins = []
        
        # 收集所有条件值
        values_by_depth = {0: []}
        depth = 0
        
        for c in conditions:
            if c.type in ['if', 'else if']:
                if c.condition not in values_by_depth[depth]:
                    values_by_depth[depth].append(c.condition)
            elif c.type == 'case':
                if c.value:
                    values_by_depth.setdefault(depth+1, []).extend(c.value.split(','))
        
        # 生成组合
        for depth, vals in values_by_depth.items():
            if vals:
                for v in vals[:10]:  # 限制数量
                    bins.append(v.strip())
        
        return bins[:20]
    
    def _get_code(self, fname: str) -> str:
        """获取源码。
        
        Args:
            fname: 文件名
        
        Returns:
            str: 源代码字符串
        """
        # Use parser's get_source method if available
        if hasattr(self.parser, 'get_source'):
            source = self.parser.get_source(fname)
            if source:
                return source
        
        if fname in self.parser.trees:
            t = self.parser.trees[fname]
            if hasattr(t, 'source'):
                return t.source
        try:
            with open(fname) as f:
                return f.read()
        except:
            return ""


def extract_condition_relation(parser, signal: str) -> ConditionRelation:
    """便捷函数：提取信号的条件关系。
    
    Args:
        parser: SVParser 实例
        signal: 信号名
    
    Returns:
        ConditionRelation: 条件关系对象
    """
    extractor = ConditionRelationExtractor(parser)
    return extractor.extract(signal)
