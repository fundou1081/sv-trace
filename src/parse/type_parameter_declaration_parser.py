"""
Type Parameter Declaration Parser - 使用正确的 AST 遍历

提取类型参数声明：
- TypeParameterDeclaration

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class TypeParameterDeclaration:
    name: str = ""
    default_type: str = ""


class TypeParameterDeclarationExtractor:
    def __init__(self):
        self.parameters: List[TypeParameterDeclaration] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'TypeParameterDeclaration':
                tpd = TypeParameterDeclaration()
                
                if hasattr(node, 'name') and node.name:
                    tpd.name = str(node.name)
                
                if hasattr(node, 'defaultType') and node.defaultType:
                    tpd.default_type = str(node.defaultType)[:30]
                
                self.parameters.append(tpd)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': p.name, 'default': p.default_type[:25]} for p in self.parameters]


def extract_type_parameters(code: str) -> List[Dict]:
    return TypeParameterDeclarationExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
module m #(
    type T = int
);
endmodule
'''
    result = extract_type_parameters(test_code)
    print(f"Type parameters: {len(result)}")
