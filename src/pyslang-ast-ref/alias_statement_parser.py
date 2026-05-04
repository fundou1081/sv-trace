"""
Alias Statement Parser - 使用正确的 AST 遍历

提取 alias 语句：
- alias (a = b) 结构

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
class AliasStmt:
    """别名语句"""
    left: str = ""
    right: str = ""


class AliasStatementExtractor:
    def __init__(self):
        self.alias_stmts: List[AliasStmt] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'AliasStatement':
                a = AliasStmt()
                if hasattr(node, 'left') and node.left:
                    a.left = str(node.left)
                if hasattr(node, 'right') and node.right:
                    a.right = str(node.right)
                self.alias_stmts.append(a)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [
            {'left': a.left, 'right': a.right}
            for a in self.alias_stmts
        ]


def extract_alias_statements(code: str) -> List[Dict]:
    return AliasStatementExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
module test;
    alias bit [7:0] my_alias = original_signal;
endmodule
'''
    result = extract_alias_statements(test_code)
    print(f"Alias statements: {len(result)}")
