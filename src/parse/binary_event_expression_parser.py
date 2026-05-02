"""
Binary Event Expression Parser - 使用正确的 AST 遍历

提取二元事件表达式：
- BinaryEventExpression
- BinaryOrExpression

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class BinaryEventExpr:
    operator: str = ""
    left: str = ""
    right: str = ""


class BinaryEventExpressionExtractor:
    def __init__(self):
        self.expressions: List[BinaryEventExpr] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['BinaryEventExpression', 'BinaryOrExpression', 'OrExpression']:
                bee = BinaryEventExpr()
                if kind_name == 'BinaryEventExpression':
                    bee.operator = 'or'
                else:
                    bee.operator = '||'
                
                if hasattr(node, 'left') and node.left:
                    bee.left = str(node.left)[:30]
                if hasattr(node, 'right') and node.right:
                    bee.right = str(node.right)[:30]
                
                self.expressions.append(bee)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'op': e.operator, 'left': e.left[:25], 'right': e.right[:25]} for e in self.expressions[:20]]


def extract_binary_events(code: str) -> List[Dict]:
    return BinaryEventExpressionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
sequence s;
    a or b;
endsequence
'''
    result = extract_binary_events(test_code)
    print(f"Binary event expressions: {len(result)}")
