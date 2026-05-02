"""
Function Port Parser - 使用正确的 AST 遍历

提取函数/任务端口：
- FunctionPort
- FunctionPortList
- FunctionPrototype

注意：此文件不包含任何正则表达式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict
import pyslang
from pyslang import SyntaxKind


@dataclass
class FunctionPort:
    name: str = ""
    direction: str = ""  # input, output, inout, ref
    data_type: str = ""
    width: str = ""


@dataclass
class FunctionPrototype:
    name: str = ""
    return_type: str = ""
    ports: List[FunctionPort] = field(default_factory=list)


class FunctionPortExtractor:
    def __init__(self):
        self.prototypes: List[FunctionPrototype] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'FunctionPrototype':
                fp = FunctionPrototype()
                if hasattr(node, 'name') and node.name:
                    fp.name = str(node.name)
                if hasattr(node, 'returnType') and node.returnType:
                    fp.return_type = str(node.returnType)[:30]
                
                # FunctionPortList
                if hasattr(node, 'ports') and node.ports:
                    for port in node.ports:
                        fp.ports.append(self._extract_port(port))
                
                self.prototypes.append(fp)
            
            elif kind_name == 'FunctionPort':
                fp = FunctionPrototype()
                fp.ports.append(self._extract_port(node))
                self.prototypes.append(fp)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _extract_port(self, node) -> FunctionPort:
        p = FunctionPort()
        if hasattr(node, 'name') and node.name:
            p.name = str(node.name)
        if hasattr(node, 'direction') and node.direction:
            p.direction = str(node.direction).lower()
        if hasattr(node, 'dataType') and node.dataType:
            p.data_type = str(node.dataType)[:30]
        return p
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [
            {
                'name': fp.name,
                'return_type': fp.return_type,
                'ports': [{'name': p.name, 'dir': p.direction} for p in fp.ports]
            }
            for fp in self.prototypes
        ]


def extract_function_ports(code: str) -> List[Dict]:
    return FunctionPortExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
function automatic int my_func(input [7:0] a, output [7:0] b);
endfunction
'''
    result = extract_function_ports(test_code)
    print(f"Function prototypes: {len(result)}")
