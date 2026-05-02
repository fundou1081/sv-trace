"""
Simple Assignment Pattern Parser - 使用正确的 AST 遍历

提取简单赋值模式：
- SimpleAssignmentPattern

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class SimpleAssignmentPattern:
    expressions: List[str] = None
    
    def __post_init__(self):
        if self.expressions is None:
            self.expressions = []


class SimpleAssignmentPatternExtractor:
    def __init__(self):
        self.patterns: List[SimpleAssignmentPattern] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'SimpleAssignmentPattern':
                sap = SimpleAssignmentPattern()
                
                exprs = []
                def get_exprs(n):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'Expression' in kn and 'Assignment' not in kn:
                        exprs.append(str(n)[:20])
                    return pyslang.VisitAction.Advance
                node.visit(get_exprs)
                sap.expressions = exprs[:20]
                
                self.patterns.append(sap)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'count': len(p.expressions)} for p in self.patterns[:20]]


def extract_simple_patterns(code: str) -> List[Dict]:
    return SimpleAssignmentPatternExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
int arr[4] = '{0, 1, 2, 3};
'''
    result = extract_simple_patterns(test_code)
    print(f"Simple patterns: {len(result)}")
