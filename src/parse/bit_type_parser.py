"""
Bit Type Parser - 使用正确的 AST 遍历

提取 bit 类型：
- BitType
- IntegerVectorExpression
- IntegerBase

注意：此文件不包含任何正则表达式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang
from pyslang import SyntaxKind


@dataclass
class BitTypeInfo:
    type_keyword: str = ""
    signedness: str = ""  # signed, unsigned
    width: str = ""


class BitTypeExtractor:
    def __init__(self):
        self.types: List[BitTypeInfo] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['BitType', 'IntegerVectorExpression']:
                bt = BitTypeInfo()
                bt.type_keyword = 'bit'
                
                if hasattr(node, 'keyword') and node.keyword:
                    bt.type_keyword = str(node.keyword).lower()
                
                if hasattr(node, 'signed') and node.signed:
                    bt.signedness = 'signed'
                elif hasattr(node, 'unsigned') and node.unsigned:
                    bt.signedness = 'unsigned'
                
                self.types.append(bt)
            
            elif kind_name == 'IntegerBase':
                bt = BitTypeInfo()
                if hasattr(node, 'keyword') and node.keyword:
                    bt.type_keyword = str(node.keyword).lower()
                self.types.append(bt)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'keyword': t.type_keyword, 'signed': t.signedness} for t in self.types]


def extract_bit_types(code: str) -> List[Dict]:
    return BitTypeExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
logic [7:0] a;
bit signed [3:0] b;
'''
    result = extract_bit_types(test_code)
    print(f"Bit types: {len(result)}")
