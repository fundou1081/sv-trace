"""
Assignment Pattern Item Parser - 使用正确的 AST 遍历

提取赋值模式项：
- AssignmentPatternItem
- StructuredAssignmentPattern

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class AssignmentPatternItem:
    name: str = ""
    pattern: str = ""


class AssignmentPatternItemExtractor:
    def __init__(self):
        self.items: List[AssignmentPatternItem] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['AssignmentPatternItem', 'StructuredAssignmentPattern',
                           'SimpleAssignmentPattern']:
                api = AssignmentPatternItem()
                if hasattr(node, 'name') and node.name:
                    api.name = str(node.name)[:30]
                if hasattr(node, 'pattern') and node.pattern:
                    api.pattern = str(node.pattern)[:30]
                self.items.append(api)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': i.name[:25], 'pattern': i.pattern[:25]} for i in self.items[:20]]


def extract_assignment_patterns(code: str) -> List[Dict]:
    return AssignmentPatternItemExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
int arr[4] = '{0, 1, 2, 3};
'''
    result = extract_assignment_patterns(test_code)
    print(f"Assignment pattern items: {len(result)}")
