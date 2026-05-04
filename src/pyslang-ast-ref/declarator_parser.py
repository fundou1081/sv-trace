"""
Declarator Parser - 使用正确的 AST 遍历

提取变量声明器：
- Declarator
- VariableDeclarator
- NetDeclarator

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
class Declarator:
    name: str = ""
    dimensions: List[str] = field(default_factory=list)
    init_value: str = ""


class DeclaratorExtractor:
    def __init__(self):
        self.declarators: List[Declarator] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['Declarator', 'VariableDeclarator', 'NetDeclarator']:
                d = self._extract_declarator(node)
                if d:
                    self.declarators.append(d)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _extract_declarator(self, node) -> Optional[Declarator]:
        d = Declarator()
        
        if hasattr(node, 'name') and node.name:
            d.name = str(node.name)
        
        # 提取维度
        if hasattr(node, 'dimensions') and node.dimensions:
            for dim in node.dimensions:
                d.dimensions.append(str(dim))
        
        # 提取初始化值
        if hasattr(node, 'initializer') and node.initializer:
            d.init_value = str(node.initializer)[:50]
        elif hasattr(node, 'value') and node.value:
            d.init_value = str(node.value)[:50]
        
        return d if d.name else None
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [
            {
                'name': d.name,
                'dims': d.dimensions,
                'init': d.init_value[:30]
            }
            for d in self.declarators[:30]
        ]


def extract_declarators(code: str) -> List[Dict]:
    return DeclaratorExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
module test;
    logic [7:0] a, b, c;
    logic [15:0] arr [0:3];
    logic [7:0] x = 8'hFF;
endmodule
'''
    result = extract_declarators(test_code)
    print(f"Declarators: {len(result)}")
    for r in result[:5]:
        print(f"  {r['name']}: dims={r['dims']}")
