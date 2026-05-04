"""
Concurrent Assertion Member Parser - 使用正确的 AST 遍历

提取并发断言成员：
- ConcurrentAssertionMember

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
class ConcurrentAssertionMember:
    name: str = ""
    property_expr: str = ""


class ConcurrentAssertionMemberExtractor:
    def __init__(self):
        self.members: List[ConcurrentAssertionMember] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ConcurrentAssertionMember':
                cam = ConcurrentAssertionMember()
                if hasattr(node, 'name') and node.name:
                    cam.name = str(node.name)
                if hasattr(node, 'property') and node.property:
                    cam.property_expr = str(node.property)[:50]
                self.members.append(cam)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': m.name, 'property': m.property_expr[:30]} for m in self.members]


def extract_concurrent_assertion_members(code: str) -> List[Dict]:
    return ConcurrentAssertionMemberExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
assert property (@(posedge clk) req |-> ack) else $error("failed");
'''
    result = extract_concurrent_assertion_members(test_code)
    print(f"Concurrent assertion members: {len(result)}")
