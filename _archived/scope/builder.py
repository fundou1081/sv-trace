"""ScopeBuilder - Pass 1: 构建作用域树

从 SystemVerilog AST 构建完整的作用域树和符号表。

符合铁律 18-20:
- 使用 pyslang.visit() 遍历
- 输出 ScopeTree + SymbolTable
- 先于所有 Extractor 执行
"""

import pyslang
from typing import Dict, List, Optional, Tuple, Set

from scope.models import (
    ScopeKind,
    ScopeInfo,
    SignalDecl,
    InstanceInfo,
    ScopeTree,
)
from scope.symbol_table import SymbolTable


# 公共工具函数
try:
    from semantic.utils import extract_identifier
except ImportError:
    def extract_identifier(node):
        if hasattr(node, 'text') and node.text:
            return node.text
        return ""


class ScopeBuilder:
    """作用域树构建器
    
    Pass 1: 从 AST 构建 ScopeTree + SymbolTable
    
    使用 pyslang.visit() 遍历，一次遍历完成所有 scope 信息提取。
    """
    
    def __init__(self):
        self._scope_tree: Optional[ScopeTree] = None
        self._symbol_table: Optional[SymbolTable] = None
        self._scope_stack: List[str] = []  # 当前作用域栈
        self._module_stack: List[str] = []  # 模块定义栈
        self._instance_stack: List[str] = []  # 实例栈
        self._hierarchy_path: str = ""  # 当前层级路径
        self._scope_counter: Dict[str, int] = {}  # 作用域计数器
    
    def build(self, tree: pyslang.SyntaxTree) -> Tuple[ScopeTree, SymbolTable]:
        """从 SyntaxTree 构建 ScopeTree 和 SymbolTable"""
        # 初始化
        root_id = "root"
        root_scope = ScopeInfo(
            scope_id=root_id,
            kind=ScopeKind.MODULE,
            hierarchy_path="",
        )
        
        self._scope_tree = ScopeTree(root_scope=root_id, scopes={root_id: root_scope})
        self._symbol_table = SymbolTable(self._scope_tree)
        self._scope_stack = [root_id]
        self._module_stack = []
        self._instance_stack = []
        self._hierarchy_path = ""
        self._scope_counter = {}
        
        # 遍历 AST
        def visitor(node):
            self._on_node(node)
            return pyslang.VisitAction.Advance
        
        tree.root.visit(visitor)
        
        return self._scope_tree, self._symbol_table
    
    def _get_kind(self, node) -> str:
        """获取节点 kind 名称"""
        if not hasattr(node, 'kind'):
            return ""
        kind = node.kind
        if hasattr(kind, 'name'):
            return kind.name
        return str(kind)
    
    def _iter_children(self, node) -> list:
        """安全遍历子节点"""
        try:
            return list(node)
        except:
            return []
    
    def _current_scope(self) -> str:
        """当前作用域 ID"""
        return self._scope_stack[-1] if self._scope_stack else "root"
    
    def _gen_scope_id(self, kind: ScopeKind, name: str) -> str:
        """生成唯一作用域 ID"""
        key = f"{kind.value}_{name}"
        count = self._scope_counter.get(key, 0) + 1
        self._scope_counter[key] = count
        if count == 1:
            return f"{self._hierarchy_path}.{name}" if self._hierarchy_path else name
        return f"{self._hierarchy_path}.{name}_{count}"
    
    def _push_scope(self, scope_id: str, kind: ScopeKind, hierarchy_path: str = ""):
        """压入新作用域"""
        if scope_id not in self._scope_tree.scopes:
            scope = ScopeInfo(
                scope_id=scope_id,
                kind=kind,
                parent_scope=self._current_scope(),
                hierarchy_path=hierarchy_path,
            )
            self._scope_tree.add_scope(scope)
        
        self._scope_stack.append(scope_id)
    
    def _pop_scope(self):
        """弹出作用域"""
        if len(self._scope_stack) > 1:
            self._scope_stack.pop()
    
    def _on_node(self, node):
        """处理每个节点"""
        kind = self._get_kind(node)
        
        # 模块/接口定义
        if kind == 'ModuleDeclaration':
            self._enter_module(node)
        elif kind == 'InterfaceDeclaration':
            self._enter_interface(node)
        elif kind == 'ProgramDeclaration':
            self._enter_program(node)
        elif kind == 'PackageDeclaration':
            self._enter_package(node)
        
        # 过程块
        elif kind == 'AlwaysFFBlock':
            self._enter_always_ff(node)
        elif kind == 'AlwaysCombProcedure':
            self._enter_always_comb(node)
        elif kind == 'AlwaysLatchProcedure':
            self._enter_always_latch(node)
        elif kind == 'AlwaysProcedure':
            self._enter_always(node)
        
        # generate 块
        elif kind == 'GenerateIfStatement':
            self._enter_generate_if(node)
        elif kind == 'GenerateCaseStatement':
            self._enter_generate_case(node)
        elif kind == 'GenerateLoopStatement':
            self._enter_generate_for(node)
        
        # 实例化
        elif kind == 'ModuleInstance':
            self._process_module_instance(node)
        elif kind == 'InterfaceInstance':
            self._process_interface_instance(node)
        
        # 信号声明
        elif kind == 'Declarator':
            self._process_declarator(node)
        
        # 端口声明
        elif kind == 'AnsiPortDeclaration':
            self._process_port_decl(node)
        elif kind == 'PortDeclaration':
            self._process_port_decl(node)
        
        # 类
        elif kind == 'ClassDeclaration':
            self._enter_class(node)
        
        # 函数/任务
        elif kind == 'FunctionDeclaration':
            self._enter_function(node)
        elif kind == 'TaskDeclaration':
            self._enter_task(node)
        
        # begin...end 命名块
        elif kind == 'SequentialBlockStatement':
            self._process_named_block(node)
    
    # =========================================================================
    # 模块/接口/程序/包
    # =========================================================================
    
    def _enter_module(self, node):
        """处理模块定义"""
        name = self._get_module_name(node)
        if not name:
            return
        
        self._module_stack.append(name)
        
        if self._hierarchy_path:
            hierarchy = f"{self._hierarchy_path}.{name}"
        else:
            hierarchy = name
        
        scope_id = hierarchy
        self._push_scope(scope_id, ScopeKind.MODULE, hierarchy)
        
        # 处理端口
        self._process_module_ports(node)
    
    def _enter_interface(self, node):
        """处理接口定义"""
        name = self._get_module_name(node)
        if not name:
            return
        
        hierarchy = f"{self._hierarchy_path}.{name}" if self._hierarchy_path else name
        self._push_scope(hierarchy, ScopeKind.INTERFACE, hierarchy)
    
    def _enter_program(self, node):
        """处理程序定义"""
        name = self._get_module_name(node)
        if not name:
            return
        
        hierarchy = f"{self._hierarchy_path}.{name}" if self._hierarchy_path else name
        self._push_scope(hierarchy, ScopeKind.PROGRAM, hierarchy)
    
    def _enter_package(self, node):
        """处理包定义"""
        name = self._get_module_name(node)
        if not name:
            return
        
        hierarchy = f"{self._hierarchy_path}.{name}" if self._hierarchy_path else name
        self._push_scope(hierarchy, ScopeKind.PACKAGE, hierarchy)
    
    def _get_module_name(self, node) -> str:
        """从模块声明节点提取名称"""
        for child in self._iter_children(node):
            kind = self._get_kind(child)
            if kind == 'Identifier':
                return extract_identifier(child) or ""
            if kind == 'IdentifierName':
                return extract_identifier(child) or ""
        return ""
    
    def _process_module_ports(self, node):
        """处理模块端口声明"""
        for child in self._iter_children(node):
            kind = self._get_kind(child)
            if kind == 'AnsiPortList':
                for port_item in self._iter_children(child):
                    self._process_port_item(port_item)
            elif kind == 'PortDeclaration':
                self._process_port_decl(port_item)
    
    def _process_port_item(self, node):
        """处理单个端口"""
        kind = self._get_kind(node)
        if kind == 'AnsiPortDeclaration':
            self._process_port_decl(node)
    
    # =========================================================================
    # 过程块
    # =========================================================================
    
    def _enter_always_ff(self, node):
        """处理 always_ff 块"""
        scope_id = self._gen_scope_id(ScopeKind.ALWAYS_FF, "always_ff")
        hierarchy = f"{self._hierarchy_path}.{scope_id.split('.')[-1]}"
        self._push_scope(scope_id, ScopeKind.ALWAYS_FF, hierarchy)
    
    def _enter_always_comb(self, node):
        """处理 always_comb 块"""
        scope_id = self._gen_scope_id(ScopeKind.ALWAYS_COMB, "always_comb")
        hierarchy = f"{self._hierarchy_path}.{scope_id.split('.')[-1]}"
        self._push_scope(scope_id, ScopeKind.ALWAYS_COMB, hierarchy)
    
    def _enter_always_latch(self, node):
        """处理 always_latch 块"""
        scope_id = self._gen_scope_id(ScopeKind.ALWAYS_LATCH, "always_latch")
        hierarchy = f"{self._hierarchy_path}.{scope_id.split('.')[-1]}"
        self._push_scope(scope_id, ScopeKind.ALWAYS_LATCH, hierarchy)
    
    def _enter_always(self, node):
        """处理 always 块"""
        scope_id = self._gen_scope_id(ScopeKind.ALWAYS, "always")
        hierarchy = f"{self._hierarchy_path}.{scope_id.split('.')[-1]}"
        self._push_scope(scope_id, ScopeKind.ALWAYS, hierarchy)
    
    # =========================================================================
    # Generate 块
    # =========================================================================
    
    def _enter_generate_if(self, node):
        """处理 generate if"""
        scope_id = self._gen_scope_id(ScopeKind.GENERATE_IF, "genif")
        self._push_scope(scope_id, ScopeKind.GENERATE_IF, self._hierarchy_path)
    
    def _enter_generate_case(self, node):
        """处理 generate case"""
        scope_id = self._gen_scope_id(ScopeKind.GENERATE_CASE, "gencase")
        self._push_scope(scope_id, ScopeKind.GENERATE_CASE, self._hierarchy_path)
    
    def _enter_generate_for(self, node):
        """处理 generate for"""
        scope_id = self._gen_scope_id(ScopeKind.GENERATE_FOR, "genfor")
        self._push_scope(scope_id, ScopeKind.GENERATE_FOR, self._hierarchy_path)
    
    # =========================================================================
    # 实例化
    # =========================================================================
    
    def _process_module_instance(self, node):
        """处理模块实例化"""
        # 获取实例名和模块名
        instance_name = ""
        module_name = ""
        
        for child in self._iter_children(node):
            kind = self._get_kind(child)
            if kind == 'Identifier':
                instance_name = extract_identifier(child) or ""
            elif kind == 'IdentifierName':
                if not module_name:
                    module_name = extract_identifier(child) or ""
        
        if not instance_name:
            return
        
        # 构建实例层级
        parent_path = self._hierarchy_path
        if parent_path:
            hierarchy = f"{parent_path}.{instance_name}"
        else:
            hierarchy = instance_name
        
        old_hierarchy = self._hierarchy_path
        self._hierarchy_path = hierarchy
        
        scope_id = hierarchy
        self._push_scope(scope_id, ScopeKind.MODULE, hierarchy)
        
        # 记录实例信息
        instance = InstanceInfo(
            instance_name=instance_name,
            module_name=module_name,
            scope_id=scope_id,
            parent_scope=self._current_scope(),
            port_connections={},
        )
        self._scope_tree.instances[instance_name] = instance
        
        # 处理端口连接
        self._process_port_connections(node)
        
        self._pop_scope()
        self._hierarchy_path = old_hierarchy
    
    def _process_interface_instance(self, node):
        """处理接口实例化"""
        instance_name = ""
        interface_name = ""
        
        for child in self._iter_children(node):
            kind = self._get_kind(child)
            if kind == 'Identifier':
                instance_name = extract_identifier(child) or ""
            elif kind == 'IdentifierName':
                if not interface_name:
                    interface_name = extract_identifier(child) or ""
        
        if not instance_name:
            return
        
        parent_path = self._hierarchy_path
        hierarchy = f"{parent_path}.{instance_name}" if parent_path else instance_name
        
        old_hierarchy = self._hierarchy_path
        self._hierarchy_path = hierarchy
        
        scope_id = hierarchy
        self._push_scope(scope_id, ScopeKind.INTERFACE, hierarchy)
        
        self._pop_scope()
        self._hierarchy_path = old_hierarchy
    
    def _process_port_connections(self, node):
        """处理端口连接"""
        for child in self._iter_children(node):
            kind = self._get_kind(child)
            if kind == 'OrderedPortConnections':
                # 有序端口连接
                pass  # TODO
            elif kind == 'NamedPortConnections':
                # 命名端口连接
                for conn in self._iter_children(child):
                    self._process_named_connection(conn)
    
    def _process_named_connection(self, node):
        """处理命名端口连接"""
        port_name = ""
        connected_signal = ""
        
        for child in self._iter_children(node):
            kind = self._get_kind(child)
            if kind == 'Identifier' or kind == 'IdentifierName':
                if not port_name:
                    port_name = extract_identifier(child) or ""
                elif not connected_signal:
                    connected_signal = extract_identifier(child) or ""
        
        if port_name:
            instance = self._scope_tree.instances.get(self._hierarchy_path.split('.')[-1])
            if instance:
                instance.port_connections[port_name] = connected_signal
    
    # =========================================================================
    # 信号声明
    # =========================================================================
    
    def _process_declarator(self, node):
        """处理信号声明"""
        name = ""
        width = 1
        line = 0
        
        if hasattr(node, 'span') and node.span:
            line = node.span.start_line
        
        for child in self._iter_children(node):
            kind = self._get_kind(child)
            if kind == 'Identifier':
                name = extract_identifier(child) or ""
            elif kind in ('VariableDimension', 'RangeDimensionSpecifier'):
                # 简单处理宽度
                width = 8  # TODO: 精确提取
        
        if not name:
            return
        
        decl = SignalDecl(
            name=name,
            scope_id=self._current_scope(),
            width=width,
            line=line,
        )
        
        self._symbol_table.declare(self._current_scope(), decl)
    
    def _process_port_decl(self, node):
        """处理端口声明"""
        direction = "input"  # 默认
        name = ""
        width = 1
        line = 0
        
        if hasattr(node, 'span') and node.span:
            line = node.span.start_line
        
        for child in self._iter_children(node):
            kind = self._get_kind(child)
            if kind in ('InputKeyword', 'OutputKeyword', 'InOutKeyword'):
                direction = kind.replace('Keyword', '').lower()
            elif kind == 'Identifier' or kind == 'IdentifierName':
                name = extract_identifier(child) or ""
        
        if not name:
            return
        
        decl = SignalDecl(
            name=name,
            scope_id=self._current_scope(),
            width=width,
            declaration_kind="port",
            line=line,
        )
        
        self._symbol_table.declare(self._current_scope(), decl)
        
        # 记录到作用域的端口列表
        scope = self._scope_tree.get_scope(self._current_scope())
        if scope:
            if direction == "input":
                scope.ports_input.append(name)
            elif direction == "output":
                scope.ports_output.append(name)
            elif direction == "inout":
                scope.ports_inout.append(name)
    
    # =========================================================================
    # 类/函数/任务
    # =========================================================================
    
    def _enter_class(self, node):
        """处理类定义"""
        name = self._get_module_name(node)
        if not name:
            return
        
        hierarchy = f"{self._hierarchy_path}.{name}" if self._hierarchy_path else name
        self._push_scope(hierarchy, ScopeKind.CLASS, hierarchy)
    
    def _enter_function(self, node):
        """处理函数定义"""
        name = "function"
        for child in self._iter_children(node):
            if self._get_kind(child) == 'Identifier':
                name = extract_identifier(child) or "function"
                break
        
        hierarchy = f"{self._hierarchy_path}.{name}" if self._hierarchy_path else name
        self._push_scope(hierarchy, ScopeKind.FUNCTION, hierarchy)
        self._pop_scope()  # 函数内部不再细分
    
    def _enter_task(self, node):
        """处理任务定义"""
        name = "task"
        for child in self._iter_children(node):
            if self._get_kind(child) == 'Identifier':
                name = extract_identifier(child) or "task"
                break
        
        hierarchy = f"{self._hierarchy_path}.{name}" if self._hierarchy_path else name
        self._push_scope(hierarchy, ScopeKind.TASK, hierarchy)
        self._pop_scope()  # 任务内部不再细分
    
    # =========================================================================
    # 命名块
    # =========================================================================
    
    def _process_named_block(self, node):
        """处理 begin...end 命名块"""
        name = ""
        for child in self._iter_children(node):
            kind = self._get_kind(child)
            if kind == 'Identifier' or kind == 'IdentifierName':
                name = extract_identifier(child) or ""
                break
        
        if name:
            hierarchy = f"{self._hierarchy_path}.{name}" if self._hierarchy_path else name
            self._push_scope(hierarchy, ScopeKind.BLOCK, hierarchy)
            self._pop_scope()
