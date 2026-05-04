"""
Wait Parser - 使用 pyslang AST

支持:
- wait statement
- wait order
- wait fork
- procedural statements
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List
import pyslang
from pyslang import SyntaxKind


@dataclass
class WaitItem:
    """wait item"""
    kind: str = ""
    expression: str = ""


@dataclass
class WaitStatement:
    """wait statement"""
    condition: str = ""
    then_do: str = ""  # wait statement 的后续动作


@dataclass
class WaitOrderItem:
    """wait order item"""
    events: List[str] = field(default_factory=list)


class WaitParser:
    def __init__(self, parser=None):
        self.parser = parser
        self.waits = []
        self.wait_orders = []
        
        if parser:
            self._extract_all()
    
    def _extract_all(self):
        for key, tree in getattr(self.parser, 'trees', {}).items():
            root = tree.root if hasattr(tree, 'root') else tree
            self._extract_from_tree(root)
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'WaitStatement':
                self._extract_wait(node)
            elif kind_name == 'WaitOrderStatement':
                self._extract_wait_order(node)
            elif kind_name == 'ProceduralAssignStatement':
                self._extract_procedural_assign(node)
            elif kind_name == 'ProceduralForceStatement':
                self._extract_force(node)
            elif kind_name == 'ProceduralReleaseStatement':
                self._extract_release(node)
            
            return pyslang.VisitAction.Advance
        
        (root.root if hasattr(root, "root") else root).visit(collect)
    
    def _extract_wait(self, node):
        wait = WaitStatement()
        
        # 条件
        if hasattr(node, 'condition') and node.condition:
            wait.condition = str(node.condition)
        
        # then
        if hasattr(node, 'statement') and node.statement:
            wait.then_do = str(node.statement)
        
        self.waits.append(wait)
    
    def _extract_wait_order(self, node):
        wo = WaitOrderItem()
        
        # events (wait order (a, b, c))
        if hasattr(node, 'events') and node.events:
            for ev in node.events:
                if ev:
                    wo.events.append(str(ev))
        
        self.wait_orders.append(wo)
    
    def _extract_procedural_assign(self, node):
        # procedural assign (assign, force, release)
        pass
    
    def _extract_force(self, node):
        pass
    
    def _extract_release(self, node):
        pass
    
    def get_waits(self):
        return self.waits
    
    def get_wait_orders(self):
        return self.wait_orders


def extract_waits(code):
    tree = pyslang.SyntaxTree.fromText(code)
    extractor = WaitParser(None)
    extractor._extract_from_tree(tree)
    return extractor


if __name__ == "__main__":
    test_code = '''
module test;
    initial begin
        wait (data_valid);
        #10;
        
        wait order(a, b, c);
        
        assign data = tmp;
        force data = 0;
        release data;
    end
endmodule
'''
    
    result = extract_waits(test_code)
    print("=== Wait Parser ===")
    print(f"waits: {len(result.waits)}")
    print(f"wait_orders: {len(result.wait_orders)}")
