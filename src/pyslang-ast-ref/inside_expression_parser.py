"""
Inside Expression Parser - 使用正确的 AST 遍历

提取 inside 表达式：
- InsideExpression

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class InsideExpression:
    expression: str = ""
    ranges: List[str] = None
    
    def __post_init__(self):
        if self.ranges is None:
            self.ranges = []


class InsideExpressionExtractor:
    def __init__(self):
        self.expressions: List[InsideExpression] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'InsideExpression':
                ie = InsideExpression()
                
                if hasattr(node, 'expression') and node.expression:
                    ie.expression = str(node.expression)[:30]
                
                ranges = []
                def get_ranges(n):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'Range' in kn or 'Set' in kn:
                        ranges.append(str(n)[:30])
                    return pyslang.VisitAction.Advance
                node.visit(get_ranges)
                ie.ranges = ranges[:10]
                
                self.expressions.append(ie)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'expr': e.expression[:25], 'ranges': len(e.ranges)} for e in self.expressions[:20]]


def extract_inside_expressions(code: str) -> List[Dict]:
    return InsideExpressionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
if (a inside {[0:10], [20:30]}) begin end
'''
    result = extract_inside_expressions(test_code)
    print(f"Inside expressions: {len(result)}")
