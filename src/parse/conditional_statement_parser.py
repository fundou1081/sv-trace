"""
Conditional Statement Parser - 使用正确的 AST 遍历

提取条件语句：
- ConditionalStatement (if-else)
- ConditionalPredicate
- ConditionalPattern

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
class ConditionalStmt:
    condition: str = ""
    then_stmt: str = ""
    else_stmt: str = ""


class ConditionalStatementExtractor:
    def __init__(self):
        self.statements: List[ConditionalStmt] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ConditionalStatement':
                cs = ConditionalStmt()
                if hasattr(node, 'condition') and node.condition:
                    cs.condition = str(node.condition)
                if hasattr(node, 'thenStatement') and node.thenStatement:
                    cs.then_stmt = str(node.thenStatement)[:50]
                if hasattr(node, 'elseStatement') and node.elseStatement:
                    cs.else_stmt = str(node.elseStatement)[:50]
                self.statements.append(cs)
            
            elif kind_name == 'ConditionalPredicate':
                cs = ConditionalStmt()
                if hasattr(node, 'condition') and node.condition:
                    cs.condition = str(node.condition)
                self.statements.append(cs)
            
            elif kind_name == 'ConditionalPattern':
                cs = ConditionalStmt()
                if hasattr(node, 'pattern') and node.pattern:
                    cs.condition = str(node.pattern)
                self.statements.append(cs)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [
            {'cond': s.condition[:30], 'has_else': bool(s.else_stmt)}
            for s in self.statements[:20]
        ]


def extract_conditionals(code: str) -> List[Dict]:
    return ConditionalStatementExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
if (a > b) begin
    x = 1;
end else begin
    x = 2;
end
'''
    result = extract_conditionals(test_code)
    print(f"Conditional statements: {len(result)}")
