"""
Implements Clause Parser - 使用正确的 AST 遍历

提取实现子句：
- ImplementsClause

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ImplementsClause:
    interface_names: List[str] = None
    
    def __post_init__(self):
        if self.interface_names is None:
            self.interface_names = []


class ImplementsClauseExtractor:
    def __init__(self):
        self.clauses: List[ImplementsClause] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ImplementsClause':
                ic = ImplementsClause()
                
                names = []
                def get_names(n):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'Name' in kn or 'Identifier' in kn:
                        names.append(str(n))
                    return pyslang.VisitAction.Advance
                node.visit(get_names)
                ic.interface_names = names[:10]
                
                self.clauses.append(ic)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'interfaces': c.interface_names[:5]} for c in self.clauses]


def extract_implements_clauses(code: str) -> List[Dict]:
    return ImplementsClauseExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
class my_class implements my_interface, another_interface;
endclass
'''
    result = extract_implements_clauses(test_code)
    print(f"Implements clauses: {len(result)}")
