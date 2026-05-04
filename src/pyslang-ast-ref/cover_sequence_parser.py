"""
Cover Sequence Parser - 使用正确的 AST 遍历

提取覆盖序列：
- CoverSequence

注意：此文件不包含任何正则表达式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict
import pyslang
from pyslang import SyntaxKind


@dataclass
class CoverSequence:
    name: str = ""
    expression: str = ""


class CoverSequenceExtractor:
    def __init__(self):
        self.sequences: List[CoverSequence] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'CoverSequence':
                cs = CoverSequence()
                if hasattr(node, 'name') and node.name:
                    cs.name = str(node.name)
                if hasattr(node, 'expression') and node.expression:
                    cs.expression = str(node.expression)
                self.sequences.append(cs)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [
            {'name': cs.name, 'expr': cs.expression[:40]}
            for cs in self.sequences
        ]


def extract_cover_sequences(code: str) -> List[Dict]:
    return CoverSequenceExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
cover sequence (s1 ##1 s2);
'''
    result = extract_cover_sequences(test_code)
    print(f"Cover sequences: {len(result)}")
