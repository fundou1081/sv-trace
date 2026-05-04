"""
Unary Bitwise OR Expression Parser - 使用正确的 AST 遍历

提取一元按位或表达式：
- UnaryBitwiseOrExpression

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class UnaryBitwiseOrExpr:
    operand: str = ""


class UnaryBitwiseOrExtractor:
    def __init__(self):
        self.expressions: List[UnaryBitwiseOrExpr] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'UnaryBitwiseOrExpression':
                uboe = UnaryBitwiseOrExpr()
                if hasattr(node, 'operand') and node.operand:
                    uboe.operand = str(node.operand)[:30]
                self.expressions.append(uboe)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'operand': e.operand[:30]} for e in self.expressions[:20]]


def extract_unary_bitwise_or(code: str) -> List[Dict]:
    return UnaryBitwiseOrExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
|a
'''
    result = extract_unary_bitwise_or(test_code)
    print(f"Unary bitwise or: {len(result)}")
