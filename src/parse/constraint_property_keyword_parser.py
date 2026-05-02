"""
Constraint Property Keyword Parser - 使用正确的 AST 遍历

提取 constraint/property/sequence 关键字：
- ConstraintKeyword
- PropertyKeyword
- SequenceKeyword

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ConstraintKeyword:
    keyword: str = ""


class ConstraintKeywordExtractor:
    def __init__(self):
        self.keywords: List[ConstraintKeyword] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['ConstraintKeyword', 'PropertyKeyword', 'SequenceKeyword',
                           'EndConstraintKeyword', 'EndPropertyKeyword', 
                           'EndSequenceKeyword', 'EndCovergroupKeyword', 'CovergroupKeyword']:
                ck = ConstraintKeyword()
                ck.keyword = kind_name.replace('Keyword', '').lower()
                self.keywords.append(ck)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'keyword': k.keyword} for k in self.keywords[:50]]


def extract_constraint_property_keywords(code: str) -> List[Dict]:
    return ConstraintKeywordExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
constraint c1 { x > 5; }
property p1;
endproperty
sequence s1;
endsequence
'''
    result = extract_constraint_property_keywords(test_code)
    print(f"Constraint/Property/Sequence keywords: {len(result)}")
