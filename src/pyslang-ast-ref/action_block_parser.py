"""
Action Block Parser - 使用正确的 AST 遍历

提取动作块：
- ActionBlock

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
class ActionBlock:
    statement: str = ""
    is_empty: bool = False


class ActionBlockExtractor:
    def __init__(self):
        self.blocks: List[ActionBlock] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ActionBlock':
                ab = ActionBlock()
                if hasattr(node, 'statement') and node.statement:
                    ab.statement = str(node.statement)[:50]
                elif hasattr(node, 'body') and node.body:
                    ab.statement = str(node.body)[:50]
                else:
                    ab.is_empty = True
                self.blocks.append(ab)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'stmt': b.statement[:30], 'empty': b.is_empty} for b in self.blocks]


def extract_action_blocks(code: str) -> List[Dict]:
    return ActionBlockExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
assert (a) else begin end
'''
    result = extract_action_blocks(test_code)
    print(f"Action blocks: {len(result)}")
