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
        """Extract ports from module declaration using pyslang PortDeclaration"""
        ports = {}
        
        try:
            # 遍历 module members 查找 PortDeclaration
            if not hasattr(module, 'members'):
                return ports
            
            for i in range(len(module.members)):
                member = module.members[i]
                if not hasattr(member, 'kind'):
                    continue
                
                kind_str = str(member.kind)
                
                # PortDeclaration: has declarators and header
                if 'PortDeclaration' in kind_str:
                    # Get direction from header
                    direction = PortDirection.INPUT  # default
                    header = getattr(member, 'header', None)
                    if header:
                        dir_str = str(header.direction).lower() if hasattr(header, 'direction') else ''
                        if 'output' in dir_str:
                            direction = PortDirection.OUTPUT
                        elif 'inout' in dir_str:
                            direction = PortDirection.INOUT
                    
                    # Get port name(s) from declarators
                    declarators = getattr(member, 'declarators', None)
                    if declarators:
                        # declarators could be a list or SeparatedList
                        try:
                            for decl in declarators:
                                if hasattr(decl, 'name') and decl.name:
                                    port_name = str(decl.name).strip()
                                    if port_name:
                                        ports[port_name] = direction
                        except TypeError:
                            # May be a SeparatedList, try iterate
                            if hasattr(declarators, '__iter__'):
                                for decl in declarators:
                                    if hasattr(decl, 'name') and decl.name:
                                        port_name = str(decl.name).strip()
                                        if port_name:
                                            ports[port_name] = direction
                                            
        except Exception as e:
            pass
        
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
