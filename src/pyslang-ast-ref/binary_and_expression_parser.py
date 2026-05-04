"""
Binary AND Expression Parser - 使用正确的 AST 遍历

提取按位与表达式：
- BinaryAndExpression
- And

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class BinaryAndExpr:
    left: str = ""
    right: str = ""


class BinaryAndExpressionExtractor:
    def __init__(self):
        self.expressions: List[BinaryAndExpr] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['BinaryAndExpression', 'BitwiseAndExpression']:
                bae = BinaryAndExpr()
                if hasattr(node, 'left') and node.left:
                    bae.left = str(node.left)[:30]
                if hasattr(node, 'right') and node.right:
                    bae.right = str(node.right)[:30]
                self.expressions.append(bae)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'left': e.left[:25], 'right': e.right[:25]} for e in self.expressions[:20]]


def extract_bitwise_and(code: str) -> List[Dict]:
    return BinaryAndExpressionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
logic [7:0] a, b, c;
assign c = a & b;
'''
    result = extract_bitwise_and(test_code)
    print(f"Binary AND expressions: {len(result)}")
