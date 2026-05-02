"""
Implication Property Expression Parser - 使用正确的 AST 遍历

提取蕴含属性表达式：
- ImplicationPropertyExpr
- SequenceImplication

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ImplicationPropertyExpr:
    antecedent: str = ""
    consequent: str = ""


class ImplicationPropertyExprExtractor:
    def __init__(self):
        self.expressions: List[ImplicationPropertyExpr] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['ImplicationPropertyExpr', 'SequenceImplication', 'PropertyImplication']:
                ipe = ImplicationPropertyExpr()
                
                if hasattr(node, 'antecedent') and node.antecedent:
                    ipe.antecedent = str(node.antecedent)[:40]
                elif hasattr(node, 'left') and node.left:
                    ipe.antecedent = str(node.left)[:40]
                
                if hasattr(node, 'consequent') and node.consequent:
                    ipe.consequent = str(node.consequent)[:40]
                elif hasattr(node, 'right') and node.right:
                    ipe.consequent = str(node.right)[:40]
                
                self.expressions.append(ipe)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'antecedent': e.antecedent[:40], 'consequent': e.consequent[:40]} for e in self.expressions]


def extract_implications(code: str) -> List[Dict]:
    return ImplicationPropertyExprExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
property p;
    @(posedge clk) a |-> b;
endproperty
'''
    result = extract_implications(test_code)
    print(f"Implication expressions: {len(result)}")
