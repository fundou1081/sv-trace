"""
Arithmetic Shift Parser - 使用正确的 AST 遍历

提取算术移位表达式：
- TripleLeftShift
- TripleRightShift
- ArithmeticLeftShiftAssignmentExpression
- ArithmeticRightShiftAssignmentExpression

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ArithmeticShiftExpr:
    operator: str = ""
    left: str = ""
    right: str = ""


class ArithmeticShiftExtractor:
    def __init__(self):
        self.expressions: List[ArithmeticShiftExpr] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['TripleLeftShift', 'TripleRightShift',
                           'ArithmeticLeftShiftAssignmentExpression',
                           'ArithmeticRightShiftAssignmentExpression']:
                ase = ArithmeticShiftExpr()
                if 'Left' in kind_name:
                    ase.operator = '<<<'
                else:
                    ase.operator = '>>>'
                
                if hasattr(node, 'left') and node.left:
                    ase.left = str(node.left)[:30]
                if hasattr(node, 'right') and node.right:
                    ase.right = str(node.right)[:30]
                
                self.expressions.append(ase)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'op': e.operator, 'left': e.left[:25], 'right': e.right[:25]} for e in self.expressions[:20]]


def extract_arithmetic_shifts(code: str) -> List[Dict]:
    return ArithmeticShiftExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
logic [31:0] a, b;
a = b >>> 5;
a = b <<< 3;
'''
    result = extract_arithmetic_shifts(test_code)
    print(f"Arithmetic shifts: {len(result)}")
