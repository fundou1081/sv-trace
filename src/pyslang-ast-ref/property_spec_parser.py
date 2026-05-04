"""
Property Spec Parser - 使用正确的 AST 遍历

提取属性规格：
- PropertySpec

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
class PropertySpec:
    expression: str = ""
    clock: str = ""


class PropertySpecExtractor:
    def __init__(self):
        self.specs: List[PropertySpec] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'PropertySpec':
                ps = PropertySpec()
                if hasattr(node, 'property') and node.property:
                    ps.expression = str(node.property)
                elif hasattr(node, 'expression') and node.expression:
                    ps.expression = str(node.expression)
                
                if hasattr(node, 'clock') and node.clock:
                    ps.clock = str(node.clock)
                
                self.specs.append(ps)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'expr': s.expression[:40], 'clock': s.clock[:30]} for s in self.specs]


def extract_property_specs(code: str) -> List[Dict]:
    return PropertySpecExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
property p1;
    @(posedge clk) a |-> b;
endproperty
'''
    result = extract_property_specs(test_code)
    print(f"Property specs: {len(result)}")
