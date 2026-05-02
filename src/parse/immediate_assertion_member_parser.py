"""
Immediate Assertion Member Parser - 使用正确的 AST 遍历

提取立即断言成员：
- ImmediateAssertionMember

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ImmediateAssertionMember:
    assertion_type: str = ""
    expression: str = ""


class ImmediateAssertionMemberExtractor:
    def __init__(self):
        self.members: List[ImmediateAssertionMember] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['ImmediateAssertionMember', 'ImmediateAssertStatement']:
                iam = ImmediateAssertionMember()
                
                if hasattr(node, 'assertion') and node.assertion:
                    iam.expression = str(node.assertion)[:50]
                elif hasattr(node, 'property') and node.property:
                    iam.expression = str(node.property)[:50]
                
                self.members.append(iam)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'type': m.assertion_type, 'expr': m.expression[:40]} for m in self.members]


def extract_immediate_assertions(code: str) -> List[Dict]:
    return ImmediateAssertionMemberExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
assert (a) else $error("fail");
'''
    result = extract_immediate_assertions(test_code)
    print(f"Immediate assertions: {len(result)}")
