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
        """查找信号"""
        from core.models import Signal
        
        # 遍历所有解析的树
        for key, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root') or not tree.root:
                continue
            
            root = tree.root
            
            # root 是 CompilationUnit，需要从 members 找 ModuleDeclaration
            if not hasattr(root, 'members'):
                continue
            
            for i in range(len(root.members)):
                member = root.members[i]
                if 'ModuleDeclaration' not in str(type(member)):
                    continue
                
                # 获取模块名
                header = getattr(member, 'header', None)
                mod_name = ""
                if header:
                    name_attr = getattr(header, 'name', None)
                    if name_attr:
                        try:
                            mod_name = name_attr.value
                        except:
                            mod_name = str(name_attr)
                
                if module_name and mod_name != module_name:
                    continue
                
                # 在模块的 members 中查找信号声明
                if hasattr(member, 'members'):
                    for j in range(len(member.members)):
                        body_member = member.members[j]
                        
                        # 检查是否是 DataDeclaration
                        if 'DataDeclaration' in str(type(body_member)):
                            declarators = getattr(body_member, 'declarators', None)
                            if declarators:
                                try:
                                    for decl in declarators:
                                        if hasattr(decl, 'name'):
                                            decl_name = str(decl.name).strip()
                                            if decl_name == name:
                                                return Signal(name=name, module=mod_name, width=1)
                                except:
                                    pass
        
        # 没找到
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
