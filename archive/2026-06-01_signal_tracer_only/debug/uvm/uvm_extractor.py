"""UVM testbench structure extractor."""

import re
from typing import Dict, List, Set, Optional

from ..class_extractor import ClassExtractor
from ..class_relation import ClassRelationExtractor
from .uvm_component import UVMComponentInfo, UVMConnectionInfo


UVM_COMPONENT_TYPES = {
    'uvm_component', 'uvm_test', 'uvm_env', 'uvm_agent',
    'uvm_driver', 'uvm_sequencer', 'uvm_monitor', 'uvm_scoreboard',
    'uvm_subscriber', 'uvm_object', 'uvm_sequence_item',
    'uvm_fifo', 'uvm_tlm_fifo', 'uvm_analysis_fifo',
    'uvm_put_port', 'uvm_get_port', 'uvm_transport_port',
}

UVM_PHASES = {
    'build_phase', 'connect_phase', 'end_of_elaboration_phase',
    'start_of_simulation_phase', 'run_phase', 'extract_phase',
    'check_phase', 'report_phase', 'final_phase',
}


class UVMExtractor:
    def __init__(self, class_extractor, relation_extractor):
        self.class_extractor = class_extractor
        self.relation_extractor = relation_extractor
        self.classes = class_extractor.classes
        self.components = {}
        self.connections = []
        self._extract_uvm_structure()
    
    def _is_uvm_component(self, cls):
        current = cls.extends
        while current:
            if current in UVM_COMPONENT_TYPES:
                return True
            if current in self.classes:
                current = self.classes[current].extends
            else:
                break
        return False
    
    def _extract_uvm_structure(self):
        for class_name, cls in self.classes.items():
            if self._is_uvm_component(cls):
                info = UVMComponentInfo(
                    name=class_name,
                    type_name=class_name,
                    parent=cls.extends
                )
                
                if class_name in self.relation_extractor.method_definitions:
                    for method in self.relation_extractor.method_definitions[class_name]:
                        for phase in UVM_PHASES:
                            if phase in method.name:
                                info.phase_methods.append(method.name)
                                break
                
                self.components[class_name] = info
    
    def extract_tlm_connections(self, code):
        lines = code.split('\n')
        for i, line in enumerate(lines):
            pattern = r'(\w+)\.(\w+)\.connect\s*\(\s*(\w+)\.(\w+)\s*\)'
            matches = re.findall(pattern, line)
            for match in matches:
                comp1, port, comp2, export = match
                conn_type = 'analysis'
                if 'put' in port.lower():
                    conn_type = 'blocking_put'
                elif 'get' in port.lower():
                    conn_type = 'blocking_get'
                elif 'transport' in port.lower():
                    conn_type = 'transport'
                elif 'seq_item' in port.lower():
                    conn_type = 'seq_item_pull'
                
                conn = UVMConnectionInfo(
                    from_component=comp1,
                    from_port=port,
                    to_component=comp2,
                    to_port=export,
                    connection_type=conn_type,
                    line_number=i + 1
                )
                self.connections.append(conn)
    
    def get_report(self):
        lines = []
        lines.append("=" * 60)
        lines.append("UVM TESTBENCH STRUCTURE")
        lines.append("=" * 60)
        
        lines.append(f"\n[Components] ({len(self.components)})")
        for name, info in sorted(self.components.items()):
            lines.append(f"  {name}")
            if info.parent:
                lines.append(f"    extends: {info.parent}")
            if info.phase_methods:
                phases = sorted(set(info.phase_methods))
                lines.append(f"    phases: {', '.join(phases)}")
        
        lines.append(f"\n[TLM Connections] ({len(self.connections)})")
        for conn in self.connections:
            lines.append(f"  {conn.from_component}.{conn.from_port}")
            lines.append(f"    -> {conn.to_component}.{conn.to_port}")
            lines.append(f"    type: {conn.connection_type}")
        
        return "\n".join(lines)
