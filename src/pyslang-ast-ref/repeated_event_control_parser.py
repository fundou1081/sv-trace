"""
Repeated Event Control Parser - 使用正确的 AST 遍历

提取重复事件控制：
- RepeatedEventControl

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class RepeatedEventControl:
    count: str = ""
    event: str = ""


class RepeatedEventControlExtractor:
    def __init__(self):
        self.controls: List[RepeatedEventControl] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'RepeatedEventControl':
                rec = RepeatedEventControl()
                
                if hasattr(node, 'count') and node.count:
                    rec.count = str(node.count)[:20]
                
                if hasattr(node, 'event') and node.event:
                    rec.event = str(node.event)[:30]
                
                self.controls.append(rec)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'count': c.count[:15], 'event': c.event[:25]} for c in self.controls]


def extract_repeated_events(code: str) -> List[Dict]:
    return RepeatedEventControlExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
##[1:3] event_trigger;
'''
    result = extract_repeated_events(test_code)
    print(f"Repeated event controls: {len(result)}")
