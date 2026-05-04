"""
Scoped Name Parser - 使用正确的 AST 遍历

提取作用域名称：
- ScopedName
- ClassName
- PackageImportItem

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
class ScopedName:
    full_name: str = ""
    parts: List[str] = ""


class ScopedNameExtractor:
    def __init__(self):
        self.names: List[ScopedName] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ScopedName':
                sn = ScopedName()
                sn.full_name = str(node)[:100]
                if hasattr(node, 'parts') and node.parts:
                    for p in node.parts:
                        sn.parts.append(str(p))
                self.names.append(sn)
            
            elif kind_name == 'ClassName':
                sn = ScopedName()
                sn.full_name = str(node)
                self.names.append(sn)
            
            elif kind_name == 'PackageImportItem':
                sn = ScopedName()
                if hasattr(node, 'package') and node.package:
                    sn.full_name = str(node.package) + '::'
                if hasattr(node, 'item') and node.item:
                    sn.full_name += str(node.item)
                self.names.append(sn)
            
            elif kind_name == 'PackageImportDeclaration':
                sn = ScopedName()
                sn.full_name = str(node)[:50]
                self.names.append(sn)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': n.full_name[:40]} for n in self.names[:20]]


def extract_scoped_names(code: str) -> List[Dict]:
    return ScopedNameExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
import pkg::item;
my_class::method();
pkg2::CONST;
'''
    result = extract_scoped_names(test_code)
    print(f"Scoped names: {len(result)}")
