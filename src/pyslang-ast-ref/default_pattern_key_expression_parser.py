"""
Default Pattern Key Expression Parser - 使用正确的 AST 遍历

提取默认模式键表达式：
- DefaultPatternKeyExpression

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class DefaultPatternKeyExpr:
    key: str = ""
    pattern: str = ""


class DefaultPatternKeyExprExtractor:
    def __init__(self):
        self.expressions: List[DefaultPatternKeyExpr] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'DefaultPatternKeyExpression':
                dpke = DefaultPatternKeyExpr()
                if hasattr(node, 'key') and node.key:
                    dpke.key = str(node.key)[:30]
                if hasattr(node, 'pattern') and node.pattern:
                    dpke.pattern = str(node.pattern)[:30]
                self.expressions.append(dpke)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'key': e.key[:25], 'pattern': e.pattern[:25]} for e in self.expressions[:20]]


def extract_default_patterns(code: str) -> List[Dict]:
    return DefaultPatternKeyExprExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
with (item.key := item.default);
'''
    result = extract_default_patterns(test_code)
    print(f"Default pattern key expressions: {len(result)}")
