"""
New Array Expression Parser - 使用正确的 AST 遍历

提取动态数组表达式：
- NewArrayExpression

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class NewArrayExpression:
    size: str = ""
    init_values: str = ""


class NewArrayExpressionExtractor:
    def __init__(self):
        self.expressions: List[NewArrayExpression] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'NewArrayExpression':
                nae = NewArrayExpression()
                
                if hasattr(node, 'size') and node.size:
                    nae.size = str(node.size)
                
                if hasattr(node, 'init') and node.init:
                    nae.init_values = str(node.init)[:30]
                
                self.expressions.append(nae)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'size': e.size[:20], 'init': e.init_values[:30]} for e in self.expressions]


def extract_new_arrays(code: str) -> List[Dict]:
    return NewArrayExpressionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
int arr[];
arr = new[10];
'''
    result = extract_new_arrays(test_code)
    print(f"New array expressions: {len(result)}")
