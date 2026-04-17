"""
Connection Tracer - 模块/接口连接追踪
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, List, Optional
from dataclasses import dataclass
import re


@dataclass
class Connection:
    source: str = ""
    dest: str = ""
    signal: str = ""


@dataclass
class Instance:
    name: str = ""
    module_type: str = ""
    connections: List[Connection] = None
    
    def __init__(self):
        self.connections = []


class ConnectionTracer:
    def __init__(self, parser):
        self.parser = parser
        self.instances: Dict[str, Instance] = {}
        self._extract_all()
    
    def _extract_all(self):
        for key, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root') or not tree.root:
                continue
            
            root = tree.root
            
            for attr in ['body', 'members']:
                if hasattr(root, attr) and getattr(root, attr):
                    for member in getattr(root, attr):
                        self._extract_from_member(member)
    
    def _extract_from_member(self, member):
        type_name = str(type(member))
        
        if 'HierarchyInstantiation' in type_name:
            self._extract_instance(member)
        
        for attr in ['body', 'members', 'statements']:
            if hasattr(member, attr):
                child = getattr(member, attr)
                if child:
                    if isinstance(child, list):
                        for c in child:
                            self._extract_from_member(c)
                    else:
                        self._extract_from_member(child)
    
    def _extract_instance(self, inst):
        instance = Instance()
        
        # 模块类型
        if hasattr(inst, 'type') and inst.type:
            instance.module_type = inst.type.value if hasattr(inst.type, 'value') else str(inst.type)
        
        # 实例列表
        if hasattr(inst, 'instances') and inst.instances:
            for i in inst.instances:
                # 实例名 - 从 decl.name 获取
                if hasattr(i, 'decl') and i.decl:
                    decl = i.decl
                    if hasattr(decl, 'name') and decl.name:
                        instance.name = decl.name.value if hasattr(decl.name, 'value') else str(decl.name)
                
                # 连接
                if hasattr(i, 'connections') and i.connections:
                    for conn in i.connections:
                        connection = self._parse_connection(conn)
                        if connection:
                            instance.connections.append(connection)
        
        if instance.name:
            self.instances[instance.name] = instance
    
    def _parse_connection(self, conn) -> Optional[Connection]:
        connection = Connection()
        conn_str = str(conn)
        
        # .port(signal)
        match = re.search(r'\.(\w+)\s*\(\s*(\w+)\s*\)', conn_str)
        if match:
            connection.dest = match.group(1)
            connection.signal = match.group(2)
        
        return connection if connection.signal else None
    
    def find_instance(self, name: str) -> Optional[Instance]:
        return self.instances.get(name)
    
    def get_all_instances(self) -> Dict[str, Instance]:
        return self.instances
    
    def get_connections_to_signal(self, signal_name: str) -> List[Connection]:
        results = []
        for inst in self.instances.values():
            for conn in inst.connections:
                if conn.signal == signal_name:
                    results.append(conn)
        return results
