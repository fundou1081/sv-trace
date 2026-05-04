"""
Shift Expression Parser - 使用正确的 AST 遍历

提取移位表达式：
- LeftShiftExpression
- RightShiftExpression

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ShiftExpression:
    operator: str = ""
    left: str = ""
    right: str = ""


class ShiftExpressionExtractor:
    def __init__(self):
        self.expressions: List[ShiftExpression] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['LeftShiftExpression', 'RightShiftExpression', 'LeftShift', 'RightShift',
                           'ArithmeticShiftLeftExpression', 'ArithmeticShiftRightExpression']:
                se = ShiftExpression()
                if 'Left' in kind_name:
                    se.operator = '<<'
                else:
                    se.operator = '>>'
                
                if hasattr(node, 'left') and node.left:
                    se.left = str(node.left)[:30]
                if hasattr(node, 'right') and node.right:
                    se.right = str(node.right)[:30]
                
                self.expressions.append(se)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'op': e.operator, 'left': e.left[:25], 'right': e.right[:25]} for e in self.expressions[:20]]


def extract_shift_expressions(code: str) -> List[Dict]:
    return ShiftExpressionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
logic [7:0] a;
a = b << 2;
a = c >> 1;
'''
    result = extract_shift_expressions(test_code)
    print(f"Shift expressions: {len(result)}")
