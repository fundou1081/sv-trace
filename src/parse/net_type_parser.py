"""
Net Type Parser - 使用正确的 AST 遍历

提取线网类型：
- NetTypeKeyword
- NetTypeDeclaration

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class NetType:
    keyword: str = ""


class NetTypeExtractor:
    def __init__(self):
        self.types: List[NetType] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['NetTypeKeyword', 'NetTypeDeclaration', 'Tri0Keyword', 'Tri1Keyword',
                           'TriregKeyword', 'Supply0Keyword', 'Supply1Keyword']:
                nt = NetType()
                if hasattr(node, 'keyword') and node.keyword:
                    nt.keyword = str(node.keyword).lower()
                self.types.append(nt)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'keyword': t.keyword} for t in self.types]


def extract_net_types(code: str) -> List[Dict]:
    return NetTypeExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
wire w;
tri1 t1;
trireg tr;
'''
    result = extract_net_types(test_code)
    print(f"Net types: {len(result)}")
