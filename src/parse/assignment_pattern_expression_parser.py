"""
Assignment Pattern Expression Parser - 使用正确的 AST 遍历

提取赋值模式表达式：
- AssignmentPatternExpression

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class AssignmentPatternExpr:
    patterns: List[str] = None
    
    def __post_init__(self):
        if self.patterns is None:
            self.patterns = []


class AssignmentPatternExpressionExtractor:
    def __init__(self):
        self.expressions: List[AssignmentPatternExpr] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'AssignmentPatternExpression':
                ape = AssignmentPatternExpr()
                
                patterns = []
                def get_patterns(n):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'Expression' in kn:
                        patterns.append(str(n)[:20])
                    return pyslang.VisitAction.Advance
                node.visit(get_patterns)
                ape.patterns = patterns[:20]
                
                self.expressions.append(ape)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'count': len(e.patterns)} for e in self.expressions[:20]]


def extract_assignment_patterns(code: str) -> List[Dict]:
    return AssignmentPatternExpressionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
logic [7:0] arr = '{0, 1, 2, 3};
'''
    result = extract_assignment_patterns(test_code)
    print(f"Assignment patterns: {len(result)}")
