"""
Iff Event Clause Parser - 使用正确的 AST 遍历

提取 iff 事件子句：
- IffEventClause

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class IffEventClause:
    event: str = ""


class IffEventClauseExtractor:
    def __init__(self):
        self.clauses: List[IffEventClause] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'IffEventClause':
                iec = IffEventClause()
                if hasattr(node, 'event') and node.event:
                    iec.event = str(node.event)[:40]
                self.clauses.append(iec)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'event': c.event[:40]} for c in self.clauses]


def extract_iff_events(code: str) -> List[Dict]:
    return IffEventClauseExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
@event iff condition;
'''
    result = extract_iff_events(test_code)
    print(f"Iff event clauses: {len(result)}")
