"""
Streaming Concatenation Parser - 使用正确的 AST 遍历

提取流连接表达式：
- StreamingConcatenationExpression
- StreamExpression

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class StreamingConcatenation:
    direction: str = ""  # left or right
    expressions: List[str] = None
    
    def __post_init__(self):
        if self.expressions is None:
            self.expressions = []


class StreamingConcatenationExtractor:
    def __init__(self):
        self.expressions: List[StreamingConcatenation] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['StreamingConcatenationExpression', 'StreamExpression']:
                sc = StreamingConcatenation()
                
                if hasattr(node, 'direction') and node.direction:
                    sc.direction = str(node.direction).lower()
                
                exprs = []
                def get_exprs(n):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'Expression' in kn:
                        exprs.append(str(n)[:20])
                    return pyslang.VisitAction.Advance
                node.visit(get_exprs)
                sc.expressions = exprs[:10]
                
                self.expressions.append(sc)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'dir': s.direction, 'count': len(s.expressions)} for s in self.expressions[:20]]


def extract_streaming_concat(code: str) -> List[Dict]:
    return StreamingConcatenationExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
bit [7:0] a, b;
a = {>>{b}};
'''
    result = extract_streaming_concat(test_code)
    print(f"Streaming concatenations: {len(result)}")
