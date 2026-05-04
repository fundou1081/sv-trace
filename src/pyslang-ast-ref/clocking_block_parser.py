"""
Clocking Block Parser - 使用正确的 AST 遍历

提取时钟块：
- ClockingBlock

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ClockingBlock:
    name: str = ""
    clock_event: str = ""


class ClockingBlockExtractor:
    def __init__(self):
        self.blocks: List[ClockingBlock] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ClockingBlock':
                cb = ClockingBlock()
                
                if hasattr(node, 'name') and node.name:
                    cb.name = str(node.name)
                
                if hasattr(node, 'clock') and node.clock:
                    cb.clock_event = str(node.clock)[:30]
                elif hasattr(node, 'event') and node.event:
                    cb.clock_event = str(node.event)[:30]
                
                self.blocks.append(cb)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': b.name or '(default)', 'clock': b.clock_event[:30]} for b in self.blocks]


def extract_clocking_blocks(code: str) -> List[Dict]:
    return ClockingBlockExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
clocking cb @(posedge clk);
endclocking
'''
    result = extract_clocking_blocks(test_code)
    print(f"Clocking blocks: {len(result)}")
