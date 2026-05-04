"""
Expect Property Statement Parser - 使用正确的 AST 遍历

提取 expect property 语句：
- ExpectPropertyStatement

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
class ExpectPropertyStmt:
    property_expr: str = ""
    action_block: str = ""


class ExpectPropertyExtractor:
    def __init__(self):
        self.statements: List[ExpectPropertyStmt] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ExpectPropertyStatement':
                stmt = ExpectPropertyStmt()
                if hasattr(node, 'property') and node.property:
                    stmt.property_expr = str(node.property)
                if hasattr(node, 'action') and node.action:
                    stmt.action_block = str(node.action)
                self.statements.append(stmt)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [
            {'property': e.property_expr[:50], 'has_action': bool(e.action_block)}
            for e in self.statements
        ]


def extract_expect_property(code: str) -> List[Dict]:
    return ExpectPropertyExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
expect property (@(posedge clk) req |-> ##[1:3] ack) else $error("Expect failed");
'''
    result = extract_expect_property(test_code)
    print(f"Expect property statements: {len(result)}")
