"""
Procedural Deassign Statement Parser - 使用正确的 AST 遍历

提取过程赋值语句：
- ProceduralDeassignStatement

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ProceduralDeassignStatement:
    target: str = ""


class ProceduralDeassignExtractor:
    def __init__(self):
        self.statements: List[ProceduralDeassignStatement] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ProceduralDeassignStatement':
                pds = ProceduralDeassignStatement()
                if hasattr(node, 'target') and node.target:
                    pds.target = str(node.target)[:30]
                self.statements.append(pds)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'target': s.target[:30]} for s in self.statements]


def extract_deassign(code: str) -> List[Dict]:
    return ProceduralDeassignExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
deassign sig;
'''
    result = extract_deassign(test_code)
    print(f"Deassign statements: {len(result)}")
