"""
Package Header Parser - 使用正确的 AST 遍历

提取包头：
- PackageHeader

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class PackageHeader:
    name: str = ""
    imports: List[str] = None
    
    def __post_init__(self):
        if self.imports is None:
            self.imports = []


class PackageHeaderExtractor:
    def __init__(self):
        self.headers: List[PackageHeader] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'PackageHeader':
                ph = PackageHeader()
                
                if hasattr(node, 'name') and node.name:
                    ph.name = str(node.name)
                
                imports = []
                def get_imports(n):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'Import' in kn:
                        imports.append(str(n)[:30])
                    return pyslang.VisitAction.Advance
                node.visit(get_imports)
                ph.imports = imports[:10]
                
                self.headers.append(ph)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': h.name, 'imports': len(h.imports)} for h in self.headers]


def extract_package_headers(code: str) -> List[Dict]:
    return PackageHeaderExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
package my_pkg;
endpackage
'''
    result = extract_package_headers(test_code)
    print(f"Package headers: {len(result)}")
