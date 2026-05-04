"""
For Loop Statement Parser - 使用正确的 AST 遍历

提取 for 循环语句：
- ForLoopStatement

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ForLoopStatement:
    init: str = ""
    condition: str = ""
    increment: str = ""
    body: str = ""


class ForLoopStatementExtractor:
    def __init__(self):
        self.statements: List[ForLoopStatement] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ForLoopStatement':
                fls = ForLoopStatement()
                
                if hasattr(node, 'init') and node.init:
                    fls.init = str(node.init)[:30]
                
                if hasattr(node, 'condition') and node.condition:
                    fls.condition = str(node.condition)[:30]
                
                if hasattr(node, 'increment') and node.increment:
                    fls.increment = str(node.increment)[:30]
                
                if hasattr(node, 'body') and node.body:
                    fls.body = str(node.body)[:30]
                
                self.statements.append(fls)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'init': s.init[:20], 'cond': s.condition[:20], 'inc': s.increment[:20]} for s in self.statements]


def extract_for_loops(code: str) -> List[Dict]:
    return ForLoopStatementExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
for (int i = 0; i < 10; i++) begin
end
'''
    result = extract_for_loops(test_code)
    print(f"For loops: {len(result)}")
