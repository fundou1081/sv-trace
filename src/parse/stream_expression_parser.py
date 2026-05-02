"""
Stream Expression Parser - 使用正确的 AST 遍历

提取流表达式：
- StreamExpression
- StreamExpressionWithRange

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class StreamExpression:
    expression: str = ""
    slice_size: str = ""


class StreamExpressionExtractor:
    def __init__(self):
        self.expressions: List[StreamExpression] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['StreamExpression', 'StreamExpressionWithRange',
                           'StreamingConcatenationExpression']:
                se = StreamExpression()
                
                if hasattr(node, 'expression') and node.expression:
                    se.expression = str(node.expression)[:40]
                
                if hasattr(node, 'sliceSize') and node.sliceSize:
                    se.slice_size = str(node.sliceSize)[:20]
                
                self.expressions.append(se)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'expr': e.expression[:35], 'size': e.slice_size[:15]} for e in self.expressions[:20]]


def extract_stream_expressions(code: str) -> List[Dict]:
    return StreamExpressionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
bit [7:0] a, b;
a = {>>{b}};
'''
    result = extract_stream_expressions(test_code)
    print(f"Stream expressions: {len(result)}")
