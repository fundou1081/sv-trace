"""
While Statement Parser - 使用正确的 AST 遍历

提取 while 语句：
- WhileStatement

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class WhileStatement:
    condition: str = ""
    body: str = ""


class WhileStatementExtractor:
    def __init__(self):
        self.statements: List[WhileStatement] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['WhileStatement', 'DoWhileStatement']:
                ws = WhileStatement()
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
        return [{'cond': s.condition[:35], 'body': s.body[:25]} for s in self.statements]


def extract_while_statements(code: str) -> List[Dict]:
    return WhileStatementExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
while (i < 10) begin
    i++;
end
'''
    result = extract_while_statements(test_code)
    print(f"While statements: {len(result)}")
