"""
Plus Colon Expression Parser - 使用正确的 AST 遍历

提取 +: 动态位选择表达式：
- PlusColon

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class PlusColonExpr:
    base: str = ""
    width: str = ""


class PlusColonExtractor:
    def __init__(self):
        self.expressions: List[PlusColonExpr] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'PlusColon':
                pce = PlusColonExpr()
                if hasattr(node, 'base') and node.base:
                    pce.base = str(node.base)[:20]
                if hasattr(node, 'width') and node.width:
                    pce.width = str(node.width)[:15]
                self.expressions.append(pce)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'base': e.base[:20], 'width': e.width[:15]} for e in self.expressions[:20]]


def extract_plus_colon(code: str) -> List[Dict]:
    return PlusColonExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
logic [31:0] data;
logic [7:0] slice = data[base +: 8];
'''
    result = extract_plus_colon(test_code)
    print(f"Plus colon expressions: {len(result)}")
