"""
Interface Parser - 使用正确的 AST 遍历

接口提取

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
class InterfacePort:
    name: str = ""
    direction: str = ""  # input, output, inout


@dataclass
class InterfaceDef:
    name: str = ""
    ports: List[InterfacePort] = field(default_factory=list)
    modports: List[str] = field(default_factory=list)


class InterfaceExtractor:
    """提取接口定义"""
    
    def __init__(self):
        self.interfaces: List[InterfaceDef] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'InterfaceDeclaration':
                interface = InterfaceDef()
                if hasattr(node, 'name') and node.name:
                    interface.name = str(node.name)
                
                # 提取端口
                for child in node:
                    if not child:
                        continue
                    try:
                        child_kind = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
                    except:
                        continue
                    
                    # 端口声明
                    if child_kind in ['InterfacePortHeader', 'AnsiPortList', 'NonAnsiPortList']:
                        port = InterfacePort()
                        if hasattr(child, 'name') and child.name:
                            port.name = str(child.name)
                        if hasattr(child, 'direction'):
                            port.direction = str(child.direction)
                        if port.name:
                            interface.ports.append(port)
                    
                    # Modport 声明
                    elif child_kind == 'ModportDeclaration':
                        if hasattr(child, 'items') and child.items:
                            for m in child.items:
                                if hasattr(m, 'name') and m.name:
                                    interface.modports.append(str(m.name))
                
                if interface.name:
                    self.interfaces.append(interface)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [
            {
                'name': i.name,
                'ports': [{'name': p.name, 'direction': p.direction} for p in i.ports],
                'modports': i.modports
            }
            for i in self.interfaces
        ]


def extract_interfaces(code: str) -> List[Dict]:
    return InterfaceExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
interface arb_if (input clk, input rst);
    logic [7:0] data;
    modport master (input data);
    modport slave (output data);
endinterface
'''
    result = extract_interfaces(test_code)
    print(result)
