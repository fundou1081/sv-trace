"""
Matches Clause Parser - 使用正确的 AST 遍历

提取 matches 子句：
- MatchesClause

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class MatchesClause:
    pattern: str = ""
    guard: str = ""


class MatchesClauseExtractor:
    def __init__(self):
        self.clauses: List[MatchesClause] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'MatchesClause':
                mc = MatchesClause()
                if hasattr(node, 'pattern') and node.pattern:
                    mc.pattern = str(node.pattern)[:40]
                if hasattr(node, 'guard') and node.guard:
                    mc.guard = str(node.guard)[:30]
                self.clauses.append(mc)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'pattern': c.pattern[:35], 'guard': c.guard[:25]} for c in self.clauses]


def extract_matches_clauses(code: str) -> List[Dict]:
    return MatchesClauseExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
expect (foo) matches { dist [1:=1] };
'''
    result = extract_matches_clauses(test_code)
    print(f"Matches clauses: {len(result)}")
