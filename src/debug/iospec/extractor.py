"""
IOSpecExtractor - Module IO 规范提取器
"""
import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class PortDirection(Enum):
    INPUT = "input"
    OUTPUT = "output"
    INOUT = "inout"


class SignalCategory(Enum):
    CLOCK = "clock"
    RESET = "reset"
    CONTROL = "control"
    DATA = "data"
    OTHER = "other"


@dataclass
class BitUsage:
    bit_index: int
    usage: str
    consistent: bool = True


@dataclass
class Port:
    name: str
    direction: PortDirection
    width: int = 1
    bits: List[BitUsage] = field(default_factory=list)
    category: SignalCategory = SignalCategory.OTHER
    code_location: Optional[Dict] = None
    
    def __post_init__(self):
        if not self.bits:
            self.bits = [BitUsage(bit_index=i, usage="data") for i in range(self.width)]


@dataclass
class IOSpec:
    module_name: str
    parameters: Dict[str, str] = field(default_factory=dict)
    ports: List[Port] = field(default_factory=list)
    data_flows: List[Dict] = field(default_factory=list)


class IOSpecExtractor:
    """IO 规范提取器 - Phase 1-3"""
    
    def __init__(self, parser):
        self.parser = parser
    
    def extract(self, module_name: str = None) -> IOSpec:
        spec = IOSpec(module_name=module_name or "unknown")
        
        for tree in self.parser.trees.values():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            root = tree.root
            if not hasattr(root, 'members'):
                continue
            
            for i in range(len(root.members)):
                member = root.members[i]
                
                if 'ModuleDeclaration' not in str(type(member)):
                    continue
                
                # 模块名
                if hasattr(member, 'header') and member.header:
                    h = member.header
                    name = h.name.value if hasattr(h.name, 'value') else str(h.name)
                    if module_name and name != module_name:
                        continue
                    spec.module_name = name
                
                # 端口
                ports = self._extract_ports(member)
                spec.ports.extend(ports)
        
        # 分类
        self._categorize_ports(spec.ports)
        
        # 数据流
        self._trace_data_flow(spec)
        
        return spec
    
    def _extract_ports(self, module) -> List[Port]:
        ports = []
        
        if not hasattr(module, 'header') or not module.header:
            return ports
        
        h = module.header
        if not hasattr(h, 'ports') or not h.ports:
            return ports
        
        # h.ports is ( , port_list, )
        port_list = h.ports[1] if len(h.ports) > 1 else None
        if not port_list:
            return ports
        
        for item in port_list:
            if 'ImplicitAnsiPortSyntax' not in str(type(item)):
                continue
            
            # 名称
            name = ""
            if hasattr(item, 'declarator') and item.declarator:
                if hasattr(item.declarator, 'name'):
                    name = item.declarator.name.value if hasattr(item.declarator.name, 'value') else str(item.declarator.name)
            
            if not name:
                continue
            
            # 方向
            direction = PortDirection.INPUT
            if hasattr(item, 'header') and item.header:
                hdr = str(item.header).lower()
                if 'output' in hdr:
                    direction = PortDirection.OUTPUT
                elif 'inout' in hdr:
                    direction = PortDirection.INOUT
            
            # 宽度
            width = 1
            if hasattr(item, 'header') and item.header:
                hdr = str(item.header)
                if '[' in hdr:
                    m = re.search(r'\[(\d+):(\d+)\]', hdr)
                    if m:
                        width = int(m.group(1)) - int(m.group(2)) + 1
            
            ports.append(Port(name=name, direction=direction, width=width))
        
        return ports
    
    def _categorize_ports(self, ports: List[Port]):
        for port in ports:
            name_lower = port.name.lower()
            
            if 'clk' in name_lower or 'clock' in name_lower:
                port.category = SignalCategory.CLOCK
            elif 'rst' in name_lower or 'reset' in name_lower:
                port.category = SignalCategory.RESET
            elif any(k in name_lower for k in ['vld', 'valid', 'rdy', 'ready', 'en', 'enable', 'ack', 'req', 'irq', 'flag', 'start', 'stop']):
                port.category = SignalCategory.CONTROL
            elif any(k in name_lower for k in ['data', 'din', 'dout', 'addr', 'q', 'result']):
                port.category = SignalCategory.DATA
            else:
                port.category = SignalCategory.OTHER
    
    def _trace_data_flow(self, spec: IOSpec):
        """追踪数据流"""
        try:
            from trace.driver import DriverTracer
            
            dt = DriverTracer(self.parser)
            
            for port in spec.ports:
                if port.direction != PortDirection.OUTPUT:
                    continue
                
                drivers = dt.find_driver(port.name)
                if drivers:
                    for drv in drivers:
                        src = drv.source_expr if drv.source_expr else ""
                        is_input = any(p.name in src and p.direction == PortDirection.INPUT for p in spec.ports)
                        spec.data_flows.append({
                            'output': port.name,
                            'driver': src[:40],
                            'source': 'input' if is_input else 'internal'
                        })
        except:
            pass
    
    def generate_report(self, spec: IOSpec) -> str:
        report = f"Module: {spec.module_name}\n"
        report += f"Parameters: {spec.parameters}\n"
        report += f"\nPorts ({len(spec.ports)}):\n"
        
        for port in spec.ports:
            w = f"[{port.width-1}:0]" if port.width > 1 else ""
            report += f"  {port.direction.value:7} {port.name:12}{w:8} -> {port.category.value}\n"
        
        if spec.data_flows:
            report += f"\nData Flows:\n"
            for df in spec.data_flows:
                report += f"  {df['output']:12} <- {df['driver']:40} ({df['source']})\n"
        
        return report




    def generate_flow_diagram(self, spec: IOSpec) -> str:
        """Phase 4: 生成数据流图"""
        lines = []
        lines.append("=" * 60)
        lines.append(f"IO Data Flow - {spec.module_name}")
        lines.append("=" * 60)
        
        # 按类型分组
        inputs = [p for p in spec.ports if p.direction == PortDirection.INPUT]
        outputs = [p for p in spec.ports if p.direction == PortDirection.OUTPUT]
        
        lines.append(f"\nINPUTS ({len(inputs)}):")
        for p in inputs:
            w = f"[{p.width-1}:0]" if p.width > 1 else ""
            lines.append(f"  {p.name}{w} -> {p.category.value}")
        
        lines.append(f"\nOUTPUTS ({len(outputs)}):")
        for p in outputs:
            w = f"[{p.width-1}:0]" if p.width > 1 else ""
            # 找数据流
            flow = next((f for f in spec.data_flows if f['output'] == p.name), None)
            src = flow['driver'][:25] if flow else "?"
            lines.append(f"  {p.name}{w} <- {src}")
        
        # 连接关系
        lines.append(f"\nCONNECTIONS:")
        for df in spec.data_flows:
            lines.append(f"  {df['output']} <= {df['driver'][:30]}")
        
        lines.append("=" * 60)
        return "\n".join(lines)
    
    def get_port_code_location(self, spec: IOSpec, port_name: str) -> Dict:
        """获取端口的代码位置"""
        for tree in self.parser.trees.values():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            root = tree.root
            if not hasattr(root, 'members'):
                continue
            
            for i in range(len(root.members)):
                member = root.members[i]
                if 'ModuleDeclaration' not in str(type(member)):
                    continue
                
                if not hasattr(member, 'members'):
                    continue
                
                for j in range(len(member.members)):
                    stmt = member.members[j]
                    stmt_str = str(stmt)
                    
                    # 在端口声明中查找
                    if port_name in stmt_str:
                        if 'input' in stmt_str.lower() or 'output' in stmt_str.lower():
                            return {
                                'line': j + 1,
                                'file': tree.source_name if hasattr(tree, 'source_name') else '',
                                'code': stmt_str[:60]
                            }
        
        return {'line': None, 'file': '', 'code': ''}


def extract_iospec(parser, module_name: str = None) -> IOSpec:
    return IOSpecExtractor(parser).extract(module_name)
