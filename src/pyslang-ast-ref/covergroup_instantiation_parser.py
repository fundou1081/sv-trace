"""
Covergroup Instantiation Parser - 使用正确的 AST 遍历

提取覆盖组实例化：
- CovergroupInstantiation

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class CovergroupInstantiation:
    name: str = ""
    arguments: List[str] = None
    
    def __post_init__(self):
        if self.arguments is None:
            self.arguments = []


class CovergroupInstantiationExtractor:
    def __init__(self):
        self.instantiations: List[CovergroupInstantiation] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'CovergroupInstantiation':
                cgi = CovergroupInstantiation()
                
                if hasattr(node, 'name') and node.name:
                    cgi.name = str(node.name)
                
                args = []
                def get_args(n):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'Argument' in kn:
                        args.append(str(n)[:20])
                    return pyslang.VisitAction.Advance
                node.visit(get_args)
                cgi.arguments = args[:10]
                
                self.instantiations.append(cgi)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': i.name, 'args': len(i.arguments)} for i in self.instantiations]


def extract_covergroup_instantiations(code: str) -> List[Dict]:
    return CovergroupInstantiationExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
cg cg_inst();
'''
    result = extract_covergroup_instantiations(test_code)
    print(f"Covergroup instantiations: {len(result)}")
