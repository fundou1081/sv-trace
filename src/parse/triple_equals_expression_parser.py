"""
Triple Equals Expression Parser - 使用正确的 AST 遍历

提取 === 操作符：
- TripleEquals

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class TripleEqualsExpr:
    left: str = ""
    right: str = ""


class TripleEqualsExtractor:
    def __init__(self):
        self.expressions: List[TripleEqualsExpr] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['TripleEquals', 'CaseIdentityExpression']:
                tee = TripleEqualsExpr()
                if hasattr(node, 'left') and node.left:
                    tee.left = str(node.left)[:25]
                if hasattr(node, 'right') and node.right:
                    tee.right = str(node.right)[:25]
                self.expressions.append(tee)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'left': e.left[:25], 'right': e.right[:25]} for e in self.expressions[:20]]


def extract_triple_equals(code: str) -> List[Dict]:
    return TripleEqualsExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
if (a === b) begin end
'''
    result = extract_triple_equals(test_code)
    print(f"Triple equals: {len(result)}")
