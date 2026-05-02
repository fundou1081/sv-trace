"""
Port Direction Keyword Parser - 使用正确的 AST 遍历

提取端口方向关键字：
- InputKeyword
- OutputKeyword
- InoutKeyword
- RefKeyword

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class PortDirectionKeyword:
    keyword: str = ""


class PortDirectionExtractor:
    def __init__(self):
        self.keywords: List[PortDirectionKeyword] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['InputKeyword', 'OutputKeyword', 'InoutKeyword', 'RefKeyword',
                           'WireKeyword', 'TriKeyword', 'Tri0Keyword', 'Tri1Keyword',
                           'TriRegKeyword', 'Supply0Keyword', 'Supply1Keyword']:
                pd = PortDirectionKeyword()
                pd.keyword = kind_name.replace('Keyword', '').lower()
                self.keywords.append(pd)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'keyword': k.keyword} for k in self.keywords[:50]]


def extract_port_direction_keywords(code: str) -> List[Dict]:
    return PortDirectionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
module m (input clk, output [7:0] data);
endmodule
'''
    result = extract_port_direction_keywords(test_code)
    print(f"Port direction keywords: {len(result)}")
