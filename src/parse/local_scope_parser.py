"""
Local Scope Parser - 使用正确的 AST 遍历

提取局部作用域：
- LocalScope

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class LocalScope:
    name: str = ""


class LocalScopeExtractor:
    def __init__(self):
        self.scopes: List[LocalScope] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'LocalScope':
                ls = LocalScope()
                if hasattr(node, 'name') and node.name:
                    ls.name = str(node.name)
                self.scopes.append(ls)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': s.name[:30]} for s in self.scopes]


def extract_local_scopes(code: str) -> List[Dict]:
    return LocalScopeExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
local::var;
'''
    result = extract_local_scopes(test_code)
    print(f"Local scopes: {len(result)}")
