"""
Force Release Statement Parser - 使用正确的 AST 遍历

提取 force/release 语句：
- ForceStatement
- ReleaseStatement

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ForceReleaseStatement:
    statement_type: str = ""
    target: str = ""
    value: str = ""


class ForceReleaseExtractor:
    def __init__(self):
        self.statements: List[ForceReleaseStatement] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['ForceStatement', 'ReleaseStatement']:
                frs = ForceReleaseStatement()
                frs.statement_type = kind_name.replace('Statement', '').lower()
                
                if hasattr(node, 'target') and node.target:
                    frs.target = str(node.target)[:30]
                
                if hasattr(node, 'value') and node.value:
                    frs.value = str(node.value)[:30]
                
                self.statements.append(frs)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'type': s.statement_type, 'target': s.target[:25], 'value': s.value[:25]} for s in self.statements]


def extract_force_release(code: str) -> List[Dict]:
    return ForceReleaseExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
force sig = 1'b0;
release sig;
'''
    result = extract_force_release(test_code)
    print(f"Force/Release: {len(result)}")
