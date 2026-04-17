"""
Signal Query - 统一信号查询接口
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.models import Signal, SignalType
from parse.params import ParameterResolver
from typing import List, Optional


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
                    port_name = self._get_port_name(port)
                    if port_name == name:
                        return self._port_to_signal(port)
            
            # 在 body 中查找
            if hasattr(root, 'body') and root.body:
                for member in root.body:
                    sig = self._find_in_member(member, name)
                    if sig:
                        return sig
        
        return None
    
    def _get_port_name(self, port) -> str:
        if hasattr(port, 'declarator') and port.declarator:
            decl = port.declarator
            if hasattr(decl, 'name') and decl.name:
                return decl.name.value if hasattr(decl.name, 'value') else str(decl.name)
        return ""
    
    def _port_to_signal(self, port) -> Signal:
        name = self._get_port_name(port)
        
        width = 1
        if hasattr(port, 'declarator') and port.declarator:
            decl = port.declarator
            if hasattr(decl, 'dimensions') and decl.dimensions:
                for dim in decl.dimensions:
                    if hasattr(dim, 'left') and dim.left and hasattr(dim, 'right') and dim.right:
                        left = self.param_resolver.resolve(str(dim.left))
                        right = self.param_resolver.resolve(str(dim.right))
                        if isinstance(left, int) and isinstance(right, int):
                            width *= (left - right + 1)
        
        return Signal(
            name=name,
            width=width,
            signed=False,
            signal_type=SignalType.LOGIC,
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
        
        width = 1
        if hasattr(decl, 'dimensions') and decl.dimensions:
            for dim in decl.dimensions:
                if hasattr(dim, 'left') and dim.left and hasattr(dim, 'right') and dim.right:
                    left = self.param_resolver.resolve(str(dim.left))
                    right = self.param_resolver.resolve(str(dim.right))
                    if isinstance(left, int) and isinstance(right, int):
                        width *= (left - right + 1)
        
        signed = False
        if hasattr(decl_info, 'dataType') and decl_info.dataType:
            if hasattr(decl_info.dataType, 'signed') and decl_info.dataType.signed:
                signed = True
        
        return Signal(
            name=name,
            width=width,
            signed=signed,
            signal_type=SignalType.LOGIC,
        )
    
    def get_hierarchical_path(self, signal_name: str, instance_path: str = "") -> str:
        parts = []
        if instance_path:
            parts.append(instance_path)
        parts.append(signal_name)
        return ".".join(parts)
