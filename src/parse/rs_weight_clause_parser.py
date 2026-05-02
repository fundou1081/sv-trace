"""
RS Weight Clause Parser - 使用正确的 AST 遍历

提取随机约束权重子句：
- RsWeightClause
- RandJoinClause

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class RsWeightClause:
    weight: str = ""


class RsWeightClauseExtractor:
    def __init__(self):
        self.clauses: List[RsWeightClause] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['RsWeightClause', 'RandJoinClause', 'RsRepeat']:
                rwc = RsWeightClause()
                if hasattr(node, 'weight') and node.weight:
                    rwc.weight = str(node.weight)[:20]
                self.clauses.append(rwc)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'weight': c.weight[:20]} for c in self.clauses]


def extract_rs_weight_clauses(code: str) -> List[Dict]:
    return RsWeightClauseExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
randjoin;
'''
    result = extract_rs_weight_clauses(test_code)
    print(f"RS weight clauses: {len(result)}")
