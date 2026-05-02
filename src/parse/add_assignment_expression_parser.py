"""
Add Assignment Expression Parser - 使用正确的 AST 遍历

提取复合赋值表达式 (+=, -= 等)：
- AddAssignmentExpression
- SubtractAssignmentExpression
- MultiplyAssignmentExpression

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class AddAssignmentExpr:
    operator: str = ""
    target: str = ""
    value: str = ""


class AddAssignmentExpressionExtractor:
    def __init__(self):
        self.expressions: List[AddAssignmentExpr] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['AddAssignmentExpression', 'SubtractAssignmentExpression',
                           'MultiplyAssignmentExpression', 'DivideAssignmentExpression',
                           'ModuloAssignmentExpression']:
                ae = AddAssignmentExpr()
                ae.operator = kind_name.replace('AssignmentExpression', '').replace('Multiply', '*').replace('Divide', '/').replace('Modulo', '%')
                
                if hasattr(node, 'left') and node.left:
                    ae.target = str(node.left)[:30]
                if hasattr(node, 'right') and node.right:
                    ae.value = str(node.right)[:30]
                
                self.expressions.append(ae)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'op': e.operator, 'target': e.target[:20], 'value': e.value[:20]} for e in self.expressions[:20]]


def extract_add_assignments(code: str) -> List[Dict]:
    return AddAssignmentExpressionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
a += 1;
b -= 2;
'''
    result = extract_add_assignments(test_code)
    print(f"Add assignments: {len(result)}")
