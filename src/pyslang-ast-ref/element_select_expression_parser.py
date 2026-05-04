"""
Element Select Expression Parser - 使用正确的 AST 遍历

提取元素选择表达式：
- ElementSelectExpression

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ElementSelectExpr:
    name: str = ""
    index: str = ""


class ElementSelectExpressionExtractor:
    def __init__(self):
        self.expressions: List[ElementSelectExpr] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ElementSelectExpression':
                ese = ElementSelectExpr()
                if hasattr(node, 'name') and node.name:
                    ese.name = str(node.name)[:30]
                if hasattr(node, 'select') and node.select:
                    ese.index = str(node.select)[:20]
                self.expressions.append(ese)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': e.name[:25], 'index': e.index[:15]} for e in self.expressions[:20]]


def extract_element_selects(code: str) -> List[Dict]:
    return ElementSelectExpressionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
logic [7:0] arr;
assign x = arr[3];
'''
    result = extract_element_selects(test_code)
    print(f"Element select expressions: {len(result)}")
