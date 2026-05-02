"""
Tagged Union Expression Parser - 使用正确的 AST 遍历

提取标签联合表达式：
- TaggedUnionExpression

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class TaggedUnionExpression:
    member: str = ""
    expression: str = ""


class TaggedUnionExpressionExtractor:
    def __init__(self):
        self.expressions: List[TaggedUnionExpression] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'TaggedUnionExpression':
                tue = TaggedUnionExpression()
                
                if hasattr(node, 'member') and node.member:
                    tue.member = str(node.member)
                
                if hasattr(node, 'expression') and node.expression:
                    tue.expression = str(node.expression)[:30]
                
                self.expressions.append(tue)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'member': t.member[:25], 'expr': t.expression[:25]} for t in self.expressions]


def extract_tagged_unions(code: str) -> List[Dict]:
    return TaggedUnionExpressionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
tagged member expr;
'''
    result = extract_tagged_unions(test_code)
    print(f"Tagged unions: {len(result)}")
