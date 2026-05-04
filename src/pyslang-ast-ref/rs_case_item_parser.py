"""
RS Case Item Parser - 使用正确的 AST 遍历

提取随机约束 case 项：
- RsCase
- RsIfElse
- RsElseClause

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class RsCaseItem:
    case_type: str = ""
    condition: str = ""
    item: str = ""


class RsCaseItemExtractor:
    def __init__(self):
        self.items: List[RsCaseItem] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['RsCase', 'RsIfElse', 'RsElseClause',
                           'StandardRsCaseItem', 'DefaultRsCaseItem']:
                rci = RsCaseItem()
                rci.case_type = kind_name.replace('Rs', 'Random').replace('Case', '')
                
                if hasattr(node, 'condition') and node.condition:
                    rci.condition = str(node.condition)[:30]
                
                if hasattr(node, 'item') and node.item:
                    rci.item = str(node.item)[:30]
                
                self.items.append(rci)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'type': i.case_type, 'cond': i.condition[:25], 'item': i.item[:25]} for i in self.items[:20]]


def extract_rs_case_items(code: str) -> List[Dict]:
    return RsCaseItemExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
randcase
    1: x = 1;
    2: x = 2;
endcase
'''
    result = extract_rs_case_items(test_code)
    print(f"RS case items: {len(result)}")
