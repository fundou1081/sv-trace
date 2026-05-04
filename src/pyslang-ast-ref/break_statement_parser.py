"""
Break Statement Parser - 使用正确的 AST 遍历

提取 break/continue 语句：
- BreakKeyword
- ContinueStatement

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class BreakContinueStatement:
    statement_type: str = ""


class BreakContinueExtractor:
    def __init__(self):
        self.statements: List[BreakContinueStatement] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['BreakKeyword', 'BreakStatement', 'ContinueStatement', 'ContinueKeyword']:
                bc = BreakContinueStatement()
                bc.statement_type = kind_name.replace('Keyword', '').replace('Statement', '').lower()
                self.statements.append(bc)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'type': s.statement_type} for s in self.statements]


def extract_break_continue(code: str) -> List[Dict]:
    return BreakContinueExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
while (i < 10) begin
    if (i == 5) break;
    if (i == 3) continue;
end
'''
    result = extract_break_continue(test_code)
    print(f"Break/Continue: {len(result)}")
