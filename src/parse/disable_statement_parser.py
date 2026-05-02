"""
Disable Statement Parser - 使用正确的 AST 遍历

提取 disable 语句：
- DisableStatement

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class DisableStatement:
    target: str = ""


class DisableStatementExtractor:
    def __init__(self):
        self.statements: List[DisableStatement] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['DisableStatement', 'DisableForkStatement']:
                ds = DisableStatement()
                
                if hasattr(node, 'target') and node.target:
                    ds.target = str(node.target)
                elif hasattr(node, 'name') and node.name:
                    ds.target = str(node.name)
                
                self.statements.append(ds)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'target': s.target[:30]} for s in self.statements]


def extract_disable_statements(code: str) -> List[Dict]:
    return DisableStatementExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
disable task_name;
'''
    result = extract_disable_statements(test_code)
    print(f"Disable statements: {len(result)}")
