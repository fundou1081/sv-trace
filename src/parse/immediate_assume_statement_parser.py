"""
Immediate Assume Statement Parser - 使用正确的 AST 遍历

提取立即假设语句：
- ImmediateAssumeStatement

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ImmediateAssumeStatement:
    expression: str = ""
    action: str = ""


class ImmediateAssumeStatementExtractor:
    def __init__(self):
        self.statements: List[ImmediateAssumeStatement] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ImmediateAssumeStatement':
                ias = ImmediateAssumeStatement()
                
                if hasattr(node, 'expression') and node.expression:
                    ias.expression = str(node.expression)[:50]
                
                if hasattr(node, 'action') and node.action:
                    ias.action = str(node.action)[:30]
                
                self.statements.append(ias)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'expr': s.expression[:40], 'action': s.action[:20]} for s in self.statements]


def extract_assume_statements(code: str) -> List[Dict]:
    return ImmediateAssumeStatementExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
assume (a) else $error("assume failed");
'''
    result = extract_assume_statements(test_code)
    print(f"Assume statements: {len(result)}")
