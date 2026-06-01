"""semantic_ast.resolver - 跨模块符号解析器

负责跨模块符号消歧，构建全局符号表。

核心功能:
1. 收集所有模块的信号声明
2. 建立全局符号表 { fully_qualified_name → signal_node }
3. 解析跨模块引用 (e.g., `mod.inst.signal`, `pkg::signal`)
4. 处理 generate 展开后的实例层级

使用场景:
- 当信号引用跨模块时，需要消歧
- 当 generate 循环展开后，需要映射到实例层级
"""

import pyslang
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field

from semantic_ast.nodes import SemanticSignalNode, SemanticScopeNode, SemanticAST


@dataclass
class ResolvedSymbol:
    """解析后的符号引用"""
    name: str                     # 原始名称
    resolved_name: str            # 解析后的完整名称
    scope_id: str                 # 所在作用域 ID
    signal: Optional[SemanticSignalNode] = None  # 对应的信号节点
    is_input: bool = False        # 是否是输入端口
    is_output: bool = False       # 是否是输出端口
    is_local: bool = True         # 是否是本地信号


@dataclass 
class ModuleInterface:
    """模块接口信息"""
    module_name: str
    scope_id: str
    inputs: Dict[str, str] = field(default_factory=dict)   # name -> resolved_name
    outputs: Dict[str, str] = field(default_factory=dict)  # name -> resolved_name
    locals: Dict[str, str] = field(default_factory=dict)   # name -> resolved_name


