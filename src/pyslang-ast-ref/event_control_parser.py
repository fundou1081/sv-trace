"""
Event Control Parser - 使用正确的 AST 遍历

提取事件控制：
- EventControl

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class EventControl:
    events: str = ""


class EventControlExtractor:
    def __init__(self):
        self.controls: List[EventControl] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['EventControl', 'EdgeEventControl', 'LevelEventControl']:
                ec = EventControl()
                
                if hasattr(node, 'event') and node.event:
                    ec.events = str(node.event)[:40]
                elif hasattr(node, 'events') and node.events:
                    ec.events = str(node.events)[:40]
                
                self.controls.append(ec)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'events': c.events[:40]} for c in self.controls]


def extract_event_controls(code: str) -> List[Dict]:
    return EventControlExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
@(posedge clk)
@(negedge rst)
'''
    result = extract_event_controls(test_code)
    print(f"Event controls: {len(result)}")
