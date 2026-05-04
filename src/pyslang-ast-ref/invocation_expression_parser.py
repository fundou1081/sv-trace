"""
Invocation Expression Parser - 使用正确的 AST 遍历

提取函数/任务调用：
- InvocationExpression
- ArgumentList
- OrderedArgument
- NamedArgument

注意：此文件不包含任何正则表达式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict
import pyslang
from pyslang import SyntaxKind


@dataclass
class Argument:
    name: str = ""
    value: str = ""
    is_ordered: bool = True


@dataclass
class Invocation:
    callee: str = ""
    arguments: List[Argument] = field(default_factory=list)


class InvocationExtractor:
    def __init__(self):
        self.invocations: List[Invocation] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'InvocationExpression':
                inv = Invocation()
                if hasattr(node, 'function') and node.function:
                    inv.callee = str(node.function)[:50]
                
                if hasattr(node, 'arguments') and node.arguments:
                    for arg in node.arguments:
                        inv.arguments.append(self._extract_argument(arg))
                
                self.invocations.append(inv)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _extract_argument(self, node) -> Argument:
        a = Argument()
        if hasattr(node, 'name') and node.name:
            a.name = str(node.name)
            a.is_ordered = False
        if hasattr(node, 'value') and node.value:
            a.value = str(node.value)[:30]
        elif hasattr(node, 'expression') and node.expression:
            a.value = str(node.expression)[:30]
        return a
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [
            {'callee': inv.callee[:30], 'args': len(inv.arguments)}
            for inv in self.invocations[:20]
        ]


def extract_invocations(code: str) -> List[Dict]:
    return InvocationExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
initial begin
    $display("Hello");
    foo(a, b, c);
end
'''
    result = extract_invocations(test_code)
    print(f"Invocations: {len(result)}")
