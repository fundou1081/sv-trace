"""
Throughout Sequence Expression Parser - 使用正确的 AST 遍历

提取 throughout 序列表达式：
- ThroughoutSequenceExpr

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ThroughoutSequenceExpr:
    sequence: str = ""
    constraint: str = ""


class ThroughoutSequenceExprExtractor:
    def __init__(self):
        self.expressions: List[ThroughoutSequenceExpr] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ThroughoutSequenceExpr':
                tse = ThroughoutSequenceExpr()
                if hasattr(node, 'sequence') and node.sequence:
                    tse.sequence = str(node.sequence)[:40]
                if hasattr(node, 'constraint') and node.constraint:
                    tse.constraint = str(node.constraint)[:40]
                self.expressions.append(tse)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'sequence': e.sequence[:35], 'constraint': e.constraint[:35]} for e in self.expressions]


def extract_throughout(code: str) -> List[Dict]:
    return ThroughoutSequenceExprExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
sequence s;
    a throughout b;
endsequence
'''
    result = extract_throughout(test_code)
    print(f"Throughout expressions: {len(result)}")
