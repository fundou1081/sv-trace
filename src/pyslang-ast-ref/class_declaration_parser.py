"""
Class Declaration Parser - 使用正确的 AST 遍历

提取类声明：
- ClassDeclaration

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ClassDeclaration:
    name: str = ""
    extends: str = ""
    implements: List[str] = None
    
    def __post_init__(self):
        if self.implements is None:
            self.implements = []


class ClassDeclarationExtractor:
    def __init__(self):
        self.classes: List[ClassDeclaration] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ClassDeclaration':
                cd = ClassDeclaration()
                if hasattr(node, 'name') and node.name:
                    cd.name = str(node.name)
                if hasattr(node, 'extends') and node.extends:
                    cd.extends = str(node.extends)[:30]
                self.classes.append(cd)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': c.name, 'extends': c.extends[:30]} for c in self.classes]


def extract_class_declarations(code: str) -> List[Dict]:
    return ClassDeclarationExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
class my_class extends base_class;
endclass
'''
    result = extract_class_declarations(test_code)
    print(f"Class declarations: {len(result)}")
