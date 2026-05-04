"""
Real Type Parser - 使用正确的 AST 遍历

提取实数类型：
- RealType

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class RealType:
    keyword: str = "real"


class RealTypeExtractor:
    def __init__(self):
        self.types: List[RealType] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['RealType', 'ShortRealType', 'RealTimeType']:
                rt = RealType()
                if hasattr(node, 'keyword') and node.keyword:
                    rt.keyword = str(node.keyword).lower()
                self.types.append(rt)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'keyword': t.keyword} for t in self.types]


def extract_real_types(code: str) -> List[Dict]:
    return RealTypeExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
real pi;
shortreal sr;
realtime rt;
'''
    result = extract_real_types(test_code)
    print(f"Real types: {len(result)}")
