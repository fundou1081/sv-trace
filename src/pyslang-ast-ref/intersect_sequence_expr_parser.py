"""
Intersect Sequence Expression Parser - 使用正确的 AST 遍历

提取 intersect 序列表达式：
- IntersectSequenceExpr
- AndSequenceExpr
- OrSequenceExpr

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class SequenceBinaryExpr:
    operator: str = ""
    left: str = ""
    right: str = ""


class SequenceBinaryExprExtractor:
    def __init__(self):
        self.expressions: List[SequenceBinaryExpr] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['IntersectSequenceExpr', 'AndSequenceExpr', 'OrSequenceExpr',
                           'FirstMatchSequenceExpr', 'XorSequenceExpr']:
                sbe = SequenceBinaryExpr()
                sbe.operator = kind_name.replace('SequenceExpr', '').lower()
                
                if hasattr(node, 'left') and node.left:
                    sbe.left = str(node.left)[:40]
                if hasattr(node, 'right') and node.right:
                    sbe.right = str(node.right)[:40]
                
                self.expressions.append(sbe)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'op': e.operator, 'left': e.left[:30], 'right': e.right[:30]} for e in self.expressions]


def extract_sequence_binary(code: str) -> List[Dict]:
    return SequenceBinaryExprExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
sequence s;
    a intersect b;
    c and d;
endsequence
'''
    result = extract_sequence_binary(test_code)
    print(f"Sequence binary expressions: {len(result)}")
