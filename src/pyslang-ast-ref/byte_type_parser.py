"""
Byte Type Parser - 使用正确的 AST 遍历

提取 byte 类型：
- ByteType

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ByteType:
    keyword: str = "byte"
    signedness: str = ""


class ByteTypeExtractor:
    def __init__(self):
        self.types: List[ByteType] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ByteType':
                bt = ByteType()
                if hasattr(node, 'keyword') and node.keyword:
                    bt.keyword = str(node.keyword).lower()
                if hasattr(node, 'signed') and node.signed:
                    bt.signedness = 'signed'
                elif hasattr(node, 'unsigned') and node.unsigned:
                    bt.signedness = 'unsigned'
                self.types.append(bt)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'keyword': t.keyword, 'signedness': t.signedness} for t in self.types]


def extract_byte_types(code: str) -> List[Dict]:
    return ByteTypeExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
byte b;
signed byte sb;
'''
    result = extract_byte_types(test_code)
    print(f"Byte types: {len(result)}")
