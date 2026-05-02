"""
Range List Parser - 使用正确的 AST 遍历

提取范围列表：
- RangeList

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class RangeList:
    ranges: List[str] = None
    
    def __post_init__(self):
        if self.ranges is None:
            self.ranges = []


class RangeListExtractor:
    def __init__(self):
        self.lists: List[RangeList] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['RangeList', 'Range']:
                rl = RangeList()
                
                ranges = []
                def get_ranges(n):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'Range' in kn:
                        ranges.append(str(n)[:30])
                    return pyslang.VisitAction.Advance
                node.visit(get_ranges)
                rl.ranges = ranges[:20]
                
                self.lists.append(rl)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'count': len(l.ranges)} for l in self.lists[:20]]


def extract_range_lists(code: str) -> List[Dict]:
    return RangeListExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
a inside {[0:10], [20:30]};
'''
    result = extract_range_lists(test_code)
    print(f"Range lists: {len(result)}")
