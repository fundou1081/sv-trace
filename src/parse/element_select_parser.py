"""
Element Select Parser - 使用正确的 AST 遍历

提取元素选择表达式：
- ElementSelect
- BitSelect

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
class ElementSelect:
    name: str = ""
    index: str = ""


class ElementSelectExtractor:
    def __init__(self):
        self.selects: List[ElementSelect] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['ElementSelect', 'BitSelect', 'ArraySelect']:
                es = ElementSelect()
                if hasattr(node, 'name') and node.name:
                    es.name = str(node.name)
                if hasattr(node, 'index') and node.index:
                    es.index = str(node.index)
                elif hasattr(node, 'select') and node.select:
                    es.index = str(node.select)
                self.selects.append(es)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': s.name[:20], 'index': s.index[:20]} for s in self.selects[:20]]


def extract_element_selects(code: str) -> List[Dict]:
    return ElementSelectExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
logic [7:0] arr;
assign x = arr[3];
'''
    result = extract_element_selects(test_code)
    print(f"Element selects: {len(result)}")
