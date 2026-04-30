"""
Virtual Interface Parser - 使用 pyslang AST

支持:
- VirtualInterfaceVariable
- VirtualInterfaceType
- modport 在 interface 中的使用
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Optional
import pyslang
from pyslang import SyntaxKind


@dataclass
class VirtualInterface:
    """virtual interface"""
    name: str = ""
    interface_type: str = ""
    modport: str = ""


class VirtualInterfaceParser:
    def __init__(self, parser=None):
        self.parser = parser
        self.interfaces = []
        
        if parser:
            self._extract_all()
    
    def _extract_all(self):
        for key, tree in getattr(self.parser, 'trees', {}).items():
            root = tree.root if hasattr(tree, 'root') else tree
            self._extract_from_tree(root)
    
    def _extract_from_tree(self, root):
        def collect(node):
            kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            
            if kind_name in ['VirtualInterfaceVariable', 'VirtualInterfaceType']:
                self._extract_virtual(node)
            elif kind_name == 'InterfacePortHeader':
                self._extract_interface_port(node)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _extract_virtual(self, node):
        vif = VirtualInterface()
        
        # 名称
        if hasattr(node, 'identifier') and node.identifier:
            vif.name = str(node.identifier)
        
        # interface 类型
        if hasattr(node, 'interfaceType'):
            vif.interface_type = str(node.interfaceType)
        elif hasattr(node, 'type'):
            vif.interface_type = str(node.type)
        
        # modport
        if hasattr(node, 'modportClause'):
            vif.modport = str(node.modportClause)
        
        self.interfaces.append(vif)
    
    def _extract_interface_port(self, node):
        # interface port (如 input my_if)
        node_str = str(node)
        if 'virtual' in node_str.lower():
            pass  # 已经在 _extract_virtual 处理
    
    def get_interfaces(self):
        return self.interfaces


def extract_virtual_interfaces(code):
    tree = pyslang.SyntaxTree.fromText(code)
    parser = VirtualInterfaceParser(None)
    parser._extract_from_tree(tree)
    return parser.interfaces


if __name__ == "__main__":
    test_code = '''
module test;
    virtual interface my_if #(.PARAM(8)) vif();
    virtual my_if vif_i;
    
    initial begin
        vif.send();
    end
    
    modport test_mod(input clk, output data);
endmodule
'''
    
    result = extract_virtual_interfaces(test_code)
    print("=== Virtual Interfaces ===")
    for vif in result:
        print(f"  {vif.name}: {vif.interface_type}")
