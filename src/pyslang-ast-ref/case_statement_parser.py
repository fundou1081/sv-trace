"""
Case Statement Parser - 使用正确的 AST 遍历

提取 case 语句：
- CaseStatement

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class CaseStatement:
    expression: str = ""
    items: int = 0


class CaseStatementExtractor:
    def __init__(self):
        self.statements: List[CaseStatement] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['CaseStatement', 'CaseInsideStatement', 'CaseOutsideStatement']:
                cs = CaseStatement()
                if hasattr(node, 'expression') and node.expression:
                    cs.expression = str(node.expression)[:30]
                
                count = 0
                def count_items(n, c=[0]):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'CaseItem' in kn or 'Item' in kn:
                        c[0] += 1
                    return pyslang.VisitAction.Advance
                node.visit(count_items)
                cs.items = count
                
                self.statements.append(cs)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'expr': s.expression[:20], 'items': s.items} for s in self.statements]


def extract_case_statements(code: str) -> List[Dict]:
    return CaseStatementExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
case (sel)
    0: a = 1;
    1: a = 2;
endcase
'''
    result = extract_case_statements(test_code)
    print(f"Case statements: {len(result)}")
