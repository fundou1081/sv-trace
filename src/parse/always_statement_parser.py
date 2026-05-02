"""
Always Statement Parser - 使用正确的 AST 遍历

提取 always/always_ff/always_comb/always_latch 语句：
- AlwaysBlock (statement level)

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
class AlwaysStmt:
    block_type: str = ""
    sensitivity: str = ""


class AlwaysStmtExtractor:
    def __init__(self):
        self.statements: List[AlwaysStmt] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'AlwaysBlock':
                stmt = AlwaysStmt()
                stmt.block_type = 'always'
                
                if hasattr(node, 'control') and node.control:
                    ctrl = node.control
                    if hasattr(ctrl, 'eventExpression'):
                        stmt.sensitivity = str(ctrl.eventExpression)
                
                self.statements.append(stmt)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'type': s.block_type, 'sensitivity': s.sensitivity[:30]} for s in self.statements]


def extract_always_stmts(code: str) -> List[Dict]:
    return AlwaysStmtExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
always @(posedge clk) begin
    q <= d;
end
'''
    result = extract_always_stmts(test_code)
    print(f"Always statements: {len(result)}")
