"""
Interface 解析器 - Interface/Modport/Clocking 提取
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, List, Optional
from dataclasses import dataclass, field
import pyslang
from pyslang import SyntaxKind


@dataclass
class ClockingItem:
    name: str = ""
    direction: str = ""


@dataclass
class ClockingDef:
    name: str = ""
    event: str = ""
    items: List[ClockingItem] = field(default_factory=list)


@dataclass
class ModportPort:
    name: str = ""
    direction: str = ""


@dataclass
class ModportDef:
    name: str = ""
    ports: List[ModportPort] = field(default_factory=list)


@dataclass
class InterfaceDef:
    name: str = ""
    signals: List[str] = field(default_factory=list)
    modports: List[ModportDef] = field(default_factory=list)
    clockings: List[ClockingDef] = field(default_factory=list)


class InterfaceExtractor:
    def __init__(self, parser=None):
        self.parser = parser
        self.interfaces: Dict[str, InterfaceDef] = {}
        if parser:
            self._extract_all()
    
    def _extract_all(self):
        for key, tree in getattr(self.parser, 'trees', {}).items():
            if tree and hasattr(tree, 'root') and tree.root:
                self._extract_from_tree(tree)
    
    def _extract_from_tree(self, tree):
        def collect(node):
            if node.kind == SyntaxKind.InterfaceDeclaration:
                self._extract_interface(node)
            return pyslang.VisitAction.Advance
        
        tree.root.visit(collect)
    
    def _extract_interface(self, node) -> InterfaceDef:
        iface = InterfaceDef()
        
        # name from header
        if hasattr(node, 'header') and node.header:
            iface.name = str(node.header.name.valueText) if hasattr(node.header, 'name') else str(node.header)
        
        # members
        if hasattr(node, 'members') and node.members:
            for child in node.members:
                if not child:
                    continue
                kind_name = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
                
                if kind_name == 'ModportDeclaration':
                    mp = self._extract_modport(child)
                    if mp:
                        iface.modports.append(mp)
                elif kind_name == 'ClockingDeclaration':
                    cb = self._extract_clocking(child)
                    if cb:
                        iface.clockings.append(cb)
                elif 'Declaration' in kind_name:
                    decl = str(child).strip()
                    if decl:
                        iface.signals.append(decl)
        
        if iface.name:
            self.interfaces[iface.name] = iface
        return iface
    
    def _extract_modport(self, node) -> Optional[ModportDef]:
        mp = ModportDef()
        mp.name = str(node).strip().split('(')[0].strip() if node else ""
        
        # 简化：从 ModportItem 提取
        def find_ports(n, direction='input'):
            ports = []
            n.visit(lambda ch:
                (lambda k=ch.kind.name: (
                    ports.append(ModportPort(name=str(ch).strip(), direction='output'))
                    if 'Output' in k else (
                    ports.append(ModportPort(name=str(ch).strip(), direction='input'))
                    if 'Input' in k else None
                    )
                ) or pyslang.VisitAction.Advance) if 'Keyword' in k else pyslang.VisitAction.Advance
            )
            return ports
        
        # 遍历 ModportDeclaration 的子节点找 ModportExplicitPort
        for child in node:
            if 'ModportExplicitPort' in str(child.kind):
                direction = 'input'
                if hasattr(child, 'direction') and child.direction:
                    if 'Output' in str(child.direction.kind):
                        direction = 'output'
                name = str(child.port.name).strip() if hasattr(child, 'port') and hasattr(child.port, 'name') else str(child).strip()
                mp.ports.append(ModportPort(name=name, direction=direction))
        
        return mp if mp.name else None
    
    def _extract_clocking(self, node) -> Optional[ClockingDef]:
        cb = ClockingDef()
        cb.event = str(node.clockingEvent).strip() if hasattr(node, 'clockingEvent') and node.clockingEvent else ""
        
        cb.name = str(node).strip().split('(')[0].strip() if node else ""
        
        return cb if cb.name else None
    
    def get_interfaces(self) -> Dict[str, InterfaceDef]:
        return self.interfaces


def extract_interfaces(code: str) -> Dict[str, InterfaceDef]:
    tree = pyslang.SyntaxTree.fromText(code)
    extractor = InterfaceExtractor(None)
    extractor._extract_from_tree(tree)
    return extractor.interfaces


if __name__ == "__main__":
    test_code = '''
interface axi_if (input clk, input rst);
    logic [31:0] wdata;
    logic [31:0] rdata;
    logic valid;
    logic ready;
    
    modport master (
        input clk, rst, rdata, ready,
        output wdata, valid
    );
    
    modport slave (
        input clk, rst, wdata, valid,
        output rdata, ready
    );
    
    clocking cb @(posedge clk);
        input #1step rdata, ready;
        output #0 wdata, valid;
    endclocking
endinterface
'''
    
    result = extract_interfaces(test_code)
    print("=== Interface 提取测试 ===")
    for name, iface in result.items():
        print(f"\nInterface: {name}")
        print(f"  signals: {len(iface.signals)}")
        for s in iface.signals[:3]:
            print(f"    {s}")
        
        print(f"  modports: {len(iface.modports)}")
        for mp in iface.modports:
            print(f"    - {mp.name}")
        
        print(f"  clockings: {len(iface.clockings)}")
        for cb in iface.clockings:
            print(f"    - {cb.name} @{cb.event}")
