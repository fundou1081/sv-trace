"""
Pattern Case Item Parser - 使用正确的 AST 遍历

提取模式 case 项：
- PatternCaseItem

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class PatternCaseItem:
    pattern: str = ""
    statement: str = ""


class PatternCaseItemExtractor:
    def __init__(self):
        self.items: List[PatternCaseItem] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'PatternCaseItem':
                pci = PatternCaseItem()
                
                if hasattr(node, 'pattern') and node.pattern:
                    pci.pattern = str(node.pattern)[:30]
                
                if hasattr(node, 'statement') and node.statement:
                    pci.statement = str(node.statement)[:30]
                
                self.items.append(pci)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'pattern': i.pattern[:25], 'stmt': i.statement[:25]} for i in self.items]


def extract_pattern_case_items(code: str) -> List[Dict]:
    return PatternCaseItemExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
case (sel) match
    '{"a}: b = 1;
endcase
'''
    result = extract_pattern_case_items(test_code)
    print(f"Pattern case items: {len(result)}")
