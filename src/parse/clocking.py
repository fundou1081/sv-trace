"""
Clocking Block Parser - 使用 pyslang AST

支持:
- ClockingDeclaration (clocking ... endclocking)
- ClockingItem (input/output in clocking block)
- Default clocking skew
- ModportDeclaration (modport ... endmodport)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import pyslang
from pyslang import SyntaxKind
import re


@dataclass
class ClockingItem:
    """clocking block 中的信号项"""
    name: str = ""
    direction: str = ""  # input, output, inout
    skew: str = ""  # 如 #2 表示延迟


@dataclass
class ClockingBlock:
    """clocking block 定义"""
    name: str = ""
    event: str = ""  # @(posedge clk) 或类似
    items: List[ClockingItem] = field(default_factory=list)
    default_input_skew: str = ""
    default_output_skew: str = ""


class ClockingExtractor:
    """从 SystemVerilog 代码中提取 clocking 块"""
    
    def __init__(self, parser=None):
        self.parser = parser
        self.clockings: Dict[str, ClockingBlock] = {}
    
    def _extract_from_tree(self, root) -> Dict[str, ClockingBlock]:
        self.clockings = {}
        
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ClockingDeclaration':
                self._extract_clock(node)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
        return self.clockings
    
    def _extract_clock(self, node):
        """提取单个 clocking 块"""
        clk = ClockingBlock()
        
        # 名称
        if hasattr(node, 'blockName') and node.blockName:
            clk.name = str(node.blockName).strip()
        
        # clocking event
        if hasattr(node, 'event') and node.event:
            event_str = str(node.event).strip()
            if event_str.startswith('@'):
                clk.event = event_str
            elif event_str.startswith('(') and event_str.endswith(')'):
                clk.event = '@' + event_str
            else:
                clk.event = '@' + event_str if event_str else "@*"
        
        # 解析 items
        if hasattr(node, 'items') and node.items:
            items_str = str(node.items).strip()
            
            # 按分号分割，每行独立处理
            lines = items_str.split(';')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 跳过空行和注释
                if line.startswith('//') or line.startswith('/*'):
                    continue
                
                # 处理 default skew 行
                if line.startswith('default'):
                    default_input_match = re.search(r'default\s+input\s+#([^\s]+)', line)
                    default_output_match = re.search(r'default\s+output\s+#([^\s]+)', line)
                    if default_input_match:
                        clk.default_input_skew = "#" + default_input_match.group(1)
                    if default_output_match:
                        clk.default_output_skew = "#" + default_output_match.group(1)
                    continue
                
                # 处理 input/output 行
                dir_match = re.match(r'(input|output|inout)(?:\s+#([^\s,;]+))?', line)
                if dir_match:
                    direction = dir_match.group(1)
                    skew = dir_match.group(2)
                    if skew:
                        skew = "#" + skew
                    
                    # 提取信号名
                    signals_str = line[dir_match.end():].strip().lstrip(',').strip()
                    
                    for signal in signals_str.split(','):
                        signal = signal.strip()
                        if not signal:
                            continue
                        
                        signal_match = re.match(r'(#\d+)?\s*([a-zA-Z_][a-zA-Z0-9_]*)', signal)
                        if signal_match:
                            signal_skew = signal_match.group(1)
                            signal_name = signal_match.group(2)
                            
                            if signal_name and signal_name.lower() not in ['default', 'input', 'output']:
                                item = ClockingItem()
                                item.name = signal_name
                                item.direction = direction
                                if signal_skew:
                                    item.skew = signal_skew
                                elif skew:
                                    item.skew = skew
                                clk.items.append(item)
        
        if clk.name:
            self.clockings[clk.name] = clk
    
    def extract_from_text(self, code: str, source: str = "<text>") -> Dict[str, ClockingBlock]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        return self._extract_from_tree(tree.root)
    
    def get_clockings(self) -> Dict[str, ClockingBlock]:
        return self.clockings


class ModportExtractor:
    """从 SystemVerilog 代码中提取 modport 声明"""
    
    def __init__(self, parser=None):
        self.parser = parser
        self.modports: Dict[str, List[str]] = {}
    
    def _extract_from_tree(self, root) -> Dict[str, List[str]]:
        self.modports = {}
        
        # 先收集所有 interface 和 modport
        interfaces = []  # [(name, node, sourceRange)]
        modport_nodes = []  # [(node, sourceRange)]
        
        def collect_interfaces(node):
            kind = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            if kind == 'InterfaceDeclaration':
                name = ""
                if hasattr(node, 'name') and node.name:
                    name = str(node.name).strip()
                elif hasattr(node, 'header') and node.header:
                    if hasattr(node.header, 'name') and node.header.name:
                        name = str(node.header.name).strip()
                rng = getattr(node, 'sourceRange', None)
                interfaces.append((name, node, rng))
            elif kind == 'ModportDeclaration':
                rng = getattr(node, 'sourceRange', None)
                modport_nodes.append((node, rng))
            return pyslang.VisitAction.Advance
        
        root.visit(collect_interfaces)
        
        # 为每个 modport 找到对应的 interface
        for modport_node, modport_range in modport_nodes:
            # 找到最后一个开始位置小于此 modport 的 interface
            assigned_interface = "unknown"
            if modport_range and interfaces:
                for iface_name, iface_node, iface_range in reversed(interfaces):
                    if iface_range and modport_range:
                        if iface_range.start.offset < modport_range.start.offset:
                            assigned_interface = iface_name
                            break
                # 如果没找到范围比较，用最后一个 interface
                if assigned_interface == "unknown" and interfaces:
                    assigned_interface = interfaces[-1][0]
            
            # 提取 modport 名称
            if hasattr(modport_node, 'items') and modport_node.items:
                for item in modport_node.items:
                    if not item:
                        continue
                    item_str = str(item).strip()
                    match = re.match(r'(\w+)\s*\(([^)]*)\)', item_str)
                    if match:
                        mp_name = match.group(1).strip()
                        if mp_name not in ['input', 'output', 'inout', 'logic', 'wire', 'reg']:
                            if assigned_interface not in self.modports:
                                self.modports[assigned_interface] = []
                            if mp_name not in self.modports[assigned_interface]:
                                self.modports[assigned_interface].append(mp_name)
        
        return self.modports
    
    def extract_from_text(self, code: str, source: str = "<text>") -> Dict[str, List[str]]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        return self._extract_from_tree(tree.root)
    
    def get_modports(self) -> Dict[str, List[str]]:
        return self.modports


def extract_clockings(code: str) -> Dict[str, Dict]:
    """从 SystemVerilog 代码提取 clocking 块"""
    extractor = ClockingExtractor()
    clockings = extractor.extract_from_text(code)
    
    return {
        name: {
            'name': clk.name,
            'event': clk.event,
            'items': [
                {'name': i.name, 'direction': i.direction, 'skew': i.skew}
                for i in clk.items
            ],
            'default_input_skew': clk.default_input_skew,
            'default_output_skew': clk.default_output_skew,
            'item_count': len(clk.items)
        }
        for name, clk in clockings.items()
    }


def extract_modports(code: str) -> Dict[str, List[str]]:
    """从 SystemVerilog 代码提取 modport 声明"""
    extractor = ModportExtractor()
    return extractor.extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
interface arb_if (input clk, rst);
    logic grant;
    logic request;
    
    modport master (
        input request,
        output grant
    );
    
    modport slave (
        input grant,
        output request
    );
endinterface

module test;
    clocking cb @(posedge clk);
        default input #1step output #0;
        input data, valid;
        output ready;
        input #2 ack;
    endclocking
endmodule
'''
    
    print("=== Clocking/Modport Extraction ===\n")
    
    print("--- extract_clockings ---")
    clockings = extract_clockings(test_code)
    print(f"Found {len(clockings)} clocking blocks")
    for name, clk in clockings.items():
        print(f"\n{name}:")
        print(f"  event: {clk['event']}")
        print(f"  default skew: in={clk['default_input_skew']}, out={clk['default_output_skew']}")
        print(f"  items: {clk['item_count']}")
        for item in clk['items']:
            skew_str = f" (skew={item['skew']})" if item['skew'] else ""
            print(f"    - {item['name']}: {item['direction']}{skew_str}")
    
    print("\n--- extract_modports ---")
    modports = extract_modports(test_code)
    print(f"Found {len(modports)} interfaces with modports")
    for iface, mps in modports.items():
        print(f"  {iface}: {mps}")
