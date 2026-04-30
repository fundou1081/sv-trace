"""
Parameter 解析器 - parameter/localparam 解析
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.models import Parameter
from typing import Dict, Any, Optional
import pyslang


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
            
            # Use visitor to find all ModuleDeclarations
            modules = []
            def visitor(node):
                if node.kind == pyslang.SyntaxKind.ModuleDeclaration:
                    modules.append(node)
                return pyslang.VisitAction.Advancee
            
            root.visit(visitor)
            
            for mod in modules:
                # Extract from module header parameters
                if hasattr(mod, 'header') and mod.header:
                    header = mod.header
                    if hasattr(header, 'parameters') and header.parameters:
                        params = header.parameters
                        if hasattr(params, 'declarations') and params.declarations:
                            decls = params.declarations
                            for i in range(len(decls)):
                                decl = decls[i]
                                # Skip non-ParameterDeclaration (like commas)
                                if hasattr(decl, 'kind') and 'ParameterDeclaration' in str(decl.kind):
                                    self._extract_param_decl(decl)
                
                # Extract from module body
                if hasattr(mod, 'body') and mod.body:
                    for member in mod.body:
                        self._extract_from_member(member)
    
    def _extract_param_decl(self, decl):
        if not decl:
            return
        
        if hasattr(decl, 'declarators') and decl.declarators:
            for i in range(len(decl.declarators)):
                d = decl.declarators[i]
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
                        module="",
                        resolved_value=resolved
                    )
    
    def _extract_from_member(self, member):
        type_name = str(type(member))
        
        if 'ParameterDeclaration' in type_name:
            self._extract_param_decl(member)
        
        for attr in ['members', 'body']:
            if hasattr(member, attr):
                child = getattr(member, attr)
                if child:
                    if hasattr(child, '__iter__') and not isinstance(child, str):
                        for c in child:
                            self._extract_from_member(c)
    
    def _resolve_value(self, value: str) -> Any:
        """解析参数值"""
        value = value.strip()
        
        # 尝试解析为数字
        try:
            if value.startswith("'h"):
                return int(value[2:], 16)
            elif value.startswith("'b"):
                return int(value[2:], 2)
            elif value.startswith("'d"):
                return int(value[2:])
            elif value.isdigit():
                return int(value)
        except:
            pass
        
        return value
    
    def get_param(self, name: str) -> Optional[Parameter]:
        return self.params.get(name)
    
    def get_all_params(self) -> Dict[str, Parameter]:
        return self.params
    
    def __getitem__(self, name: str) -> Any:
        return self.resolve(name)
    
    def __contains__(self, name: str) -> bool:
        return name in self.params
    
    def resolve(self, name: str) -> Any:
        """解析参数值"""
        param = self.params.get(name)
        if param:
            return param.resolved_value
        return None
