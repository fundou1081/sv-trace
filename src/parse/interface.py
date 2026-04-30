"""
Interface 解析器 - Interface/Modport/Clocking 完整实现 (v8 - 简化方案)
"""
import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, List, Optional
from dataclasses import dataclass, field
import pyslang
from pyslang import SyntaxKind, TokenKind


@dataclass
class ClockingItem:
    name: str = ""
    direction: str = ""
    skew: str = ""


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
        
        if node.header:
            iface.name = str(node.header.name.valueText) if node.header.name else ""
        
        for m in node.members:
            if not m:
                continue
            
            kind_name = m.kind.name
            
            if kind_name == 'ModportDeclaration':
                mp = self._extract_modport(m)
                if mp:
                    iface.modports.append(mp)
            
            elif kind_name == 'ClockingDeclaration':
                cb = self._extract_clocking(m)
                if cb:
                    iface.clockings.append(cb)
            
            else:
                decl = str(m).strip()
                if decl:
                    iface.signals.append(decl)
        
        if iface.name:
            self.interfaces[iface.name] = iface
        
        return iface
    
    def _extract_modport(self, node) -> Optional[ModportDef]:
        """简化提取: 从完整字符串解析"""
        mp = ModportDef()
        
        # 完整字符串，如 "modport master (output wdata, input ready);"
        full_str = str(node).strip()
        
        # 解析 modport 名称: modport NAME (
        match = re.search(r'modport\s+(\w+)\s*\(', full_str)
        if match:
            mp.name = match.group(1)
        
        # 解析端口: input/output NAME, ...
        # 先找到括号内容
        paren_match = re.search(r'\(([^)]+)\)', full_str)
        if paren_match:
            ports_str = paren_match.group(1)
            # 按逗号分割，但注意 array slice 如 [7:0]
            # 简化：按 "input" / "output" 分割
            parts = re.split(r',\s*(?=input\s|output\s)', ports_str)
            
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                
                # 判断方向
                direction = 'input'
                if part.startswith('output'):
                    direction = 'output'
                elif part.startswith('inout'):
                    direction = 'inout'
                
                # 提取信号名 (第一个 word)
                # 移除方向关键词后，第一个 word 是信号名
                sig_match = re.search(r'(?:input|output|inout|ref)\s+([\w\[\]:]+)', part)
                if sig_match:
                    sig = sig_match.group(1).strip()
                    # 清理
                    sig = re.sub(r'\[.*?\]', '', sig)  # 移除 [7:0] 等
                    sig = sig.strip()
                    
                    if sig:
                        mp.ports.append(ModportPort(name=sig, direction=direction))
        
        return mp if mp.name else None
    
    def _extract_clocking(self, node) -> Optional[ClockingDef]:
        cb = ClockingDef()
        
        full_str = str(node).strip()
        
        # 名称
        match = re.search(r'clocking\s+(\w+)', full_str)
        if match:
            cb.name = match.group(1)
        
        # 事件
        match = re.search(r'@(\([^)]+\))', full_str)
        if match:
            cb.event = '@' + match.group(1)
        
        # items
        match = re.search(r'endclocking', full_str)
        if match:
            # 找到 clocking ... endclocking 之间的内容
            start = full_str.find('clocking')
            end = full_str.find('endclocking')
            if start >= 0 and end > start:
                body = full_str[start:end]
                
                # 按 ';' 分割
                for item in body.split(';'):
                    item = item.strip()
                    if not item or 'input' not in item and 'output' not in item:
                        continue
                    
                    cbi = ClockingItem()
                    
                    # direction
                    if 'input' in item.split()[0]:
                        cbi.direction = 'input'
                    elif 'output' in item.split()[0]:
                        cbi.direction = 'output'
                    
                    # 名称 - 最后一个 word 或倒数第二个
                    words = item.split()
                    for i, w in enumerate(words):
                        if w in ['input', 'output']:
                            if i + 1 < len(words):
                                cbi.name = words[i+1].strip()
                                # 清理 array index
                                cbi.name = re.sub(r'\[.*?\]', '', cbi.name)
                                break
                    
                    # skew
                    if '#' in item:
                        skew_match = re.search(r'#(\w+)', item)
                        if skew_match:
                            cbi.skew = '#' + skew_match.group(1)
                    
                    if cbi.name:
                        cb.items.append(cbi)
        
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
        
        print(f"  modports: {len(iface.modports)}")
        for mp in iface.modports:
            print(f"    - {mp.name}")
            for p in mp.ports:
                print(f"        {p.direction}: {p.name}")
        
        print(f"  clockings: {len(iface.clockings)}")
        for cb in iface.clockings:
            print(f"    - {cb.name} @{cb.event}")
            for item in cb.items:
                print(f"        {item.direction} {item.name}")
