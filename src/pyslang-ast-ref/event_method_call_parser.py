"""
Event Method Call Parser - 使用正确的 AST 遍历

提取事件方法调用：
- @event
- wait_order
- trigger

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
class EventMethodCall:
    method: str = ""  # trigger, wait_order, etc.
    expression: str = ""


class EventMethodCallExtractor:
    def __init__(self):
        self.events: List[EventMethodCall] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'EventMethodCall':
                em = EventMethodCall()
                if hasattr(node, 'method') and node.method:
                    em.method = str(node.method)
                if hasattr(node, 'expression') and node.expression:
                    em.expression = str(node.expression)
                self.events.append(em)
            
            elif kind_name == 'WaitOrderStatement':
                em = EventMethodCall()
                em.method = 'wait_order'
                if hasattr(node, 'condition') and node.condition:
                    em.expression = str(node.condition)
                self.events.append(em)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'method': e.method, 'expr': e.expression[:30]} for e in self.events]


def extract_event_methods(code: str) -> List[Dict]:
    return EventMethodCallExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
initial begin
    @(posedge clk);
    wait_order(a, b, c);
    ->evt;
end
'''
    result = extract_event_methods(test_code)
    print(f"Event methods: {len(result)}")
