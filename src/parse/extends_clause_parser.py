"""
Extends Clause Parser - 使用正确的 AST 遍历

提取类继承信息：
- ExtendsClause
- ClassExtension

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
class ExtendsInfo:
    base_class: str = ""
    arguments: str = ""


class ExtendsClauseExtractor:
    def __init__(self):
        self.extends: List[ExtendsInfo] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['ExtendsClause', 'ClassExtension']:
                ei = ExtendsInfo()
                if hasattr(node, 'classType') and node.classType:
                    ei.base_class = str(node.classType)
                if hasattr(node, 'arguments') and node.arguments:
                    ei.arguments = str(node.arguments)
                self.extends.append(ei)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'base_class': e.base_class, 'args': e.arguments[:30]} for e in self.extends]


def extract_extends(code: str) -> List[Dict]:
    return ExtendsClauseExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
class MyChild extends MyParent;
endclass
'''
    result = extract_extends(test_code)
    print(f"Extends clauses: {len(result)}")
