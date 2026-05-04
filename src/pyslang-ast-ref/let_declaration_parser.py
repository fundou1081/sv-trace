"""
Let Declaration Parser - 使用正确的 AST 遍历

提取 let 声明：
- LetKeyword

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class LetDeclaration:
    name: str = ""
    arguments: List[str] = None
    expression: str = ""
    
    def __post_init__(self):
        if self.arguments is None:
            self.arguments = []


class LetDeclarationExtractor:
    def __init__(self):
        self.declarations: List[LetDeclaration] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['LetDeclaration', 'LetKeyword']:
                ld = LetDeclaration()
                
                if hasattr(node, 'name') and node.name:
                    ld.name = str(node.name)
                
                args = []
                def get_args(n):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'Port' in kn or 'Argument' in kn:
                        args.append(str(n)[:20])
                    return pyslang.VisitAction.Advance
                node.visit(get_args)
                ld.arguments = args[:10]
                
                if hasattr(node, 'expression') and node.expression:
                    ld.expression = str(node.expression)[:40]
                
                self.declarations.append(ld)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': d.name, 'args': len(d.arguments), 'expr': d.expression[:35]} for d in self.declarations]


def extract_let_declarations(code: str) -> List[Dict]:
    return LetDeclarationExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
let sum(a, b) = a + b;
'''
    result = extract_let_declarations(test_code)
    print(f"Let declarations: {len(result)}")
