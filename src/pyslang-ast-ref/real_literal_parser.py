"""
Real Literal Parser - 使用正确的 AST 遍历

提取实数字面量：
- 浮点数 (1.5, 2.0, 3.14)
- 科学计数法 (1e-10, 2.5E+3)

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
class RealLiteral:
    value: str = ""
    is_scientific: bool = False


class RealLiteralExtractor:
    def __init__(self):
        self.literals: List[RealLiteral] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'RealLiteral':
                rl = RealLiteral()
                if hasattr(node, 'value') and node.value:
                    rl.value = str(node.value)
                if 'e' in rl.value.lower():
                    rl.is_scientific = True
                self.literals.append(rl)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'value': rl.value, 'scientific': rl.is_scientific} for rl in self.literals]


def extract_real_literals(code: str) -> List[Dict]:
    return RealLiteralExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
real pi = 3.14159;
real scientific = 1.5e-10;
'''
    result = extract_real_literals(test_code)
    print(f"Real literals: {len(result)}")
