"""
DPI Parser - 使用正确的 AST 遍历

DPI import/export 提取

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
class DPIImport:
    name: str = ""
    return_type: str = ""


@dataclass
class DPIExport:
    name: str = ""
    return_type: str = ""


class DPIExtractor:
    """提取 DPI 声明"""
    
    def __init__(self):
        self.imports: List[DPIImport] = []
        self.exports: List[DPIExport] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'DPIImport':
                dpi = DPIImport()
                if hasattr(node, 'name') and node.name:
                    dpi.name = str(node.name)
                if hasattr(node, 'returnType') and node.returnType:
                    dpi.return_type = str(node.returnType)
                self.imports.append(dpi)
            
            elif kind_name == 'DPIExport':
                dpi = DPIExport()
                if hasattr(node, 'name') and node.name:
                    dpi.name = str(node.name)
                self.exports.append(dpi)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> Dict:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return {
            'imports': [{'name': i.name, 'return': i.return_type} for i in self.imports],
            'exports': [{'name': e.name} for e in self.exports]
        }


def extract_dpi(code: str) -> Dict:
    return DPIExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
import "DPI" function int my_func(input int a);
export "DPI" function my_c_func;
'''
    result = extract_dpi(test_code)
    print(result)
