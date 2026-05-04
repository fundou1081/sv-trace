"""
Deferred Assertion Parser - 使用正确的 AST 遍历

提取延迟断言：
- DeferredAssertion
- DeferredImmediateAssertion

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class DeferredAssertion:
    assertion_type: str = ""
    expression: str = ""


class DeferredAssertionExtractor:
    def __init__(self):
        self.assertions: List[DeferredAssertion] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['DeferredAssertion', 'DeferredImmediateAssertion']:
                da = DeferredAssertion()
                da.assertion_type = kind_name.replace('Deferred', '').replace('Assertion', '')
                
                if hasattr(node, 'assertion') and node.assertion:
                    da.expression = str(node.assertion)[:40]
                elif hasattr(node, 'property') and node.property:
                    da.expression = str(node.property)[:40]
                
                self.assertions.append(da)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'type': a.assertion_type, 'expr': a.expression[:40]} for a in self.assertions]


def extract_deferred_assertions(code: str) -> List[Dict]:
    return DeferredAssertionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
#0 assert (a) else $error("fail");
'''
    result = extract_deferred_assertions(test_code)
    print(f"Deferred assertions: {len(result)}")
