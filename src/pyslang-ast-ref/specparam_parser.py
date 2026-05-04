"""
Specparam Parser - 使用正确的 AST 遍历

提取规范参数：
- SpecparamKeyword
- SpecparamDeclarator

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class Specparam:
    name: str = ""
    value: str = ""


class SpecparamExtractor:
    def __init__(self):
        self.params: List[Specparam] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['SpecparamDeclaration', 'SpecparamDeclarator']:
                sp = Specparam()
                if hasattr(node, 'name') and node.name:
                    sp.name = str(node.name)[:30]
                if hasattr(node, 'value') and node.value:
                    sp.value = str(node.value)[:20]
                self.params.append(sp)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': p.name[:25], 'value': p.value[:15]} for p in self.params[:20]]


def extract_specparams(code: str) -> List[Dict]:
    return SpecparamExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
specify
    specparam t_rise = 1ns;
endspecify
'''
    result = extract_specparams(test_code)
    print(f"Specparams: {len(result)}")
