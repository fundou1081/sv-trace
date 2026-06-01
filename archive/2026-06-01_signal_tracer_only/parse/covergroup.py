"""
Covergroup Parser - 使用正确的 AST 遍历

覆盖组提取

注意：此文件使用正确的 AST 属性访问，不包含正则表达式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import pyslang
from pyslang import SyntaxKind


@dataclass
class Coverpoint:
    name: str = ""
    type: str = ""  # int, bit, etc.
    bins: List[str] = field(default_factory=list)


@dataclass
class CoverCross:
    name: str = ""
    referenced_points: List[str] = field(default_factory=list)


@dataclass
class CovergroupDeclaration:
    name: str = ""
    coverpoints: List[Coverpoint] = field(default_factory=list)
    covercrosses: List[CoverCross] = field(default_factory=list)


class CovergroupExtractor:
    """提取覆盖组 - 使用正确的 AST 遍历"""
    
    def __init__(self):
        self.covergroups: List[CovergroupDeclaration] = []
    
    def _extract_from_tree(self, root):
        """使用 AST 遍历"""
        self.covergroups = []
        
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'CovergroupDeclaration':
                cg = self._extract_covergroup(node)
                if cg:
                    self.covergroups.append(cg)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
        return self.covergroups
    
    def _extract_covergroup(self, node) -> Optional[CovergroupDeclaration]:
        """提取覆盖组 - 使用 AST 属性"""
        cg = CovergroupDeclaration()
        
        # 名称
        if hasattr(node, 'name') and node.name:
            cg.name = str(node.name)
        
        # 遍历子节点查找 coverpoint 和 covercross
        for child in node:
            if not child:
                continue
            
            try:
                child_kind = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            except:
                continue
            
            # CoverpointSymbol
            if child_kind == 'CoverpointSymbol':
                cp = self._extract_coverpoint(child)
                if cp:
                    cg.coverpoints.append(cp)
            
            # CoverCrossSymbol
            elif child_kind == 'CoverCrossSymbol':
                cc = self._extract_covercross(child)
                if cc:
                    cg.covercrosses.append(cc)
        
        return cg if cg.name or cg.coverpoints or cg.covercrosses else None
    
    def _extract_coverpoint(self, node) -> Optional[Coverpoint]:
        """提取 coverpoint"""
        cp = Coverpoint()
        
        if hasattr(node, 'name') and node.name:
            cp.name = str(node.name)
        elif hasattr(node, 'identifier') and node.identifier:
            cp.name = str(node.identifier)
        
        # 类型
        if hasattr(node, 'type') and node.type:
            cp.type = str(node.type)
        
        return cp if cp.name else None
    
    def _extract_covercross(self, node) -> Optional[CoverCross]:
        """提取 covercross"""
        cc = CoverCross()
        
        if hasattr(node, 'name') and node.name:
            cc.name = str(node.name)
        
        return cc if cc.name else None
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        """提取"""
        tree = pyslang.SyntaxTree.fromText(code, source)
        cgs = self._extract_from_tree(tree.root)
        
        return [
            {
                'name': cg.name,
                'coverpoints': len(cg.coverpoints),
                'covercrosses': len(cg.covercrosses),
                'point_names': [cp.name for cp in cg.coverpoints]
            }
            for cg in cgs
        ]


# ============================================================================
# 便捷函数
# ============================================================================

def extract_covergroups(code: str) -> List[Dict]:
    """提取覆盖组"""
    extractor = CovergroupExtractor()
    return extractor.extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
module test;
    covergroup cg1 with function sample(bit [7:0] data);
        option.per_instance = 1;
        cp_data: coverpoint data {
            bins low = {[0:31]};
            bins high = {[32:255]};
        }
    endgroup
    
    covergroup cg2;
        cross a, b {
            bins a1b1 = a[0] && b[0];
        }
    endgroup
endmodule
'''
    
    print("=== Covergroup Extraction ===\n")
    
    result = extract_covergroups(test_code)
    
    print(f"Found {len(result)} covergroups:")
    for r in result:
        print(f"  {r['name']}: {r['coverpoints']} points, {r['covercrosses']} crosses")
        if r['point_names']:
            print(f"    points: {r['point_names']}")
