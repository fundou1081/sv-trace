"""
Clocking Skew Parser - 使用正确的 AST 遍历

提取时钟偏差：
- ClockingSkew

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ClockingSkew:
    delay: str = ""
    edge: str = ""


class ClockingSkewExtractor:
    def __init__(self):
        self.skews: List[ClockingSkew] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ClockingSkew':
                cs = ClockingSkew()
                
                if hasattr(node, 'delay') and node.delay:
                    cs.delay = str(node.delay)
                elif hasattr(node, 'edge') and node.edge:
                    cs.edge = str(node.edge)
                
                self.skews.append(cs)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'delay': s.delay[:20], 'edge': s.edge[:20]} for s in self.skews]


def extract_clocking_skews(code: str) -> List[Dict]:
    return ClockingSkewExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
##1 data;
'''
    result = extract_clocking_skews(test_code)
    print(f"Clocking skews: {len(result)}")
