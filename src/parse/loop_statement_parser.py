"""
Loop Statement Parser - 使用正确的 AST 遍历

提取循环语句：
- LoopStatement

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
class LoopStatement:
    loop_type: str = ""  # for, while, do-while, foreach
    body: str = ""


class LoopStatementExtractor:
    def __init__(self):
        self.statements: List[LoopStatement] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'LoopStatement':
                ls = LoopStatement()
                if hasattr(node, 'statement') and node.statement:
                    ls.body = str(node.statement)[:50]
                
                # 检查类型
                if hasattr(node, 'keyword') and node.keyword:
                    ls.loop_type = str(node.keyword).lower()
                
                self.statements.append(ls)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'type': s.loop_type, 'body': s.body[:30]} for s in self.statements]


def extract_loop_statements(code: str) -> List[Dict]:
    return LoopStatementExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
for (int i = 0; i < 10; i++) begin
end
'''
    result = extract_loop_statements(test_code)
    print(f"Loop statements: {len(result)}")
