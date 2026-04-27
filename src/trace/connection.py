"""
Connection Tracer - 模块/接口连接追踪
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, List, Optional
from dataclasses import dataclass, field
import pyslang


@dataclass
class Connection:
    """信号连接"""
    source: str = ""
    dest: str = ""
    signal: str = ""
    port_name: str = ""
    instance_name: str = ""


@dataclass 
class Instance:
    """模块实例"""
    name: str = ""
    module_type: str = ""
    connections: List[Connection] = field(default_factory=list)
    parent_module: str = ""


class ConnectionTracer:
    """追踪模块实例和连接"""
    
    def __init__(self, parser):
        self.parser = parser
        self.instances: List[Instance] = []
        self.instance_map: Dict[str, Instance] = {}
        self.signal_connections: Dict[str, List[Connection]] = {}
        self._extract_all()
    
    def _extract_all(self):
        for fname, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root') or not tree.root:
                continue
            root = tree.root
            
            if hasattr(root, 'members') and root.members:
                members = self._to_list(root.members)
                for member in members:
                    kind_name = str(member.kind) if hasattr(member, 'kind') else ""
                    if 'ModuleDeclaration' in kind_name:
                        self._extract_from_module(member)
    
    def _to_list(self, obj):
        if isinstance(obj, list):
            return obj
        if hasattr(obj, '__iter__') and not isinstance(obj, str):
            try:
                return list(obj)
            except:
                pass
        return []
    
    def _extract_from_module(self, module_node):
        try:
            module_name = ""
            if hasattr(module_node, 'header') and module_node.header:
                if hasattr(module_node.header, 'name'):
                    module_name = str(module_node.header.name).strip()
            
            if hasattr(module_node, 'members') and module_node.members:
                members = self._to_list(module_node.members)
                for member in members:
                    self._extract_member(member, module_name)
                    
        except Exception as e:
            pass
    
    def _extract_member(self, member, parent_module: str):
        if member is None:
            return
        
        kind_name = str(member.kind) if hasattr(member, 'kind') else ""
        
        if 'HierarchyInstantiation' in kind_name:
            self._process_hierarchy_instantiation(member, parent_module)
        
        for attr in ['members', 'statements', 'body']:
            if hasattr(member, attr):
                child = getattr(member, attr)
                if child:
                    children = self._to_list(child)
                    for c in children:
                        self._extract_member(c, parent_module)
    
    def _process_hierarchy_instantiation(self, inst_node, parent_module: str):
        try:
            module_type = ""
            if hasattr(inst_node, 'type') and inst_node.type:
                module_type = str(inst_node.type).strip()
            
            if not module_type:
                return
            
            if hasattr(inst_node, 'instances') and inst_node.instances:
                for hier_inst in inst_node.instances:
                    self._process_hierarchical_instance(hier_inst, module_type, parent_module)
                    
        except Exception as e:
            pass
    
    def _process_hierarchical_instance(self, hier_inst, module_type: str, parent_module: str):
        try:
            instance_name = ""
            if hasattr(hier_inst, 'decl') and hier_inst.decl:
                if hasattr(hier_inst.decl, 'name') and hier_inst.decl.name:
                    instance_name = str(hier_inst.decl.name).strip()
            
            if not instance_name:
                return
            
            inst = Instance(
                name=instance_name,
                module_type=module_type,
                parent_module=parent_module
            )
            self.instances.append(inst)
            self.instance_map[instance_name] = inst
            
            if hasattr(hier_inst, 'connections') and hier_inst.connections:
                self._extract_named_port_connections(hier_inst.connections, inst)
                    
        except Exception as e:
            pass
    
    def _extract_named_port_connections(self, conn_node, inst: Instance):
        try:
            results = []
            
            def visitor(node):
                if 'NamedPortConnection' in str(node.kind):
                    text = str(node).strip()
                    if text.startswith('.'):
                        text = text[1:]
                        parts = text.split('(', 1)
                        if len(parts) == 2:
                            port_name = parts[0].strip()
                            source = parts[1].rstrip(')').strip()
                            results.append((port_name, source))
                return pyslang.VisitAction.Advance
            
            conn_node.visit(visitor)
            
            for port_name, source in results:
                conn_obj = Connection(
                    source=source,
                    dest=port_name,
                    signal=source,
                    port_name=port_name,
                    instance_name=inst.name
                )
                inst.connections.append(conn_obj)
                
                if source not in self.signal_connections:
                    self.signal_connections[source] = []
                self.signal_connections[source].append(conn_obj)
                
        except Exception as e:
            pass
    
    def get_all_instances(self) -> List[Instance]:
        return self.instances
    
    def find_instance(self, name: str):
        """别名 - 兼容旧API"""
        return self.get_instance(name)

    def get_instance(self, name: str) -> Optional[Instance]:
        return self.instance_map.get(name)
    
    def get_instances_by_type(self, module_type: str) -> List[Instance]:
        return [i for i in self.instances if i.module_type == module_type]
    
    def get_signal_connections(self, signal: str) -> List[Connection]:
        return self.signal_connections.get(signal, [])
    
    def get_instance_inputs(self, instance_name: str) -> List[str]:
        inst = self.instance_map.get(instance_name)
        if not inst:
            return []
        return [c.source for c in inst.connections if c.source]
    
    def get_instance_outputs(self, instance_name: str) -> List[str]:
        inst = self.instance_map.get(instance_name)
        if not inst:
            return []
        return [c.dest for c in inst.connections if c.dest]


def trace_connections(parser) -> ConnectionTracer:
    return ConnectionTracer(parser)
