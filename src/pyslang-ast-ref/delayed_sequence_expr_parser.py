"""
Delayed Sequence Expression Parser - 使用正确的 AST 遍历

提取延迟序列表达式：
- DelayedSequenceExpr
- DelayedSequenceElement
- ClockingSequenceExpr

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
class DelayedSequenceExpr:
    delay: str = ""
    sequence: str = ""


class DelayedSequenceExprExtractor:
    def __init__(self):
        self.expressions: List[DelayedSequenceExpr] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['DelayedSequenceExpr', 'DelayedSequenceElement', 'ClockingSequenceExpr']:
                dse = DelayedSequenceExpr()
                if hasattr(node, 'delay') and node.delay:
                    dse.delay = str(node.delay)
                if hasattr(node, 'sequence') and node.sequence:
                    dse.sequence = str(node.sequence)[:30]
                self.expressions.append(dse)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'delay': d.delay[:20], 'sequence': d.sequence[:30]} for d in self.expressions]


def extract_delayed_sequences(code: str) -> List[Dict]:
    return DelayedSequenceExprExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
sequence s;
    ##1 a;
endsequence
'''
    result = extract_delayed_sequences(test_code)
    print(f"Delayed sequences: {len(result)}")
