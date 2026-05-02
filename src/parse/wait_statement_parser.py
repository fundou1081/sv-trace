"""
Wait Statement Parser - 使用正确的 AST 遍历

提取 wait 语句：
- WaitStatement
- WaitOrderStatement

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class WaitStatement:
    condition: str = ""
    body: str = ""


class WaitStatementExtractor:
    def __init__(self):
        self.statements: List[WaitStatement] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['WaitStatement', 'WaitOrderStatement']:
                ws = WaitStatement()
                if hasattr(node, 'condition') and node.condition:
                    ws.condition = str(node.condition)[:40]
                if hasattr(node, 'body') and node.body:
                    ws.body = str(node.body)[:30]
                self.statements.append(ws)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'cond': s.condition[:40], 'body': s.body[:30]} for s in self.statements]


def extract_wait_statements(code: str) -> List[Dict]:
    return WaitStatementExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
wait (data_ready) begin
end
'''
    result = extract_wait_statements(test_code)
    print(f"Wait statements: {len(result)}")
