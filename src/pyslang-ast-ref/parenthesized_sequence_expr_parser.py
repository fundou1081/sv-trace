"""
Parenthesized Sequence Expression Parser - 使用正确的 AST 遍历

提取括号序列表达式：
- ParenthesizedSequenceExpr

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ParenthesizedSequenceExpr:
    sequence: str = ""


class ParenthesizedSequenceExprExtractor:
    def __init__(self):
        self.expressions: List[ParenthesizedSequenceExpr] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ParenthesizedSequenceExpr':
                pse = ParenthesizedSequenceExpr()
                if hasattr(node, 'sequence') and node.sequence:
                    pse.sequence = str(node.sequence)[:50]
                elif hasattr(node, 'expr') and node.expr:
                    pse.sequence = str(node.expr)[:50]
                self.expressions.append(pse)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'seq': e.sequence[:40]} for e in self.expressions]


def extract_parenthesized_sequences(code: str) -> List[Dict]:
    return ParenthesizedSequenceExprExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
sequence s;
    (a ##1 b);
endsequence
'''
    result = extract_parenthesized_sequences(test_code)
    print(f"Parenthesized sequences: {len(result)}")
