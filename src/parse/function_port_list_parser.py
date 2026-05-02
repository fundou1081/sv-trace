"""
Function Port List Parser - 使用正确的 AST 遍历

提取函数端口列表：
- FunctionPortList

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class FunctionPortList:
    ports: List[Dict] = None
    
    def __post_init__(self):
        if self.ports is None:
            self.ports = []


class FunctionPortListExtractor:
    def __init__(self):
        self.lists: List[FunctionPortList] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'FunctionPortList':
                fpl = FunctionPortList()
                
                ports = []
                def get_ports(n):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'Port' in kn or 'Argument' in kn:
                        ports.append(str(n)[:30])
                    return pyslang.VisitAction.Advance
                node.visit(get_ports)
                fpl.ports = ports[:20]
                
                self.lists.append(fpl)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'count': len(l.ports)} for l in self.lists[:20]]


def extract_function_ports(code: str) -> List[Dict]:
    return FunctionPortListExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
function void my_func(input a, output b);
endfunction
'''
    result = extract_function_ports(test_code)
    print(f"Function port lists: {len(result)}")
