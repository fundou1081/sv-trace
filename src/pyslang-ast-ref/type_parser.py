"""
Type Parser - 使用正确的 AST 遍历

提取类型声明：
- NamedType
- ImplicitType
- StringType
- LogicType
- RegType
- IntegerLiteralExpression
- VariableDimension
- RangeDimensionSpecifier

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
class TypeInfo:
    type_name: str = ""
    kind: str = ""  # named, implicit, string, logic, reg, etc.
    width: str = ""


class TypeExtractor:
    def __init__(self):
        self.types: List[TypeInfo] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['NamedType', 'ImplicitType', 'StringType', 
                            'LogicType', 'RegType', 'IntegerLiteralExpression',
                            'VariableDimension', 'RangeDimensionSpecifier']:
                t = TypeInfo()
                t.kind = kind_name
                
                if hasattr(node, 'name') and node.name:
                    t.type_name = str(node.name)
                elif hasattr(node, 'keyword') and node.keyword:
                    t.type_name = str(node.keyword)
                
                if t.type_name or t.kind:
                    self.types.append(t)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [
            {'kind': t.kind, 'name': t.type_name[:30]}
            for t in self.types[:20]
        ]


def extract_types(code: str) -> List[Dict]:
    return TypeExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
module test;
    logic [7:0] a;
    bit [3:0] b;
    string s;
    integer i;
endmodule
'''
    result = extract_types(test_code)
    print(f"Types: {len(result)}")
