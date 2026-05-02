"""
Package Parser - 使用正确的 AST 遍历

package 声明提取

注意：此文件不包含任何正则表达式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict
import pyslang
from pyslang import SyntaxKind


@dataclass
class PackageItem:
    name: str = ""
    item_type: str = ""


@dataclass
class PackageDef:
    name: str = ""
    items: List[PackageItem] = field(default_factory=list)


class PackageExtractor:
    """提取 package 声明"""
    
    def __init__(self):
        self.packages: List[PackageDef] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            # 只处理顶层的 PackageDeclaration
            if kind_name == 'PackageDeclaration':
                # 检查是否在根层级 (parent 可能不是另一个 package)
                pkg = PackageDef()
                if hasattr(node, 'name') and node.name:
                    pkg.name = str(node.name)
                
                # 提取内部项
                for child in node:
                    if not child:
                        continue
                    try:
                        child_kind = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
                    except:
                        continue
                    
                    if child_kind in ['FunctionDeclaration', 'TaskDeclaration', 
                                       'ClassDeclaration', 'ParameterDeclaration']:
                        item = PackageItem()
                        if hasattr(child, 'name') and child.name:
                            item.name = str(child.name)
                        item.item_type = child_kind
                        pkg.items.append(item)
                
                if pkg.name:
                    self.packages.append(pkg)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [
            {
                'name': p.name,
                'items': [{'name': i.name, 'type': i.item_type} for i in p.items]
            }
            for p in self.packages
        ]


def extract_packages(code: str) -> List[Dict]:
    return PackageExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
package my_pkg;
    function int add(int a, b);
        return a + b;
    endfunction
    
    class MyClass;
    endclass
endpackage
'''
    result = extract_packages(test_code)
    print(result)
