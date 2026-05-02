"""
Assert Cover Keyword Parser - 使用正确的 AST 遍历

提取 assert/cover/assume 关键字：
- AssertKeyword
- CoverKeyword
- AssumeKeyword

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class AssertCoverKeyword:
    keyword: str = ""


class AssertCoverExtractor:
    def __init__(self):
        self.keywords: List[AssertCoverKeyword] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['AssertKeyword', 'CoverKeyword', 'AssumeKeyword', 'BindKeyword',
                           'ExpectKeyword', 'AssertStatement', 'CoverStatement', 'AssumeStatement']:
                ack = AssertCoverKeyword()
                ack.keyword = kind_name.replace('Keyword', '').replace('Statement', '').lower()
                self.keywords.append(ack)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'keyword': k.keyword} for k in self.keywords[:50]]


def extract_assert_cover_keywords(code: str) -> List[Dict]:
    return AssertCoverExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
assert (a) else $error("fail");
cover property (@(posedge clk) a);
'''
    result = extract_assert_cover_keywords(test_code)
    print(f"Assert/Cover keywords: {len(result)}")
