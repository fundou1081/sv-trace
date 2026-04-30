"""
Interface 解析器 - 使用 pyslang AST 提取

Interface/Modport/Clocking
"""
import sys
import os
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


def _collect_all_nodes(node):
    nodes = []
    def collect(n):
        nodes.append(n)
        return pyslang.VisitAction.Advance
    node.visit(collect)
    return nodes


def _get_token_kind(node):
    """获取 Token 的 kind 或 SyntaxKind"""
    if hasattr(node, 'kind'):
        return node.kind
    return None


class InterfaceExtractor:
    def __init__(self, parser=None):
        self.parser = parser
        self.interfaces = {}
        if parser:
            self._extract_all()
    
    def _extract_all(self):
        for key, tree in getattr(self.parser, 'trees', {}).items():
            if tree and hasattr(tree, 'root') and tree.root:
                self._extract_from_tree(tree)
    
    def _extract_from_tree(self, tree):
        # 支持 SyntaxTree 或 CompilationUnitSyntax
        root = tree.root if hasattr(tree, 'root') else root
        
        def collect(node):
            if node.kind == SyntaxKind.InterfaceDeclaration:
                self._extract_interface(node)
            return pyslang.VisitAction.Advance
        root.visit(collect)
    
    def _extract_interface(self, node):
        iface = InterfaceDef()
        if node.header and node.header.name:
            iface.name = str(node.header.name.valueText)
        
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
    
    def _extract_modport(self, node):
        mp = ModportDef()
        
        # 收集所有子节点
        all_nodes = _collect_all_nodes(node)
        
        # 用字符串位置逻辑
        str_repr = str(node)
        items = []
        
        # 找到 modport 名称
        # 模式: modport NAME (
        import re
        m = re.search(r'modport\s+(\w+)\s*\(', str_repr)
        if m:
            mp.name = m.group(1)
        
        # 端口: 分析 tokens
        for i, n in enumerate(all_nodes):
            s = str(n).strip()
            
            # 方向
            if 'output' in s.lower():
                current_dir = 'output'
            elif 'input' in s.lower():
                current_dir = 'input'
            
            # ModportNamedPort 包含端口名
            elif _get_token_kind(n) == SyntaxKind.ModportNamedPort:
                for child in n:
                    cs = str(child).strip()
                    if cs and cs not in ['output', 'input', 'inout']:
                        mp.ports.append(ModportPort(name=cs, direction=current_dir))
                        break
        
        return mp if mp.name else None
    
    def _extract_clocking(self, node):
        cb = ClockingDef()
        
        str_repr = str(node)
        
        # 名称
        import re
        m = re.search(r'clocking\s+(\w+)', str_repr)
        if m:
            cb.name = m.group(1)
        
        # 事件
        m = re.search(r'@(\([^)]+\))', str_repr)
        if m:
            cb.event = '@' + m.group(1)
        
        # 端口 - 简化: 从 str 提取
        # 模式: input/output NAME
        for match in re.finditer(r'(input|output)\s+(\w+)', str_repr):
            direction = match.group(1)
            name = match.group(2)
            # 清理 #1step 等
            name = re.sub(r'#\w+', '', name).strip()
            if name:
                cb.items.append(ClockingItem(name=name, direction=direction))
        
        return cb if cb.name else None
    
    def get_interfaces(self):
        return self.interfaces


def extract_interfaces(code):
    tree = pyslang.SyntaxTree.fromText(code)
    extractor = InterfaceExtractor(None)
    extractor._extract_from_tree(tree)
    return extractor.interfaces


if __name__ == "__main__":
    test_code = '''interface axi_if (input clk);
    logic [31:0] wdata;
    logic ready;
    
    modport master (output wdata, input ready);
    clocking cb @(posedge clk);
        input ready;
    endclocking
endinterface'''
    
    result = extract_interfaces(test_code)
    print("=== Interface ===")
    for name, iface in result.items():
        print(f"\nInterface: {name}")
        print(f"  modports: {len(iface.modports)}")
        for mp in iface.modports:
            print(f"    - {mp.name}")
            for p in mp.ports:
                print(f"        {p.direction}: {p.name}")
        print(f"  clockings: {len(iface.clockings)}")
        for cb in iface.clockings:
            print(f"    - {cb.name}")
            if cb.event:
                print(f"      event: {cb.event}")
            for item in cb.items:
                print(f"        {item.direction} {item.name}")
