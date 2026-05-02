"""
Sequence and Property Parsers - 使用正确的 AST 遍历

提取：
- SequenceMatchItem (序列匹配项)
- PropertyCaseItem (属性分支)

注意：此文件不包含任何正则表达式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import pyslang
from pyslang import SyntaxKind


@dataclass
class SequenceMatchItem:
    """序列匹配项"""
    kind: str = ""  # and, or, etc.
    expression: str = ""


@dataclass
class PropertyCaseItem:
    """属性分支"""
    condition: str = ""
    action: str = ""


class SequencePropertyExtractor:
    def __init__(self):
        self.sequence_match_items: List[SequenceMatchItem] = []
        self.property_case_items: List[PropertyCaseItem] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'SequenceMatchItem':
                smi = SequenceMatchItem()
                smi.kind = 'match_item'
                if hasattr(node, 'left') and node.left:
                    smi.expression = str(node.left)
                self.sequence_match_items.append(smi)
            
            elif kind_name == 'PropertyCaseItem':
                pci = PropertyCaseItem()
                if hasattr(node, 'condition') and node.condition:
                    pci.condition = str(node.condition)
                if hasattr(node, 'action') and node.action:
                    pci.action = str(node.action)
                self.property_case_items.append(pci)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> Dict:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return {
            'sequence_match_items': len(self.sequence_match_items),
            'property_case_items': [
                {'condition': pci.condition[:40], 'action': pci.action[:40]}
                for pci in self.property_case_items
            ]
        }


def extract_sequence_property(code: str) -> Dict:
    return SequencePropertyExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
sequence s1;
    a ##1 b ##1 c;
endsequence

property p1;
    casez (state)
        2'b00: accept_on (cond);
        2'b01: reject;
        default: endproperty
'''
    result = extract_sequence_property(test_code)
    print(f"SequenceMatchItem: {result['sequence_match_items']}")
    print(f"PropertyCaseItem: {len(result['property_case_items'])}")
