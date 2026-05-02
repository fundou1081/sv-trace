"""
Equals Value Clause V2 Parser - 使用正确的 AST 遍历

提取 = 值 子句：
- EqualsValueClause

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class EqualsValueClause:
    name: str = ""
    value: str = ""


class EqualsValueClauseExtractor:
    def __init__(self):
        self.clauses: List[EqualsValueClause] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'EqualsValueClause':
                evc = EqualsValueClause()
                if hasattr(node, 'name') and node.name:
                    evc.name = str(node.name)
                if hasattr(node, 'value') and node.value:
                    evc.value = str(node.value)
                self.clauses.append(evc)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': c.name[:30], 'value': c.value[:30]} for c in self.clauses[:50]]


def extract_equals_value_clauses(code: str) -> List[Dict]:
    return EqualsValueClauseExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
logic [7:0] sig = 8'h0;
'''
    result = extract_equals_value_clauses(test_code)
    print(f"Equals value clauses: {len(result)}")
