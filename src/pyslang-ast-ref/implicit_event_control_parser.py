"""
Implicit Event Control Parser - 使用正确的 AST 遍历

提取隐式事件控制：
- ImplicitEventControl
- StarEventControl

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ImplicitEventControl:
    event_list: str = ""


class ImplicitEventControlExtractor:
    def __init__(self):
        self.controls: List[ImplicitEventControl] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['ImplicitEventControl', 'StarEventControl', 'ImplicitTrigger']:
                iec = ImplicitEventControl()
                if hasattr(node, 'events') and node.events:
                    iec.event_list = str(node.events)[:30]
                elif hasattr(node, 'event') and node.event:
                    iec.event_list = str(node.event)[:30]
                self.controls.append(iec)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'events': c.event_list[:30]} for c in self.controls]


def extract_implicit_events(code: str) -> List[Dict]:
    return ImplicitEventControlExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
always @* begin
end
'''
    result = extract_implicit_events(test_code)
    print(f"Implicit event controls: {len(result)}")
