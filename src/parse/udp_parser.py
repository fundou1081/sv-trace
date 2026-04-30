"""
UDP Parser - 使用 pyslang AST

支持:
- UdpDeclaration
- Udp ports (combotional, sequential)
- Udp body entries
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List
import pyslang
from pyslang import SyntaxKind


@dataclass
class UdpPort:
    """UDP 端口"""
    name: str = ""
    direction: str = ""  # input, output
    is_output: bool = False


@dataclass
class UdpEntry:
    """UDP table entry"""
    level: str = ""  # 0, 1, x
    next_level: str = ""
    condition: str = ""


@dataclass
class UdpDef:
    """UDP 定义"""
    name: str = ""
    is_sequential: bool = False
    ports: List[UdpPort] = field(default_factory=list)
    entries: List[UdpEntry] = field(default_factory=list)
    initial_value: str = ""


class UDPParser:
    def __init__(self, parser=None):
        self.parser = parser
        self.udps = []
        
        if parser:
            self._extract_all()
    
    def _extract_all(self):
        for key, tree in getattr(self.parser, 'trees', {}).items():
            root = tree.root if hasattr(tree, 'root') else tree
            self._extract_from_tree(root)
    
    def _extract_from_tree(self, root):
        def collect(node):
            kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            
            if kind_name == 'UdpDeclaration':
                self._extract_udp(node)
            
            return pyslang.VisitAction.Advance
        
        (root.root if hasattr(root, "root") else root).visit(collect)
    
    def _extract_udp(self, node):
        udp = UdpDef()
        
        # 名称
        if hasattr(node, 'name') and node.name:
            udp.name = str(node.name)
        
        # sequential UDP
        if hasattr(node, 'isSequential') and node.isSequential:
            udp.is_sequential = True
        
        # ports
        if hasattr(node, 'ports') and node.ports:
            for port in node.ports:
                if not port:
                    continue
                
                up = UdpPort()
                if hasattr(port, 'identifier'):
                    up.name = str(port.identifier)
                if hasattr(port, 'direction'):
                    up.direction = str(port.direction)
                
                # 最后一个端口是 output
                if hasattr(node, 'ports'):
                    ports_list = list(node.ports)
                    if port == ports_list[-1]:
                        up.is_output = True
                
                udp.ports.append(up)
        
        # entries (table entries)
        if hasattr(node, 'body') and node.body:
            node_str = str(node.body)
            # 简单解析 table entries
            for line in node_str.split('\n'):
                if line.strip() and ('0' in line or '1' in line or 'x' in line or 'X' in line):
                    entry = UdpEntry()
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        entry.level = parts[0]
                        entry.next_level = parts[1]
                    udp.entries.append(entry)
        
        # initial value
        if hasattr(node, 'initialValue') and node.initialValue:
            udp.initial_value = str(node.initialValue)
        
        self.udps.append(udp)
    
    def get_udps(self):
        return self.udps


def extract_udps(code):
    tree = pyslang.SyntaxTree.fromText(code)
    extractor = UDPParser(None)
    extractor._extract_from_tree(tree)
    return extractor.udps


if __name__ == "__main__":
    test_code = '''
module test;
    primitive mux_buf (y, a, b, sel);
    output y;
    input a, b, sel;
    
    table
        1 ? 0 : 0;
        0 ? 1 : 0;
        ? ? 1 : 1;
        0 0 0 : 0;
        1 1 1 : 1;
    endtable
    endprimitive
endmodule
'''
    
    result = extract_udps(test_code)
    print("=== UDP Extraction ===")
    for udp in result:
        print(f"{udp.name}: {len(udp.entries)} entries")
