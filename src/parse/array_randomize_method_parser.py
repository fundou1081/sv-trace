"""
Array/Randomize Method Expression Parser - 使用正确的 AST 遍历

提取数组/随机方法表达式：
- ArrayOrRandomizeMethodExpression

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ArrayOrRandomizeMethod:
    name: str = ""
    arguments: List[str] = None
    
    def __post_init__(self):
        if self.arguments is None:
            self.arguments = []


class ArrayOrRandomizeMethodExtractor:
    def __init__(self):
        self.methods: List[ArrayOrRandomizeMethod] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ArrayOrRandomizeMethodExpression':
                arm = ArrayOrRandomizeMethod()
                if hasattr(node, 'name') and node.name:
                    arm.name = str(node.name)
                
                args = []
                def get_args(n):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if kn in ['ArgumentList', 'Argument']:
                        args.append(str(n)[:20])
                    return pyslang.VisitAction.Advance
                node.visit(get_args)
                arm.arguments = args[:5]
                
                self.methods.append(arm)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': m.name, 'args': len(m.arguments)} for m in self.methods[:20]]


def extract_array_methods(code: str) -> List[Dict]:
    return ArrayOrRandomizeMethodExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
arr.size();
obj.randomize();
'''
    result = extract_array_methods(test_code)
    print(f"Array/randomize methods: {len(result)}")
