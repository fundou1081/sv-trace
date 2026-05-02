"""
Parameter Declaration Parser - 使用正确的 AST 遍历

提取参数声明：
- ParameterDeclaration

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
class ParameterDeclaration:
    name: str = ""
    data_type: str = ""
    default_value: str = ""


class ParameterDeclarationExtractor:
    def __init__(self):
        self.parameters: List[ParameterDeclaration] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ParameterDeclaration':
                pd = ParameterDeclaration()
                if hasattr(node, 'name') and node.name:
                    pd.name = str(node.name)
                if hasattr(node, 'dataType') and node.dataType:
                    pd.data_type = str(node.dataType)[:30]
                if hasattr(node, 'defaultValue') and node.defaultValue:
                    pd.default_value = str(node.defaultValue)
                self.parameters.append(pd)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [
            {'name': p.name, 'type': p.data_type[:20], 'default': p.default_value[:20]}
            for p in self.parameters
        ]


def extract_parameters(code: str) -> List[Dict]:
    return ParameterDeclarationExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
module test #(
    parameter WIDTH = 8,
    parameter DEPTH = 16
);
endmodule
'''
    result = extract_parameters(test_code)
    print(f"Parameters: {len(result)}")
