"""
Parameter 解析器 - parameter/localparam 解析
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.models import Parameter
from typing import Dict, Any, Optional


class ParameterResolver:
    def __init__(self, parser):
        self.parser = parser
        self.params: Dict[str, Parameter] = {}
        self._extract_all_params()
    
    def _extract_all_params(self):
        for key, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root') or not tree.root:
                continue
            
            root = tree.root
            
            if 'ModuleDeclaration' not in str(type(root)):
                continue
            
            if hasattr(root, 'header') and root.header:
                header = root.header
                if hasattr(header, 'parameters') and header.parameters:
                    for decl in header.parameters.declarations:
                        self._extract_param_decl(decl)
            
            if hasattr(root, 'body') and root.body:
                for member in root.body:
                    self._extract_from_member(member)
    
    def _extract_param_decl(self, decl):
        if not decl:
            return
        
        if hasattr(decl, 'declarators') and decl.declarators:
            for d in decl.declarators:
                name = ""
                value = ""
                
                if hasattr(d, 'name') and d.name:
                    name = d.name.value if hasattr(d.name, 'value') else str(d.name)
                
                if hasattr(d, 'initializer') and d.initializer:
                    init = d.initializer
                    # 使用 expr
                    if hasattr(init, 'expr') and init.expr:
                        value = str(init.expr)
                    else:
                        value = str(init)
                
                if name:
                    resolved = self._resolve_value(value)
                    self.params[name] = Parameter(
                        name=name,
                        value=value,
                        resolved_value=resolved,
                        is_localparam='parameter' not in str(type(decl)).lower(),
                    )
    
    def _extract_from_member(self, member):
        type_name = str(type(member))
        
        if 'ParameterDeclaration' in type_name:
            self._extract_param_decl(member)
        
        for attr in ['members', 'body']:
            if hasattr(member, attr):
                child = getattr(member, attr)
                if child:
                    if isinstance(child, list):
                        for c in child:
                            self._extract_from_member(c)
                    else:
                        self._extract_from_member(child)
    
    def _resolve_value(self, value: str) -> Optional[int]:
        if not value:
            return None
        
        value = value.strip()
        
        try:
            if value.isdigit():
                return int(value)
            
            for base in ["'h", "'H", "'b", "'B", "'d", "'D"]:
                if base in value:
                    parts = value.split(base)
                    if len(parts) == 2:
                        base_char = base[1]
                        if base_char in 'hH':
                            return int(parts[1], 16)
                        elif base_char in 'bB':
                            return int(parts[1], 2)
                        else:
                            return int(parts[1], 10)
            
            if value in self.params:
                return self.params[value].resolved_value
            
            return int(value, 0)
        except:
            return None
    
    def resolve(self, value: str) -> Any:
        if not value:
            return value
        
        resolved = self._resolve_value(value)
        if resolved is not None:
            return resolved
        
        if value in self.params:
            return self.params[value].resolved_value
        
        return value
    
    def resolve_width(self, width_expr: str) -> int:
        if not width_expr:
            return 1
        
        import re
        match = re.match(r'(\w+)\s*-\s*(\d+)', width_expr.strip())
        if match:
            param_name = match.group(1)
            num = int(match.group(2))
            param_val = self.resolve(param_name)
            if isinstance(param_val, int):
                return param_val - num + 1
        
        return 1
    
    def get_param(self, name: str) -> Optional[Parameter]:
        return self.params.get(name)
    
    def get_all_params(self) -> Dict[str, Parameter]:
        return self.params
    
    def __getitem__(self, name: str) -> Any:
        return self.resolve(name)
    
    def __contains__(self, name: str) -> bool:
        return name in self.params
