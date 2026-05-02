"""
Standard Case Item Parser - 使用正确的 AST 遍历

提取 case 语句项：
- StandardCaseItem
- DefaultCaseItem

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class CaseItem:
    item_type: str = ""
    values: List[str] = None
    
    def __post_init__(self):
        if self.values is None:
            self.values = []


class StandardCaseItemExtractor:
    def __init__(self):
        self.items: List[CaseItem] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['StandardCaseItem', 'DefaultCaseItem', 'CaseInsideItem']:
                ci = CaseItem()
                ci.item_type = 'default' if 'Default' in kind_name else 'standard'
                
                values = []
                def get_values(n):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'Expression' in kn:
                        values.append(str(n)[:20])
                    return pyslang.VisitAction.Advance
                node.visit(get_values)
                ci.values = values[:10]
                
                self.items.append(ci)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'type': i.item_type, 'values': i.values[:5]} for i in self.items]


def extract_case_items(code: str) -> List[Dict]:
    return StandardCaseItemExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
case (sel)
    0: a = 1;
    default: a = 0;
endcase
'''
    result = extract_case_items(test_code)
    print(f"Case items: {len(result)}")
