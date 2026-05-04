"""
Intersect Keyword Parser - 使用正确的 AST 遍历

提取 intersect/solve/before 关键字：
- IntersectKeyword
- SolveKeyword
- BeforeKeyword

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ConstraintOperator:
    keyword: str = ""


class ConstraintOperatorExtractor:
    def __init__(self):
        self.keywords: List[ConstraintOperator] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['IntersectKeyword', 'SolveKeyword', 'BeforeKeyword']:
                co = ConstraintOperator()
                co.keyword = kind_name.replace('Keyword', '').lower()
                self.keywords.append(co)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'keyword': k.keyword} for k in self.keywords]


def extract_constraint_operators(code: str) -> List[Dict]:
    return ConstraintOperatorExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
constraint c { solve a before b; }
'''
    result = extract_constraint_operators(test_code)
    print(f"Constraint operators: {len(result)}")
