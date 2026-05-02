"""
Time Literal Expression Parser - 使用正确的 AST 遍历

提取时间字面量表达式：
- TimeLiteralExpression

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class TimeLiteralExpression:
    value: str = ""
    unit: str = ""


class TimeLiteralExpressionExtractor:
    def __init__(self):
        self.expressions: List[TimeLiteralExpression] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'TimeLiteralExpression':
                tle = TimeLiteralExpression()
                
                if hasattr(node, 'literal') and node.literal:
                    lit = str(node.literal)
                    tle.value = lit
                    tle.unit = lit[-1] if lit[-1] in ['s', 'm', 'u', 'n', 'p', 'f'] else ''
                
                self.expressions.append(tle)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'value': e.value[:15], 'unit': e.unit} for e in self.expressions]


def extract_time_literals(code: str) -> List[Dict]:
    return TimeLiteralExpressionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
#10ns;
#100us;
'''
    result = extract_time_literals(test_code)
    print(f"Time literals: {len(result)}")
