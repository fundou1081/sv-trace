"""符号表管理

提供信号声明和引用的查询接口。
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from scope.models import (
    ScopeKind,
    ScopeInfo,
    SignalDecl,
    SignalRef,
    ScopeTree,
)


class SymbolTable:
    """符号表
    
    管理所有信号的声明和引用解析。
    """
    
    def __init__(self, scope_tree: ScopeTree):
        self._scope_tree = scope_tree
        # scope_id → signal_name → SignalDecl
        self._decls: Dict[str, Dict[str, SignalDecl]] = {}
    
    def declare(self, scope_id: str, sig: SignalDecl):
        """注册信号声明"""
        if scope_id not in self._decls:
            self._decls[scope_id] = {}
        self._decls[scope_id][sig.name] = sig
        
        # 同时注册到 ScopeTree
        scope = self._scope_tree.get_scope(scope_id)
        if scope:
            scope.add_signal(sig)
    
    def lookup(self, name: str, scope_id: str) -> Optional[SignalDecl]:
        """在当前作用域查找信号声明
        
        不向上查找父作用域。
        """
        scope_decls = self._decls.get(scope_id, {})
        return scope_decls.get(name)
    
    def lookup_upward(self, name: str, scope_id: str) -> Optional[Tuple[SignalDecl, str]]:
        """向上查找信号声明
        
        从当前作用域向上查找，直到根作用域。
        返回 (SignalDecl, scope_id)。
        """
        current = scope_id
        
        while current:
            sig = self.lookup(name, current)
            if sig:
                return (sig, current)
            
            parent = self._scope_tree.get_parent(current)
            current = parent
        
        return None
    
    def resolve_reference(self, name: str, scope_id: str) -> Optional[SignalRef]:
        """解析信号引用
        
        向上查找信号声明，构建完整的 SignalRef。
        """
        result = self.lookup_upward(name, scope_id)
        
        if not result:
            return None
        
        sig, resolved_scope = result
        scope = self._scope_tree.get_scope(scope_id)
        
        # 判断是否跨模块/跨实例
        is_cross = self._scope_tree.is_ancestor(resolved_scope, scope_id) and \
                   resolved_scope != scope_id
        
        return SignalRef(
            signal_name=name,
            resolved_scope=resolved_scope,
            resolved_name=f"{scope.hierarchy_path}.{sig.name}" if scope.hierarchy_path else sig.name,
            ref_context=scope.kind.value if hasattr(scope.kind, 'value') else "unknown",
            is_cross_module=is_cross,
        )
    
    def get_scope_signals(self, scope_id: str) -> List[SignalDecl]:
        """获取指定作用域的所有信号"""
        scope_decls = self._decls.get(scope_id, {})
        return list(scope_decls.values())
    
    def get_all_signals(self) -> List[SignalDecl]:
        """获取所有信号"""
        result = []
        for scope_decls in self._decls.values():
            result.extend(scope_decls.values())
        return result
