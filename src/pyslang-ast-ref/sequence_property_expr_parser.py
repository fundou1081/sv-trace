"""
Sequence/Property Expression Parser - 使用正确的 AST 遍历

提取序列和属性表达式：
- SimpleSequenceExpr
- SimplePropertyExpr
- SequenceExpression
- PropertyExpression

注意：此文件不包含任何正则表达式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang
from pyslang import SyntaxKind


@dataclass
class SequenceExpr:
    expr_type: str = ""
    operators: List[str] = field(default_factory=list)


class SequencePropertyExprExtractor:
    def __init__(self):
        self.sequences: List[SequenceExpr] = []
        self.properties: List[SequenceExpr] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'SimpleSequenceExpr':
                se = SequenceExpr()
                se.expr_type = 'simple_sequence'
                if hasattr(node, 'left') and node.left:
                    se.operators.append('left:' + str(node.left)[:20])
                self.sequences.append(se)
            
            elif kind_name == 'SimplePropertyExpr':
                pe = SequenceExpr()
                pe.expr_type = 'simple_property'
                if hasattr(node, 'expression') and node.expression:
                    pe.operators.append(str(node.expression)[:30])
                self.properties.append(pe)
            
            elif kind_name == 'SequenceExpr':
                se = SequenceExpr()
                se.expr_type = 'sequence'
                if hasattr(node, 'left') and node.left:
                    se.operators.append(str(node.left)[:30])
                self.sequences.append(se)
            
            elif kind_name == 'PropertyExpr':
                pe = SequenceExpr()
                pe.expr_type = 'property'
                self.properties.append(pe)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> Dict:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return {
            'sequences': len(self.sequences),
            'properties': len(self.properties)
        }


def extract_sequence_property_expr(code: str) -> Dict:
    return SequencePropertyExprExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
sequence s1;
    a ##1 b ##2 c;
endsequence

property p1;
    always @ (posedge clk) a |-> b;
endproperty
'''
    result = extract_sequence_property_expr(test_code)
    print(f"Sequences: {result['sequences']}, Properties: {result['properties']}")
