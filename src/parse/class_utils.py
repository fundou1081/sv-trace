"""
Class 解析器 - class 成员、方法提取
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, List, Optional
from dataclasses import dataclass
import re


@dataclass
class ClassMethod:
    name: str = ""
    kind: str = "function"
    return_type: str = "void"


@dataclass  
class ClassMember:
    name: str = ""
    data_type: str = "logic"
    width: int = 1
    rand_mode: str = ""


class ClassExtractor:
    def __init__(self, parser):
        self.parser = parser
        self.classes: Dict[str, Dict] = {}
        self._extract_all_classes()
    
    def _extract_all_classes(self):
        for key, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root') or not tree.root:
                continue
            
            root = tree.root
            
            if 'ClassDeclaration' in str(type(root)):
                self._extract_class(root)
            
            if hasattr(root, 'members') and root.members:
                for m in root.members:
                    self._find_class_in_member(m)
    
    def _find_class_in_member(self, member):
        type_name = str(type(member))
        
        if 'ClassDeclaration' in type_name:
            self._extract_class(member)
        
        for attr in ['members', 'body']:
            if hasattr(member, attr):
                child = getattr(member, attr)
                if child:
                    if isinstance(child, list):
                        for c in child:
                            self._find_class_in_member(c)
                    else:
                        self._find_class_in_member(child)
    
    def _extract_class(self, cls):
        name = ""
        members = []
        methods = []
        
        if hasattr(cls, 'name') and cls.name:
            name = cls.name.value if hasattr(cls.name, 'value') else str(cls.name)
        
        items = getattr(cls, 'items', [])
        
        for item in items:
            item_str = str(item)
            type_name = str(type(item))
            
            # ClassPropertyDeclaration - 检查属性
            if 'PropertyDeclaration' in type_name:
                if hasattr(item, 'declaration') and item.declaration:
                    decl = item.declaration
                    if hasattr(decl, 'declarators') and decl.declarators:
                        for d in decl.declarators:
                            m_name = d.name.value if hasattr(d.name, 'value') else str(d.name)
                            if m_name:
                                rand_mode = str(item.randMode) if hasattr(item, 'randMode') else ""
                                members.append(ClassMember(name=m_name, rand_mode=rand_mode))
            
            # 方法 - 从字符串提取
            elif 'MethodDeclaration' in type_name or 'FunctionDeclaration' in type_name:
                # 匹配函数: "function ... 函数名(...)" 或 "task ... 函数名(...)"
                match = re.search(r'(function|task)\s+(\w+)\s+(\w+)', item_str)
                if match:
                    kind = match.group(1)  # function 或 task
                    return_type = match.group(2)
                    m_name = match.group(3)
                    methods.append(ClassMethod(name=m_name, kind=kind, return_type=return_type))
        
        if name:
            self.classes[name] = {
                "name": name,
                "members": members,
                "methods": methods,
            }
    
    def find_class(self, name: str) -> Optional[Dict]:
        return self.classes.get(name)
    
    def get_all_classes(self) -> Dict[str, Dict]:
        return self.classes
