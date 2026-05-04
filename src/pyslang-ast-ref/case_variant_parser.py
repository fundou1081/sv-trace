"""
Case Variant Parser - 使用正确的 AST 遍历

提取 casex/casez 变体：
- CaseXKeyword
- CaseZKeyword

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class CaseVariant:
    keyword: str = ""


class CaseVariantExtractor:
    def __init__(self):
        self.variants: List[CaseVariant] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['CaseXKeyword', 'CaseZKeyword']:
                cv = CaseVariant()
                cv.keyword = kind_name.lower().replace('keyword', '')
                self.variants.append(cv)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'keyword': v.keyword} for v in self.variants]


def extract_case_variants(code: str) -> List[Dict]:
    return CaseVariantExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
casex (sel)
casez (sel)
endcase
'''
    result = extract_case_variants(test_code)
    print(f"Case variants: {len(result)}")
