"""
Argument List Parser - 使用正确的 AST 遍历

提取参数列表：
- ArgumentList

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ArgumentList:
    arguments: List[str] = None
    
    def __post_init__(self):
        if self.arguments is None:
            self.arguments = []


class ArgumentListExtractor:
    def __init__(self):
        self.lists: List[ArgumentList] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['ArgumentList', 'Argument']:
                al = ArgumentList()
                
                args = []
                def get_args(n):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'Expression' in kn or 'Identifier' in kn:
                        args.append(str(n)[:30])
                    return pyslang.VisitAction.Advance
                node.visit(get_args)
                al.arguments = args[:20]
                
                self.lists.append(al)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'count': len(l.arguments)} for l in self.lists[:20]]


def extract_argument_lists(code: str) -> List[Dict]:
    return ArgumentListExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
foo(a, b, c)
'''
    result = extract_argument_lists(test_code)
    print(f"Argument lists: {len(result)}")
