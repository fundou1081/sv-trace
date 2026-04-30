"""
Final Block Parser - 使用 pyslang AST

支持:
- FinalBlock
- Final procedure (如 final $finish)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List
import pyslang
from pyslang import SyntaxKind


@dataclass
class FinalBlock:
    """final block"""
    name: str = ""
    statements: List[str] = field(default_factory=list)


class FinalBlockParser:
    def __init__(self, parser=None):
        self.parser = parser
        self.blocks = []
        
        if parser:
            self._extract_all()
    
    def _extract_all(self):
        for key, tree in getattr(self.parser, 'trees', {}).items():
            root = tree.root if hasattr(tree, 'root') else tree
            self._extract_from_tree(root)
    
    def _extract_from_tree(self, root):
        def collect(node):
            kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            
            if kind_name == 'FinalBlock':
                self._extract_final(node)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _extract_final(self, node):
        block = FinalBlock()
        
        if hasattr(node, 'name') and node.name:
            block.name = str(node.name)
        
        # statements
        if hasattr(node, 'statements'):
            for stmt in node.statements:
                if stmt:
                    block.statements.append(str(stmt))
        
        self.blocks.append(block)
    
    def get_blocks(self):
        return self.blocks


def extract_final_blocks(code):
    tree = pyslang.SyntaxTree.fromText(code)
    parser = FinalBlockParser(None)
    parser._extract_from_tree(tree)
    return parser.blocks


if __name__ == "__main__":
    test_code = '''
module test;
    final $finish(\$time);
    final begin
        $display("Simulation finished at %0t", $time);
    end
endmodule
'''
    
    result = extract_final_blocks(test_code)
    print("=== Final Blocks ===")
    for block in result:
        print(f"  {block.name}: {len(block.statements)} statements")
