"""
Iff Property Expression Parser - 使用正确的 AST 遍历

提取 iff 属性表达式：
- IffPropertyExpr

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class IffPropertyExpr:
    left: str = ""
    right: str = ""


class IffPropertyExprExtractor:
    def __init__(self):
        self.expressions: List[IffPropertyExpr] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'IffPropertyExpr':
                ipe = IffPropertyExpr()
                if hasattr(node, 'left') and node.left:
                    ipe.left = str(node.left)[:40]
                if hasattr(node, 'right') and node.right:
                    ipe.right = str(node.right)[:40]
                self.expressions.append(ipe)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'left': e.left[:35], 'right': e.right[:35]} for e in self.expressions]


def extract_iff_properties(code: str) -> List[Dict]:
    return IffPropertyExprExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
property p;
    a |-> b iff c;
endproperty
'''
    result = extract_iff_properties(test_code)
    print(f"Iff properties: {len(result)}")
