"""
Signal Query - 统一信号查询接口
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.models import Signal, Signal
from parse.params import ParameterResolver
from typing import List, Optional
import re


class SignalQuery:
    def __init__(self, parser):
        self.parser = parser
        self.param_resolver = ParameterResolver(parser)
    
    def find_signal(self, name: str, module_name: str = None) -> Optional[Signal]:
        for key, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root') or not tree.root:
                continue
            
            root = tree.root
            
            if 'ModuleDeclaration' not in str(type(root)):
                continue
            
            header = getattr(root, 'header', None)
            mod_name = ""
            if header:
                name_attr = getattr(header, 'name', None)
                if name_attr:
                    mod_name = name_attr.value
            
            if module_name and mod_name != module_name:
                continue
            
            # 在 ports 中查找
            if header and hasattr(header, 'ports') and header.ports:
                for port in header.ports.ports:
                    port_name = str(port)
                    # 提取信号名
                    match = re.search(r'(\w+)\s*$', port_name)
                    if match and match.group(1) == name:
                        return self._port_to_signal(port_name)
            
            # 在 body 中查找
            if hasattr(root, 'body') and root.body:
                for member in root.body:
                    sig = self._find_in_member(member, name)
                    if sig:
                        return sig
        
        return None
    
    def _port_to_signal(self, port_str: str) -> Signal:
        # 从端口字符串解析: "input [7:0] data" -> name=data, width=8
        # 提取信号名
        match = re.search(r'(\w+)\s*$', port_str)
        name = match.group(1) if match else ""
        
        # 提取位宽 [7:0]
        width_match = re.search(r'\[(\d+):(\d+)\]', port_str)
        if width_match:
            width = int(width_match.group(1)) - int(width_match.group(2)) + 1
        else:
            width = 1
        
        return Signal(
            name=name,
            width=width,
            signed=False,
            signal_type=Signal.LOGIC,
        )
    
    def _find_in_member(self, member, name: str) -> Optional[Signal]:
        type_name = str(type(member))
        
        if 'DataDeclaration' in type_name:
            if hasattr(member, 'declarators') and member.declarators:
                for decl in member.declarators:
                    if hasattr(decl, 'name') and decl.name:
                        if decl.name.value == name:
                            return self._decl_to_signal(decl, member)
        
        for attr in ['members', 'body', 'statements']:
            if hasattr(member, attr):
                child = getattr(member, attr)
                if child:
                    if isinstance(child, list):
                        for c in child:
                            result = self._find_in_member(c, name)
                            if result:
                                return result
                    else:
                        result = self._find_in_member(child, name)
                        if result:
                            return result
        
        return None
    
    def _decl_to_signal(self, decl, decl_info) -> Signal:
        name = decl.name.value if hasattr(decl, 'name') and decl.name else ""
        
        # 尝试从字符串解析位宽
        width = 1
        decl_str = str(decl)
        width_match = re.search(r'\[(\d+):(\d+)\]', decl_str)
        if width_match:
            width = int(width_match.group(1)) - int(width_match.group(2)) + 1
        
        return Signal(
            name=name,
            width=width,
            signed=False,
            signal_type=Signal.LOGIC,
        )
    
    def get_hierarchical_path(self, signal_name: str, instance_path: str = "") -> str:
        parts = []
        if instance_path:
            parts.append(instance_path)
        parts.append(signal_name)
        return ".".join(parts)
