"""
Class Method Prototype Parser - 使用正确的 AST 遍历

提取类方法原型：
- ClassMethodPrototype

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
class ClassMethodPrototype:
    name: str = ""
    return_type: str = ""


class ClassMethodPrototypeExtractor:
    def __init__(self):
        self.prototypes: List[ClassMethodPrototype] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ClassMethodPrototype':
                cmp = ClassMethodPrototype()
                if hasattr(node, 'name') and node.name:
                    cmp.name = str(node.name)
                if hasattr(node, 'returnType') and node.returnType:
                    cmp.return_type = str(node.returnType)[:30]
                self.prototypes.append(cmp)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': p.name, 'return': p.return_type[:20]} for p in self.prototypes]


def extract_class_method_prototypes(code: str) -> List[Dict]:
    return ClassMethodPrototypeExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
class MyClass;
    extern function void my_method();
endclass
'''
    result = extract_class_method_prototypes(test_code)
    print(f"Class method prototypes: {len(result)}")
