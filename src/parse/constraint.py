"""
Constraint 解析器 - constraint 块提取
"""
import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ConstraintBlock:
    """constraint 块"""
    name: str = ""
    constraints: List[str] = None
    
    def __init__(self):
        self.constraints = []


class ConstraintExtractor:
    """Constraint 提取器"""
    
    def __init__(self, parser):
        self.parser = parser
        self.constraints: Dict[str, List[ConstraintBlock]] = {}
        self._extract_all_constraints()
    
    def _extract_all_constraints(self):
        for key, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root') or not tree.root:
                continue
            
            root = tree.root
            
            if 'ClassDeclaration' in str(type(root)):
                self._extract_from_class(root)
            
            if hasattr(root, 'members') and root.members:
                for m in root.members:
                    self._find_class_in_member(m)
    
    def _find_class_in_member(self, member):
        type_name = str(type(member))
        
        if 'ClassDeclaration' in type_name:
            self._extract_from_class(member)
        
        for attr in ['members', 'body']:
            if hasattr(member, attr):
                child = getattr(member, attr)
                if child:
                    if isinstance(child, list):
                        for c in child:
                            self._find_class_in_member(c)
                    else:
                        self._find_class_in_member(child)
    
    def _extract_from_class(self, cls):
        class_name = ""
        if hasattr(cls, 'name') and cls.name:
            class_name = cls.name.value if hasattr(cls.name, 'value') else str(cls.name)
        
        items = getattr(cls, 'items', [])
        
        for item in items:
            type_name = str(type(item))
            item_str = str(item)
            
            # ConstraintDeclarationSyntax
            if 'ConstraintDeclaration' in type_name:
                block = self._parse_constraint_block(item_str)
                if block:
                    if class_name not in self.constraints:
                        self.constraints[class_name] = []
                    self.constraints[class_name].append(block)
    
    def _parse_constraint_block(self, item_str: str) -> Optional[ConstraintBlock]:
        block = ConstraintBlock()
        
        # 匹配 constraint 块名
        match = re.search(r'constraint\s+(\w+)\s*\{', item_str)
        if match:
            block.name = match.group(1)
        
        # 提取约束内容 - 简单从字符串解析
        # 去掉 { }
        content = re.sub(r'constraint\s+\w+\s*\{', '', item_str)
        content = content.rstrip('}').strip()
        
        if content:
            lines = content.split(';')
            for line in lines:
                line = line.strip()
                if line:
                    block.constraints.append(line)
        
        return block if block.constraints else None
    
    def find_constraints(self, class_name: str) -> List[ConstraintBlock]:
        return self.constraints.get(class_name, [])
    
    def get_all_constraints(self) -> Dict[str, List[ConstraintBlock]]:
        return self.constraints
