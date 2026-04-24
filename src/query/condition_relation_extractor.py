"""
ConditionRelationExtractor - if/case 条件关系自动提取
用户在写data path coverage时，需要知道信号的条件关系
"""
import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from dataclasses import dataclass, field
from typing import List, Dict, Set


@dataclass
class Condition:
    """条件"""
    type: str = ""           # if/else if/case
    condition: str = ""       # 条件表达式
    depth: int = 0           # 嵌套深度
    value: str = ""          # case值
    children: List['Condition'] = field(default_factory=list)


@dataclass
class ConditionRelation:
    """条件关系"""
    target_signal: str
    conditions: List[Condition] = field(default_factory=list)
    cross_bins: List[str] = field(default_factory=list)
    
    def visualize(self) -> str:
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
    """条件关系提取器"""
    
    def __init__(self, parser):
        self.parser = parser
    
    def extract(self, signal: str, module: str = None) -> ConditionRelation:
        """提取信号的条件关系"""
        
        result = ConditionRelation(target_signal=signal)
        
        # 从代码中查找该信号的所有赋值
        for fname, tree in self.parser.trees.items():
            code = self._get_code(fname)
            if not code:
                continue
            
            # 查找信号的所有赋值语句
            assignments = self._find_assignments(code, signal)
            
            # 提取条件
            conditions = self._extract_conditions(assignments)
            result.conditions.extend(conditions)
        
        # 生成cross bins
        result.cross_bins = self._generate_cross_bins(result.conditions)
        
        return result
    
    def _find_assignments(self, code: str, signal: str) -> List[str]:
        """查找信号的所有赋值"""
        
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
    
    def _extract_conditions(self, assignments: List[str]) -> List[Condition]:
        """提取条件"""
        
        conditions = []
        
        for assign in assignments:
            cond = Condition(type="assignment", condition=assign.strip())
            
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
            
            # 查找case/else
            if 'case' in assign:
                cond.type = "case"
                # 简化: 提取所有值
                values = re.findall(r'\d+', assign)
                if values:
                    cond.value = ','.join(set(values))
                conditions.append(cond)
        
        return conditions
    
    def _generate_cross_bins(self, conditions: List[Condition]) -> List[str]:
        """生成cross bins"""
        
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
    extractor = ConditionRelationExtractor(parser)
    return extractor.extract(signal)
