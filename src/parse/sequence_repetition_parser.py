"""
Sequence Repetition Parser - 使用正确的 AST 遍历

提取序列重复：
- SequenceRepetition

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class SequenceRepetition:
    operator: str = ""
    count: str = ""
    sequence: str = ""


class SequenceRepetitionExtractor:
    def __init__(self):
        self.repetitions: List[SequenceRepetition] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['SequenceRepetition', 'ConsecutiveRepetition', 'NonConsecutiveRepetition']:
                sr = SequenceRepetition()
                sr.operator = '##'  # default SV repetition operator
                
                if hasattr(node, 'count') and node.count:
                    sr.count = str(node.count)[:20]
                
                if hasattr(node, 'sequence') and node.sequence:
                    sr.sequence = str(node.sequence)[:30]
                
                self.repetitions.append(sr)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'op': s.operator, 'count': s.count[:15], 'seq': s.sequence[:25]} for s in self.repetitions[:20]]


def extract_sequence_repetitions(code: str) -> List[Dict]:
    return SequenceRepetitionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
sequence s;
    a ##[1:3] b;
endsequence
'''
    result = extract_sequence_repetitions(test_code)
    print(f"Sequence repetitions: {len(result)}")
