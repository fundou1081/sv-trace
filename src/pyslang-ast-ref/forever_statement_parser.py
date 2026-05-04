"""
Forever Statement Parser - 使用正确的 AST 遍历

提取 forever 语句：
- ForeverStatement

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
class ForeverStatement:
    body: str = ""


class ForeverStatementExtractor:
    def __init__(self):
        self.statements: List[ForeverStatement] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ForeverStatement':
                fs = ForeverStatement()
                if hasattr(node, 'body') and node.body:
                    fs.body = str(node.body)[:50]
                self.statements.append(fs)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'body': s.body[:30]} for s in self.statements]


def extract_forever_statements(code: str) -> List[Dict]:
    return ForeverStatementExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
initial begin
    forever begin
        #10;
    end
end
'''
    result = extract_forever_statements(test_code)
    print(f"Forever statements: {len(result)}")
