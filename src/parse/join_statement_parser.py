"""
Join Statement Parser - 使用正确的 AST 遍历

提取 join 语句：
- JoinStatement
- JoinAnyStatement
- JoinNoneStatement

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
class JoinStmt:
    join_type: str = ""  # join, join_any, join_none


class JoinStatementExtractor:
    def __init__(self):
        self.statements: List[JoinStmt] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'JoinStatement':
                stmt = JoinStmt()
                stmt.join_type = 'join'
                self.statements.append(stmt)
            
            elif kind_name == 'JoinAnyStatement':
                stmt = JoinStmt()
                stmt.join_type = 'join_any'
                self.statements.append(stmt)
            
            elif kind_name == 'JoinNoneStatement':
                stmt = JoinStmt()
                stmt.join_type = 'join_none'
                self.statements.append(stmt)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'type': s.join_type} for s in self.statements]


def extract_join_statements(code: str) -> List[Dict]:
    return JoinStatementExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
fork
    begin
        #10;
    end
join

fork
    process1();
join_any

fork
    process2();
join_none
'''
    result = extract_join_statements(test_code)
    print(f"Join statements: {len(result)}")
