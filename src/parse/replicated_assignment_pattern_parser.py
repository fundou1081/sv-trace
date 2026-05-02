"""
Replicated Assignment Pattern Parser - 使用正确的 AST 遍历

提取重复赋值模式：
- ReplicatedAssignmentPattern

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ReplicatedAssignmentPattern:
    count: str = ""
    expression: str = ""


class ReplicatedAssignmentPatternExtractor:
    def __init__(self):
        self.patterns: List[ReplicatedAssignmentPattern] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ReplicatedAssignmentPattern':
                rap = ReplicatedAssignmentPattern()
                
                if hasattr(node, 'count') and node.count:
                    rap.count = str(node.count)[:20]
                
                if hasattr(node, 'expression') and node.expression:
                    rap.expression = str(node.expression)[:30]
                
                self.patterns.append(rap)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'count': p.count[:15], 'expr': p.expression[:25]} for p in self.patterns[:20]]


def extract_replicated_patterns(code: str) -> List[Dict]:
    return ReplicatedAssignmentPatternExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
int arr[4] = '{4{a}};
'''
    result = extract_replicated_patterns(test_code)
    print(f"Replicated patterns: {len(result)}")
