"""
chandle Type Parser - 使用正确的 AST 遍历

提取 chandle 类型：
- CHandleType

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class CHandleType:
    keyword: str = "chandle"


class CHandleTypeExtractor:
    def __init__(self):
        self.types: List[CHandleType] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'CHandleType':
                ct = CHandleType()
                if hasattr(node, 'keyword') and node.keyword:
                    ct.keyword = str(node.keyword).lower()
                self.types.append(ct)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'keyword': t.keyword} for t in self.types]


def extract_chandle_types(code: str) -> List[Dict]:
    return CHandleTypeExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
chandle handle;
'''
    result = extract_chandle_types(test_code)
    print(f"chandle types: {len(result)}")
