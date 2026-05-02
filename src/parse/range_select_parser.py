"""
Range Select Parser - 使用正确的 AST 遍历

提取范围选择表达式：
- AscendingRangeSelect
- DescendingRangeSelect

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class RangeSelect:
    direction: str = ""
    left: str = ""
    right: str = ""


class RangeSelectExtractor:
    def __init__(self):
        self.selects: List[RangeSelect] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['AscendingRangeSelect', 'DescendingRangeSelect']:
                rs = RangeSelect()
                rs.direction = 'ascending' if 'Ascending' in kind_name else 'descending'
                
                if hasattr(node, 'left') and node.left:
                    rs.left = str(node.left)[:20]
                if hasattr(node, 'right') and node.right:
                    rs.right = str(node.right)[:20]
                
                self.selects.append(rs)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'dir': s.direction, 'left': s.left[:15], 'right': s.right[:15]} for s in self.selects[:20]]


def extract_range_selects(code: str) -> List[Dict]:
    return RangeSelectExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
logic [7:0] arr [10];
'''
    result = extract_range_selects(test_code)
    print(f"Range selects: {len(result)}")
