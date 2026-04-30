"""
Clocking 解析器 - 使用 pyslang AST

支持:
- ClockingDeclaration
- ClockingBlock
- ClockingItem
- Default clocking
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Optional
import pyslang
from pyslang import SyntaxKind


@dataclass
class ClockingItem:
    """clocking block item"""
    kind: str = ""
    name: str = ""
    direction: str = ""  # input, output, inout
    expression: str = ""


@dataclass
class ClockingDef:
    """clocking definition"""
    name: str = ""
    event: str = ""  # @(posedge clk)
    items: List[ClockingItem] = field(default_factory=list)
    default_input: str = ""
    default_output: str = ""


class ClockingExtractor:
    def __init__(self, parser=None):
        self.parser = parser
        self.clockings = {}
        
        if parser:
            self._extract_all()
    
    def _extract_all(self):
        for key, tree in getattr(self.parser, 'trees', {}).items():
            root = tree.root if hasattr(tree, 'root') else tree
            self._extract_from_tree(root)
    
    def _extract_from_tree(self, root):
        def collect(node):
            kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            
            if kind_name == 'ClockingDeclaration':
                self._extract_clock(node)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _extract_clock(self, node):
        clk = ClockingDef()
        
        # 名称
        if hasattr(node, 'name') and node.name:
            clk.name = str(node.name)
        
        # clocking event
        if hasattr(node, 'clockingSkew') and node.clockingSkew:
            clk.event = str(node.clockingSkew)
        
        # items
        if hasattr(node, 'items') and node.items:
            for item in node.items:
                if not item:
                    continue
                
                ci = ClockingItem()
                kind_name = item.kind.name if hasattr(item.kind, 'name') else str(item.kind)
                ci.kind = kind_name
                
                # ClockingItem
                if kind_name == 'ClockingItem':
                    if hasattr(item, 'identifier') and item.identifier:
                        ci.name = str(item.identifier)
                    if hasattr(item, 'direction'):
                        ci.direction = str(item.direction)
                    if hasattr(item, 'expression') and item.expression:
                        ci.expression = str(item.expression)
                
                clk.items.append(ci)
        
        # default input/output
        if hasattr(node, 'defaultInputDirection'):
            clk.default_input = str(node.defaultInputDirection)
        if hasattr(node, 'defaultOutputDirection'):
            clk.default_output = str(node.defaultOutputDirection)
        
        if clk.name:
            self.clockings[clk.name] = clk
    
    def get_clockings(self):
        return self.clockings


def extract_clockings(code):
    tree = pyslang.SyntaxTree.fromText(code)
    extractor = ClockingExtractor(None)
    extractor._extract_from_tree(tree)
    return extractor.clockings


if __name__ == "__main__":
    test_code = '''
module test;
    clocking cb @(posedge clk);
        default input #1step output #0;
        input data, valid;
        output ready;
        input #2 ack;
    endclocking
endmodule
'''
    
    result = extract_clockings(test_code)
    print("=== Clocking Extraction ===")
    for name, clk in result.items():
        print(f"\n{name}:")
        print(f"  event: {clk.event}")
        print(f"  items: {len(clk.items)}")
        for item in clk.items:
            print(f"    {item.name}: {item.direction}")
