"""
Compilation Unit Parser - 使用正确的 AST 遍历

提取编译单元：
- CompilationUnit

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class CompilationUnit:
    modules: int = 0
    interfaces: int = 0
    classes: int = 0
    packages: int = 0


class CompilationUnitExtractor:
    def __init__(self):
        self.units: List[CompilationUnit] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'CompilationUnit':
                cu = CompilationUnit()
                
                mods, ints, clss, pkgs = 0, 0, 0, 0
                def count_items(n, m=[0], i=[0], c=[0], p=[0]):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'ModuleDeclaration' in kn: m[0] += 1
                    elif 'InterfaceDeclaration' in kn: i[0] += 1
                    elif 'ClassDeclaration' in kn: c[0] += 1
                    elif 'PackageDeclaration' in kn: p[0] += 1
                    return pyslang.VisitAction.Advance
                node.visit(count_items)
                
                cu.modules = mods
                cu.interfaces = ints
                cu.classes = clss
                cu.packages = pkgs
                
                self.units.append(cu)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'modules': u.modules, 'interfaces': u.interfaces, 'classes': u.classes} for u in self.units]


def extract_compilation_units(code: str) -> List[Dict]:
    return CompilationUnitExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
module top;
endmodule
'''
    result = extract_compilation_units(test_code)
    print(f"Compilation units: {len(result)}")
