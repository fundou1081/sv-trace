"""
Min Typ Max Expression Parser - 使用正确的 AST 遍历

提取 min:typ:max 表达式：
- MinTypMaxExpression

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class MinTypMaxExpr:
    min_val: str = ""
    typ_val: str = ""
    max_val: str = ""


class MinTypMaxExpressionExtractor:
    def __init__(self):
        self.expressions: List[MinTypMaxExpr] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'MinTypMaxExpression':
                mme = MinTypMaxExpr()
                
                if hasattr(node, 'min') and node.min:
                    mme.min_val = str(node.min)[:20]
                
                if hasattr(node, 'typ') and node.typ:
                    mme.typ_val = str(node.typ)[:20]
                
                if hasattr(node, 'max') and node.max:
                    mme.max_val = str(node.max)[:20]
                
                self.expressions.append(mme)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'min': e.min_val[:15], 'typ': e.typ_val[:15], 'max': e.max_val[:15]} for e in self.expressions]


def extract_min_typ_max(code: str) -> List[Dict]:
    return MinTypMaxExpressionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
parameter T = 1ns;
#(T/2) q = 1;
'''
    result = extract_min_typ_max(test_code)
    print(f"MinTypMax expressions: {len(result)}")
