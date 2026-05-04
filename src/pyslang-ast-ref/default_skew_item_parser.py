"""
Default Skew Item Parser - 使用正确的 AST 遍历

提取默认偏差项：
- DefaultSkewItem

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class DefaultSkewItem:
    clock_event: str = ""
    skew: str = ""


class DefaultSkewItemExtractor:
    def __init__(self):
        self.items: List[DefaultSkewItem] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'DefaultSkewItem':
                dsi = DefaultSkewItem()
                
                if hasattr(node, 'clockEvent') and node.clockEvent:
                    dsi.clock_event = str(node.clockEvent)[:30]
                if hasattr(node, 'clock') and node.clock:
                    dsi.clock_event = str(node.clock)[:30]
                
                if hasattr(node, 'skew') and node.skew:
                    dsi.skew = str(node.skew)[:30]
                
                self.items.append(dsi)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'clock': i.clock_event[:25], 'skew': i.skew[:20]} for i in self.items]


def extract_default_skew_items(code: str) -> List[Dict]:
    return DefaultSkewItemExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
default clocking cb @(posedge clk);
endclocking
'''
    result = extract_default_skew_items(test_code)
    print(f"Default skew items: {len(result)}")
