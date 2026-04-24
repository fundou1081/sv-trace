"""
DanglingPortDetector - 悬空端口检测
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from typing import Dict, List, Set
from dataclasses import dataclass
from enum import Enum


class PortDirection(Enum):
    INPUT = "input"
    OUTPUT = "output"
    INOUT = "inout"


@dataclass
class DanglingPort:
    port_name: str
    port_direction: PortDirection
    module_name: str
    instance_name: str = ""
    severity: str = "warning"
    reason: str = ""


class DanglingPortDetector:
    """悬空端口检测器 - Option B: 类型感知检测"""
    
    def __init__(self, parser):
        self.parser = parser
        self._driver_tracer = None
        self._load_tracer = None
    
    def _get_tracers(self):
        if not self._driver_tracer:
            from trace.driver import DriverTracer
            self._driver_tracer = DriverTracer(self.parser)
        if not self._load_tracer:
            from trace.load import LoadTracer
            self._load_tracer = LoadTracer(self.parser)
        return self._driver_tracer, self._load_tracer
    
    def detect_all(self) -> Dict[str, List[DanglingPort]]:
        results = {}
        
        for tree in self.parser.trees.values():
            if not tree or not hasattr(tree, "root"):
                continue
            
            root = tree.root
            if not hasattr(root, "members"):
                continue
            
            for i in range(len(root.members)):
                member = root.members[i]
                if "ModuleDeclaration" not in str(type(member)):
                    continue
                
                module_name = getattr(getattr(member, "header", None), "name", None)
                module_name = module_name.value if module_name else "unknown"
                
                ports = self._extract_ports(member)
                dangling = self._check_dangling_ports(module_name, ports)
                
                if dangling:
                    results[module_name] = dangling
        
        return results
    
    def detect(self, module_name: str) -> List[DanglingPort]:
        all_results = self.detect_all()
        return all_results.get(module_name, [])
    
    def _extract_ports(self, module) -> Dict[str, PortDirection]:
        ports = {}
        
        # Try header.ports (ANSI style: module top(input clk, ...))
        if hasattr(module, "header") and module.header:
            header = module.header
            ports_attr = getattr(header, "ports", None)
            if ports_attr:
                try:
                    # Use count method (like pyslang SyntaxList)
                    if hasattr(ports_attr, "count"):
                        count = ports_attr.count
                        for i in range(count):
                            port = ports_attr[i]
                            if not port:
                                continue
                            
                            # Get port name
                            port_name = None
                            if hasattr(port, "name"):
                                if hasattr(port.name, "value"):
                                    port_name = port.name.value
                                else:
                                    port_name = str(port.name)
                            
                            # Get port direction
                            direction = PortDirection.INPUT
                            if hasattr(port, "direction") and port.direction:
                                dir_str = str(port.direction).lower()
                                if "output" in dir_str:
                                    direction = PortDirection.OUTPUT
                                elif "inout" in dir_str:
                                    direction = PortDirection.INOUT
                            
                            if port_name:
                                ports[port_name] = direction
                except Exception as e:
                    print(f"Warning: Error extracting ports: {e}")
        
        # Try module.portList (traditional style: module top; input clk; ...)
        if not ports and hasattr(module, "portList") and module.portList:
            port_list = module.portList
            if hasattr(port_list, "ports") and port_list.ports:
                for i in range(len(port_list.ports)):
                    port = port_list.ports[i]
                    port_name = getattr(getattr(port, "name", None), "value", str(port.name))
                    
                    direction = PortDirection.INPUT
                    if hasattr(port, "direction"):
                        dir_str = str(port.direction).lower()
                        if "output" in dir_str:
                            direction = PortDirection.OUTPUT
                        elif "inout" in dir_str:
                            direction = PortDirection.INOUT
                    
                    ports[port_name] = direction
        
        return ports
    
    def _check_dangling_ports(
        self, 
        module_name: str, 
        ports: Dict[str, PortDirection]
    ) -> List[DanglingPort]:
        dangling = []
        driver_tracer, load_tracer = self._get_tracers()
        
        for port_name, direction in ports.items():
            is_dangling = False
            reason = ""
            
            if direction == PortDirection.INPUT:
                drivers = driver_tracer.find_driver(port_name)
                if not drivers:
                    is_dangling = True
                    reason = "Input port has no driver"
            
            elif direction == PortDirection.OUTPUT:
                loads = load_tracer.find_load(port_name)
                if not loads:
                    is_dangling = True
                    reason = "Output port has no load"
            
            elif direction == PortDirection.INOUT:
                drivers = driver_tracer.find_driver(port_name)
                loads = load_tracer.find_load(port_name)
                if not drivers and not loads:
                    is_dangling = True
                    reason = "Inout port has no connections"
            
            if is_dangling:
                severity = "error" if direction == PortDirection.OUTPUT else "warning"
                
                dangling.append(DanglingPort(
                    port_name=port_name,
                    port_direction=direction,
                    module_name=module_name,
                    severity=severity,
                    reason=reason
                ))
        
        return dangling
    
    def get_summary(self) -> Dict[str, int]:
        results = self.detect_all()
        
        summary = {
            "total_modules": len(results),
            "total_dangling": sum(len(ports) for ports in results.values()),
            "errors": sum(1 for ports in results.values() for p in ports if p.severity == "error"),
            "warnings": sum(1 for ports in results.values() for p in ports if p.severity == "warning")
        }
        
        return summary
