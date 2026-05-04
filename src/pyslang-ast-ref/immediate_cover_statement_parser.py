"""
Immediate Cover Statement Parser - 使用正确的 AST 遍历

提取立即覆盖语句：
- ImmediateCoverStatement

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ImmediateCoverStatement:
    expression: str = ""
    action: str = ""


class ImmediateCoverStatementExtractor:
    def __init__(self):
        self.statements: List[ImmediateCoverStatement] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['ImmediateCoverStatement', 'ImmediateCoverMember']:
                ics = ImmediateCoverStatement()
                
                if hasattr(node, 'expression') and node.expression:
                    ics.expression = str(node.expression)[:50]
                
                if hasattr(node, 'action') and node.action:
                    ics.action = str(node.action)[:30]
                
                self.statements.append(ics)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'expr': s.expression[:40], 'action': s.action[:25]} for s in self.statements]


def extract_cover_statements(code: str) -> List[Dict]:
    return ImmediateCoverStatementExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
cover (a) begin end
'''
    result = extract_cover_statements(test_code)
    print(f"Cover statements: {len(result)}")
