"""
Covergroup 解析器 - covergroup 提取
"""
import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Coverpoint:
    """coverpoint"""
    name: str = ""
    bins: List[str] = None
    
    def __init__(self):
        self.bins = []


@dataclass
class CovergroupDef:
    """covergroup 定义"""
    name: str = ""
    coverpoints: List[Coverpoint] = None
    cross: List[str] = None
    
    def __init__(self):
        self.coverpoints = []
        self.cross = []


class CovergroupExtractor:
    """Covergroup 提取器"""
    
    def __init__(self, parser):
        self.parser = parser
        self.covergroups: Dict[str, CovergroupDef] = {}
        self._extract_all_covergroups()
    
    def _extract_all_covergroups(self):
        for key, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root') or not tree.root:
                continue
            
            root = tree.root
            
            if 'CovergroupDeclaration' in str(type(root)):
                self._extract_covergroup(root)
            
            if hasattr(root, 'members') and root.members:
                for m in root.members:
                    self._find_covergroup_in_member(m)
    
    def _find_covergroup_in_member(self, member):
        type_name = str(type(member))
        
        if 'CovergroupDeclaration' in type_name:
            self._extract_covergroup(member)
        
        for attr in ['members', 'body', 'items']:
            if hasattr(member, attr):
                child = getattr(member, attr)
                if child:
                    if isinstance(child, list):
                        for c in child:
                            self._find_covergroup_in_member(c)
                    else:
                        self._find_covergroup_in_member(child)
    
    def _extract_covergroup(self, cg):
        name = ""
        coverpoints = []
        cross = []
        
        if hasattr(cg, 'name') and cg.name:
            name = cg.name.value if hasattr(cg.name, 'value') else str(cg.name)
        
        # 从 members 提取
        members = getattr(cg, 'members', [])
        
        for item in members:
            item_str = str(item)
            type_name = str(type(item))
            
            # Coverpoint
            if 'Coverpoint' in type_name:
                cp = self._parse_coverpoint(item_str)
                if cp:
                    coverpoints.append(cp)
            
            # Cross
            elif 'Cross' in type_name:
                cross.append(item_str)
        
        if name:
            cg_def = CovergroupDef()
            cg_def.name = name
            cg_def.coverpoints = coverpoints
            cg_def.cross = cross
            self.covergroups[name] = cg_def
    
    def _parse_coverpoint(self, item_str: str) -> Optional[Coverpoint]:
        cp = Coverpoint()
        
        # 匹配 coverpoint 名称
        match = re.search(r'coverpoint\s+(\w+)', item_str)
        if match:
            cp.name = match.group(1)
        elif 'coverpoint' not in item_str:
            # 可能是 inline coverpoint
            match = re.search(r'(\w+)\s*\{', item_str)
            if match:
                cp.name = match.group(1)
        
        # 提取 bins
        bins_match = re.findall(r'bins\s+(\w+)\s*=', item_str)
        for b in bins_match:
            cp.bins.append(b)
        
        return cp if cp.name else None
    
    def find_covergroup(self, name: str) -> Optional[CovergroupDef]:
        return self.covergroups.get(name)
    
    def get_all_covergroups(self) -> Dict[str, CovergroupDef]:
        return self.covergroups
