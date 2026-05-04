"""
String Literal Expression Parser - 使用正确的 AST 遍历

提取字符串字面量表达式：
- StringLiteralExpression

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class StringLiteralExpression:
    value: str = ""


class StringLiteralExpressionExtractor:
    def __init__(self):
        self.expressions: List[StringLiteralExpression] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'StringLiteralExpression':
                sle = StringLiteralExpression()
                if hasattr(node, 'value') and node.value:
                    sle.value = str(node.value)[:100]
                elif hasattr(node, 'literal') and node.literal:
                    sle.value = str(node.literal)[:100]
                self.expressions.append(sle)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'value': e.value[:50]} for e in self.expressions[:20]]


def extract_string_literals(code: str) -> List[Dict]:
    return StringLiteralExpressionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
string s = "Hello, World!";
'''
    result = extract_string_literals(test_code)
    print(f"String literals: {len(result)}")
