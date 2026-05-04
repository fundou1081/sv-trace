"""
Clocking Item Parser - 使用正确的 AST 遍历

提取时钟块项目：
- ClockingItem

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ClockingItem:
    name: str = ""
    direction: str = ""


class ClockingItemExtractor:
    def __init__(self):
        self.items: List[ClockingItem] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ClockingItem':
                ci = ClockingItem()
                if hasattr(node, 'name') and node.name:
                    ci.name = str(node.name)
                if hasattr(node, 'direction') and node.direction:
                    ci.direction = str(node.direction).lower()
                self.items.append(ci)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': i.name[:20], 'direction': i.direction[:10]} for i in self.items]


def extract_clocking_items(code: str) -> List[Dict]:
    return ClockingItemExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
clocking cb @(posedge clk);
    default input #1step output #2;
endclocking
'''
    result = extract_clocking_items(test_code)
    print(f"Clocking items: {len(result)}")
