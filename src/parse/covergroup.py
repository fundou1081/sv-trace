"""
Covergroup 解析器 - 使用 pyslang AST
"""
import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, List
from dataclasses import dataclass, field
import pyslang
from pyslang import SyntaxKind


@dataclass
class Coverpoint:
    name: str = ""
    bins: List[str] = field(default_factory=list)


@dataclass
class CovergroupDef:
    name: str = ""
    coverpoints: List[Coverpoint] = field(default_factory=list)
    cross: List[str] = field(default_factory=list)


class CovergroupExtractor:
    def __init__(self, parser=None):
        self.parser = parser
        self.covergroups = {}
        
        if parser:
            self._extract_all()
    
    def _extract_all(self):
        for key, tree in getattr(self.parser, 'trees', {}).items():
            if tree and hasattr(tree, 'root') and tree.root:
                self._extract_from_tree(tree)
    
    def _extract_from_tree(self, tree):
        def collect(node):
            if node.kind == SyntaxKind.CovergroupDeclaration:
                self._extract_covergroup(node)
            return pyslang.VisitAction.Advancee
        
        tree.root.visit(collect)
    
    def _extract_covergroup(self, node):
        cg = CovergroupDef()
        
        # name
        if node.name:
            cg.name = str(node.name)
        
        # coverpoints - 从 members
        if node.members:
            for m in node.members:
                if not m:
                    continue
                
                if m.kind == SyntaxKind.Coverpoint:
                    # 名称
                    cp = Coverpoint()
                    if hasattr(m, 'identifier') and m.identifier:
                        cp.name = str(m.identifier)
                    
                    # bins
                    for child in m:
                        if 'Bin' in child.kind.name or child.kind.name == 'Coverpoint':
                            for c in child:
                                sb = str(c).strip()
                                if sb:
                                    cp.bins.append(sb)
                    
                    if cp.name:
                        cg.coverpoints.append(cp)
                
                # CoverCross
                elif m.kind == SyntaxKind.CoverCross:
                    cross_name = str(m).strip()
                    if cross_name:
                        cg.cross.append(cross_name)
        
        # 从字符串提取备选
        if not cg.coverpoints and not cg.cross:
            str_repr = str(node)
            for match in re.finditer(r'coverpoint\s+(\w+)', str_repr):
                cg.coverpoints.append(Coverpoint(name=match.group(1)))
            for match in re.finditer(r'cross\s+([\w,\s]+)', str_repr):
                cg.cross.append(match.group(1).strip())
        
        if cg.name:
            self.covergroups[cg.name] = cg
    
    def get_covergroups(self):
        return self.covergroups


def extract_covergroups(code):
    tree = pyslang.SyntaxTree.fromText(code)
    extractor = CovergroupExtractor(None)
    extractor._extract_from_tree(tree)
    return extractor.covergroups


if __name__ == "__main__":
    test_code = '''class test;
    covergroup cg with function sample(bit [7:0] data);
        coverpoint data { bins zero = {0}; bins one = {1}; }
        cross data, valid;
    endgroup
endclass'''

    result = extract_covergroups(test_code)
    print("=== Covergroup ===")
    for name, cg in result.items():
        print(f"\n{name}:")
        for cp in cg.coverpoints:
            print(f"  coverpoint: {cp.name}")
        for cr in cg.cross:
            print(f"  cross: {cr}")
