"""
Token List Parser - 使用正确的 AST 遍历

提取 token 列表：
- TokenList
- Semicolon
- Comma
- Colon
- Dot

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class Token:
    kind: str = ""


class TokenListExtractor:
    def __init__(self):
        self.tokens: List[Token] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['TokenList', 'Semicolon', 'Comma', 'Colon', 'Dot', 'Star',
                           'Plus', 'Minus', 'Equals', 'OpenBrace', 'CloseBrace',
                           'OpenBracket', 'CloseBracket', 'LessThan', 'GreaterThan',
                           'At', 'Hash', 'Tilde', 'Question', 'Percent', 'Bar',
                           'Ampersand', 'Caret', 'Bang', 'Dollar']:
                t = Token()
                t.kind = kind_name
                self.tokens.append(t)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'kind': t.kind} for t in self.tokens[:100]]


def extract_tokens(code: str) -> List[Dict]:
    return TokenListExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
a, b, c;
'''
    result = extract_tokens(test_code)
    print(f"Tokens: {len(result)}")
