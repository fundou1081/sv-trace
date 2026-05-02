"""
Event Type Parser - 使用正确的 AST 遍历

提取事件类型：
- EventType

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class EventType:
    keyword: str = "event"


class EventTypeExtractor:
    def __init__(self):
        self.types: List[EventType] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['EventType', 'EventVariableType']:
                et = EventType()
                if hasattr(node, 'keyword') and node.keyword:
                    et.keyword = str(node.keyword).lower()
                self.types.append(et)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'keyword': t.keyword} for t in self.types]


def extract_event_types(code: str) -> List[Dict]:
    return EventTypeExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
event ev;
'''
    result = extract_event_types(test_code)
    print(f"Event types: {len(result)}")
