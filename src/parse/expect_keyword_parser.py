"""
Expect Keyword Parser - 使用正确的 AST 遍历

提取 expect 语句：
- ExpectKeyword

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ExpectStatement:
    action: str = ""


class ExpectExtractor:
    def __init__(self):
        self.statements: List[ExpectStatement] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['ExpectKeyword', 'ExpectStatement', 'ExpectPropertyStatement']:
                es = ExpectStatement()
                if hasattr(node, 'action') and node.action:
                    es.action = str(node.action)[:40]
                self.statements.append(es)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'action': s.action[:40]} for s in self.statements]


def extract_expect_statements(code: str) -> List[Dict]:
    return ExpectExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
expect (@posedge clk) a |-> b;
'''
    result = extract_expect_statements(test_code)
    print(f"Expect statements: {len(result)}")
