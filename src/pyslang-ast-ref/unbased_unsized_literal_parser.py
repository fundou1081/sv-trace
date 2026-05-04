"""
Unbased Unsized Literal Parser - 使用正确的 AST 遍历

提取无基础位宽字面量：
- UnbasedUnsizedLiteral
- UnbasedUnsizedLiteralExpression

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class UnbasedUnsizedLiteral:
    value: str = ""


class UnbasedUnsizedLiteralExtractor:
    def __init__(self):
        self.literals: List[UnbasedUnsizedLiteral] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['UnbasedUnsizedLiteral', 'UnbasedUnsizedLiteralExpression']:
                uul = UnbasedUnsizedLiteral()
                if hasattr(node, 'literal') and node.literal:
                    uul.value = str(node.literal)[:20]
                self.literals.append(uul)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'value': l.value[:20]} for l in self.literals[:20]]


def extract_unbased_literals(code: str) -> List[Dict]:
    return UnbasedUnsizedLiteralExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
logic [7:0] a = '0;
logic [15:0] b = '1;
logic c = 'x;
'''
    result = extract_unbased_literals(test_code)
    print(f"Unbased unsized literals: {len(result)}")
