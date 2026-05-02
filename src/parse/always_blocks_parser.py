"""
Always Blocks Parser - 使用正确的 AST 遍历

提取 always 块变体：
- AlwaysFFKeyword
- AlwaysCombKeyword
- AlwaysLatchKeyword

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class AlwaysBlock:
    block_type: str = ""


class AlwaysBlocksExtractor:
    def __init__(self):
        self.blocks: List[AlwaysBlock] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['AlwaysFFKeyword', 'AlwaysCombKeyword', 'AlwaysLatchKeyword']:
                ab = AlwaysBlock()
                ab.block_type = kind_name.replace('Keyword', '').replace('Always', '').lower()
                self.blocks.append(ab)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'type': b.block_type} for b in self.blocks]


def extract_always_blocks(code: str) -> List[Dict]:
    return AlwaysBlocksExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
always_ff @(posedge clk) begin end
always_comb begin end
always_latch begin end
'''
    result = extract_always_blocks(test_code)
    print(f"Always blocks: {len(result)}")
