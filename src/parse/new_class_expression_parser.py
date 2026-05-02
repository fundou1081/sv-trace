"""
New Class Expression Parser - 使用正确的 AST 遍历

提取类实例化：
- NewClassExpression
- ConstructorName

注意：此文件不包含任何正则表达式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang
from pyslang import SyntaxKind


@dataclass
class NewClassExpr:
    class_name: str = ""
    arguments: str = ""


class NewClassExpressionExtractor:
    def __init__(self):
        self.expressions: List[NewClassExpr] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'NewClassExpression':
                nce = NewClassExpr()
                if hasattr(node, 'classType') and node.classType:
                    nce.class_name = str(node.classType)[:50]
                if hasattr(node, 'arguments') and node.arguments:
                    nce.arguments = str(node.arguments)
                self.expressions.append(nce)
            
            elif kind_name == 'ConstructorName':
                nce = NewClassExpr()
                nce.class_name = str(node)
                self.expressions.append(nce)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [
            {'class': e.class_name[:40], 'args': e.arguments[:30]}
            for e in self.expressions
        ]


def extract_new_class(code: str) -> List[Dict]:
    return NewClassExpressionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
MyClass obj = new();
MyClass obj2 = new(arg1, arg2);
'''
    result = extract_new_class(test_code)
    print(f"New class expressions: {len(result)}")
