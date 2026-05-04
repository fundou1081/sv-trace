"""
For Variable Declaration Parser - 使用正确的 AST 遍历

提取 for 循环变量声明：
- ForVariableDeclaration

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ForVariableDeclaration:
    name: str = ""
    data_type: str = ""
    value: str = ""


class ForVariableDeclarationExtractor:
    def __init__(self):
        self.declarations: List[ForVariableDeclaration] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ForVariableDeclaration':
                fvd = ForVariableDeclaration()
                
                if hasattr(node, 'name') and node.name:
                    fvd.name = str(node.name)
                
                if hasattr(node, 'dataType') and node.dataType:
                    fvd.data_type = str(node.dataType)[:20]
                
                if hasattr(node, 'value') and node.value:
                    fvd.value = str(node.value)[:20]
                
                self.declarations.append(fvd)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': d.name, 'type': d.data_type[:15], 'value': d.value[:15]} for d in self.declarations]


def extract_for_var_decls(code: str) -> List[Dict]:
    return ForVariableDeclarationExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
for (int i = 0; i < 10; i++) begin end
'''
    result = extract_for_var_decls(test_code)
    print(f"For variable declarations: {len(result)}")
