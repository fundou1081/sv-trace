"""
Local Variable Declaration Parser - 使用正确的 AST 遍历

提取局部变量声明：
- LocalVariableDeclaration

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class LocalVariableDeclaration:
    data_type: str = ""
    names: List[str] = None
    
    def __post_init__(self):
        if self.names is None:
            self.names = []


class LocalVariableDeclarationExtractor:
    def __init__(self):
        self.declarations: List[LocalVariableDeclaration] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'LocalVariableDeclaration':
                lvd = LocalVariableDeclaration()
                
                if hasattr(node, 'dataType') and node.dataType:
                    lvd.data_type = str(node.dataType)[:30]
                
                names = []
                def get_names(n):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'Declarator' in kn or 'Identifier' in kn:
                        names.append(str(n))
                    return pyslang.VisitAction.Advance
                node.visit(get_names)
                lvd.names = names[:10]
                
                self.declarations.append(lvd)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'type': d.data_type[:25], 'names': d.names[:5]} for d in self.declarations]


def extract_local_vars(code: str) -> List[Dict]:
    return LocalVariableDeclarationExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
let x = 5;
'''
    result = extract_local_vars(test_code)
    print(f"Local variable declarations: {len(result)}")