class SymbolResolver:
    """全局符号解析器
    
    构建全局符号表，处理跨模块符号引用。
    """
    
    def __init__(self, sem_ast: SemanticAST):
        self._sem_ast = sem_ast
        
        # 全局符号表: resolved_name → signal
        self._global_table: Dict[str, SemanticSignalNode] = {}
        
        # 模块接口表: module_name → ModuleInterface
        self._module_interfaces: Dict[str, ModuleInterface] = {}
        
        # 实例映射: instance_path → module_name
        self._instances: Dict[str, str] = {}
        
        # 已解析
        self._resolved = False
    
    def resolve(self) -> 'SymbolResolver':
        """执行全局符号解析"""
        if self._resolved:
            return self
        
        # 1. 构建全局符号表
        self._build_global_table()
        
        # 2. 构建模块接口
        self._build_module_interfaces()
        
        # 3. 解析实例层级
        self._resolve_instances()
        
        self._resolved = True
        return self
    
    def _build_global_table(self):
        """构建全局符号表"""
        for sig in self._sem_ast.all_signals:
            if sig.resolved_name:
                self._global_table[sig.resolved_name] = sig
            # 也按简名称索引（用于当前作用域查找）
            short_name = sig.name.split('.')[-1]
            if short_name not in self._global_table:
                self._global_table[short_name] = sig
    
    def _build_module_interfaces(self):
        """构建模块接口表"""
        for scope_id, scope in self._sem_ast.scopes.items():
            if scope.kind.value.startswith('MODULE'):  # module, interface, program
                module_name = scope.name
                
                interface = ModuleInterface(
                    module_name=module_name,
                    scope_id=scope_id,
                )
                
                # 遍历信号的 scope_id 来确定输入/输出/本地
                for sig in self._sem_ast.all_signals:
                    if sig.scope_id == scope_id or sig.scope_id.startswith(scope_id + '.'):
                        if sig.scope_id == scope_id:
                            # 直接在模块作用域，是端口或本地
                            interface.locals[sig.name] = sig.resolved_name
                        else:
                            # 在子作用域 (如 always_ff 内部)，是本地的
                            interface.locals[sig.name] = sig.resolved_name
                
                self._module_interfaces[module_name] = interface
    
    def _resolve_instances(self):
        """解析实例层级"""
        for scope_id, scope in self._sem_ast.scopes.items():
            if scope.parent_scope:
                # 子作用域可能是实例
                parent = self._sem_ast.scopes.get(scope.parent_scope)
                if parent and parent.kind.value in ('MODULE', 'INTERFACE'):
                    self._instances[scope_id] = parent.name
    
    def resolve_signal(self, name: str, context_scope: str = None) -> Optional[ResolvedSymbol]:
        """解析信号引用
        
        Args:
            name: 信号名称 (可能是简名、pkg::name、mod.inst.signal)
            context_scope: 上下文作用域 ID
        
        Returns:
            ResolvedSymbol 或 None
        """
        # 1. 尝试直接在全局表中查找
        if name in self._global_table:
            sig = self._global_table[name]
            return ResolvedSymbol(
                name=name,
                resolved_name=sig.resolved_name,
                scope_id=sig.scope_id,
                signal=sig,
                is_local=True,
            )
        
        # 2. 处理 ScopedName (pkg::name)
        if '::' in name:
            return self._resolve_scoped_name(name, context_scope)
        
        # 3. 处理层级引用 (mod.inst.signal)
        if '.' in name:
            return self._resolve_hierarchical(name, context_scope)
        
        # 4. 在当前作用域链中查找
        return self._resolve_in_scope_chain(name, context_scope)
    
    def _resolve_scoped_name(self, name: str, context_scope: str = None) -> Optional[ResolvedSymbol]:
        """解析 pkg::signal 形式的引用"""
        parts = name.split('::')
        if len(parts) != 2:
            return None
        
        pkg_name, signal_name = parts
        
        # 在全局表中查找 pkg.signal
        full_name = f"{pkg_name}.{signal_name}"
        if full_name in self._global_table:
            sig = self._global_table[full_name]
            return ResolvedSymbol(
                name=name,
                resolved_name=sig.resolved_name,
                scope_id=sig.scope_id,
                signal=sig,
                is_local=False,
            )
        
        return None
    
    def _resolve_hierarchical(self, name: str, context_scope: str = None) -> Optional[ResolvedSymbol]:
        """解析层级引用 (mod.inst.signal)"""
        parts = name.split('.')
        if len(parts) < 2:
            return None
        
        # 尝试逐级构建完整路径
        for i in range(1, len(parts)):
            prefix = '.'.join(parts[:i])
            suffix = '.'.join(parts[i:])
            
            # 在全局表中查找
            full_name = f"{prefix}.{suffix}"
            if full_name in self._global_table:
                sig = self._global_table[full_name]
                return ResolvedSymbol(
                    name=name,
                    resolved_name=sig.resolved_name,
                    scope_id=sig.scope_id,
                    signal=sig,
                    is_local=False,
                )
        
        return None
    
    def _resolve_in_scope_chain(self, name: str, context_scope: str = None) -> Optional[ResolvedSymbol]:
        """在作用域链中查找信号"""
        if not context_scope:
            return None
        
        # 向上遍历作用域链
        scope_ids = self._get_scope_chain(context_scope)
        
        for sid in scope_ids:
            # 在该作用域中查找信号
            for sig_name, sig in self._sem_ast._global_signals.items():
                if sig.name == name and (sig.scope_id == sid or sig.scope_id.startswith(sid + '.')):
                    return ResolvedSymbol(
                        name=name,
                        resolved_name=sig.resolved_name,
                        scope_id=sig.scope_id,
                        signal=sig,
                        is_local=(sig.scope_id == sid),
                    )
        
        return None
    
    def _get_scope_chain(self, scope_id: str) -> List[str]:
        """获取作用域链"""
        chain = [scope_id]
        current = scope_id
        
        while True:
            scope = self._sem_ast.scopes.get(current)
            if not scope or not scope.parent_scope:
                break
            parent = scope.parent_scope
            if parent in chain:  # 防止循环
                break
            chain.append(parent)
            current = parent
        
        return chain
    
    def get_module_interface(self, module_name: str) -> Optional[ModuleInterface]:
        """获取模块接口信息"""
        return self._module_interfaces.get(module_name)
    
    def get_instance_module(self, instance_path: str) -> Optional[str]:
        """获取实例对应的模块名"""
        return self._instances.get(instance_path)
    
    @property
    def global_table(self) -> Dict[str, SemanticSignalNode]:
        """全局符号表"""
        return self._global_table.copy()
    
    @property 
    def module_interfaces(self) -> Dict[str, ModuleInterface]:
        """模块接口表"""
        return self._module_interfaces.copy()
    
    def __repr__(self) -> str:
        return f"SymbolResolver(signals={len(self._global_table)}, modules={len(self._module_interfaces)})"