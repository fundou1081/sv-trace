"""
Module Header Parser - 使用正确的 AST 遍历

提取模块头信息：
- ModuleHeader
- ModuleDeclaration 的头部信息

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
class ModuleHeader:
    name: str = ""
    parameters: List[str] = field(default_factory=list)
    ports: List[str] = field(default_factory=list)
    is_interface: bool = False
    is_program: bool = False


class ModuleHeaderExtractor:
    def __init__(self):
        self.headers: List[ModuleHeader] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ModuleHeader':
                mh = self._extract_module_header(node)
                if mh:
                    self.headers.append(mh)
            
            elif kind_name == 'InterfaceHeader':
                mh = ModuleHeader()
                mh.is_interface = True
                if hasattr(node, 'name') and node.name:
                    mh.name = str(node.name)
                self.headers.append(mh)
            
            elif kind_name == 'ProgramHeader':
                mh = ModuleHeader()
                mh.is_program = True
                if hasattr(node, 'name') and node.name:
                    mh.name = str(node.name)
                self.headers.append(mh)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _extract_module_header(self, node) -> Optional[ModuleHeader]:
        mh = ModuleHeader()
        
        if hasattr(node, 'name') and node.name:
            mh.name = str(node.name)
        
        # 遍历子节点提取参数和端口
        for child in node:
            if not child:
                continue
            try:
                child_kind = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            except:
                continue
            
            if child_kind in ['ParameterDeclaration', 'LocalParameterDeclaration']:
                if hasattr(child, 'name') and child.name:
                    mh.parameters.append(str(child.name))
            
            elif child_kind in ['AnsiPortList', 'NonAnsiPortList', 'PortList']:
                for port in child:
                    if hasattr(port, 'name') and port.name:
                        mh.ports.append(str(port.name))
            
            elif child_kind == 'AnsiPortDeclaration':
                if hasattr(child, 'name') and child.name:
                    mh.ports.append(str(child.name))
        
        return mh if mh.name else None
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [
            {
                'name': mh.name,
                'is_interface': mh.is_interface,
                'is_program': mh.is_program,
                'params': mh.parameters,
                'ports': mh.ports,
                'port_count': len(mh.ports)
            }
            for mh in self.headers
        ]


def extract_module_headers(code: str) -> List[Dict]:
    return ModuleHeaderExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
module test #(
    parameter WIDTH = 8
) (
    input clk,
    input [7:0] data,
    output [7:0] q
);

interface my_if;
endinterface

endmodule
'''
    result = extract_module_headers(test_code)
    for r in result:
        print(f"Module: {r['name']}, ports: {r['port_count']}")
