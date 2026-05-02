"""
Event Trigger Statement Parser - 使用正确的 AST 遍历

提取事件触发语句：
- BlockingEventTriggerStatement
- NonblockingEventTriggerStatement

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class EventTriggerStatement:
    is_blocking: bool = True
    event_name: str = ""


class EventTriggerStatementExtractor:
    def __init__(self):
        self.statements: List[EventTriggerStatement] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'BlockingEventTriggerStatement':
                ets = EventTriggerStatement()
                ets.is_blocking = True
                if hasattr(node, 'event') and node.event:
                    ets.event_name = str(node.event)
                self.statements.append(ets)
            
            elif kind_name == 'NonblockingEventTriggerStatement':
                ets = EventTriggerStatement()
                ets.is_blocking = False
                if hasattr(node, 'event') and node.event:
                    ets.event_name = str(node.event)
                self.statements.append(ets)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'blocking': s.is_blocking, 'event': s.event_name[:30]} for s in self.statements]


def extract_event_triggers(code: str) -> List[Dict]:
    return EventTriggerStatementExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
-> event_a;
->> event_b;
'''
    result = extract_event_triggers(test_code)
    print(f"Event triggers: {len(result)}")
