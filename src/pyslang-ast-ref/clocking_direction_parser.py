"""
Clocking Direction Parser - 使用正确的 AST 遍历

提取 clocking 方向：
- ClockingDirection
- ClockingSkew

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
class ClockingDirection:
    direction: str = ""  # input, output, inout
    signal: str = ""
    skew: str = ""


@dataclass
class ClockingSkew:
    edge: str = ""  # posedge, negedge, etc.
    delay: str = ""


class ClockingDirectionExtractor:
    def __init__(self):
        self.directions: List[ClockingDirection] = []
        self.skews: List[ClockingSkew] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ClockingDirection':
                cd = ClockingDirection()
                if hasattr(node, 'direction') and node.direction:
                    cd.direction = str(node.direction).lower()
                if hasattr(node, 'name') and node.name:
                    cd.signal = str(node.name)
                if hasattr(node, 'skew') and node.skew:
                    cd.skew = str(node.skew)
                self.directions.append(cd)
            
            elif kind_name == 'ClockingSkew':
                cs = ClockingSkew()
                if hasattr(node, 'edge') and node.edge:
                    cs.edge = str(node.edge)
                if hasattr(node, 'delay') and node.delay:
                    cs.delay = str(node.delay)
                self.skews.append(cs)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> Dict:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return {
            'directions': [{'dir': d.direction, 'signal': d.signal, 'skew': d.skew} for d in self.directions],
            'skews': [{'edge': s.edge, 'delay': s.delay} for s in self.skews]
        }


def extract_clocking_directions(code: str) -> Dict:
    return ClockingDirectionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
clocking cb @(posedge clk);
    default input #1step output #2;
    input data;
    output #1 addr;
endclocking
'''
    result = extract_clocking_directions(test_code)
    print(f"Directions: {len(result['directions'])}, Skews: {len(result['skews'])}")
