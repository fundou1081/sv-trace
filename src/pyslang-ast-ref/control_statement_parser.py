"""
Control Statement Parser - 使用正确的 AST 遍历

提取控制语句：
- ReturnStatement
- BreakStatement
- ContinueStatement
- YieldStatement

注意：此文件不包含任何正则表达式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict
import pyslang
from pyslang import SyntaxKind


@dataclass
class ControlStmt:
    stmt_type: str = ""
    expression: str = ""


class ControlStatementExtractor:
    def __init__(self):
        self.return_stmts: List[ControlStmt] = []
        self.break_stmts: int = 0
        self.continue_stmts: int = 0
        self.yield_stmts: int = 0
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ReturnStatement':
                cs = ControlStmt()
                cs.stmt_type = 'return'
                if hasattr(node, 'expression') and node.expression:
                    cs.expression = str(node.expression)
                self.return_stmts.append(cs)
            
            elif kind_name == 'BreakStatement':
                self.break_stmts += 1
            
            elif kind_name == 'ContinueStatement':
                self.continue_stmts += 1
            
            elif kind_name == 'YieldStatement':
                self.yield_stmts += 1
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> Dict:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        
        return {
            'return': [{'expr': cs.expression[:30]} for cs in self.return_stmts],
            'break': self.break_stmts,
            'continue': self.continue_stmts,
            'yield': self.yield_stmts
        }


def extract_control_statements(code: str) -> Dict:
    return ControlStatementExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
function automatic int factorial(int n);
    if (n <= 1) return 1;
    return n * factorial(n - 1);
endfunction

task run;
    for (int i = 0; i < 10; i++) begin
        if (i == 5) break;
        if (i == 3) continue;
    end
endtask
'''
    result = extract_control_statements(test_code)
    print(f"Return: {len(result['return'])}, Break: {result['break']}, Continue: {result['continue']}")
