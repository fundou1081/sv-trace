"""Scope 核心数据模型

定义所有 scope 体系使用的数据类型。
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


class ScopeKind(Enum):
    """作用域类型枚举"""
    MODULE = "module"
    INTERFACE = "interface"
    PROGRAM = "program"
    PACKAGE = "package"
    CLASS = "class"
    ALWAYS_FF = "always_ff"
    ALWAYS_COMB = "always_comb"
    ALWAYS_LATCH = "always_latch"
    ALWAYS = "always"
    GENERATE_IF = "generate_if"
    GENERATE_FOR = "generate_for"
    GENERATE_CASE = "generate_case"
    SEQUENCE = "sequence"
    PROPERTY = "property"
    COVERGROUP = "covergroup"
    FUNCTION = "function"
    TASK = "task"
    BLOCK = "block"  # 命名块 begin...end


class RefContext(Enum):
    """引用上下文类型"""
    ALWAYS_FF = "always_ff"
    ALWAYS_COMB = "always_comb"
    ALWAYS_LATCH = "always_latch"
    ALWAYS = "always"
    ASSIGN = "assign"
    COVERGROUP = "covergroup"
    CONSTRAINT = "constraint"
    SEQUENCE = "sequence"
    PROPERTY = "property"
    FUNCTION = "function"
    TASK = "task"
    CLASS_METHOD = "class_method"


@dataclass
class SignalDecl:
    """信号声明
    
    代表一个信号的定义信息。
    """
    name: str
    scope_id: str
    width: int = 1                      # 位宽
    declaration_kind: str = ""           # wire, reg, logic, etc.
    data_type: str = "logic"           # 数据类型
    line: int = 0                       # 声明行号
    
    # 可选属性
    init_value: Optional[str] = None    # 初始值
    is_signed: bool = False
    dimensions: List[str] = field(default_factory=list)  # 数组维度


@dataclass
class InstanceInfo:
    """模块实例信息"""
    instance_name: str                  # 实例名，如 "u_dut"
    module_name: str                     # 模块名，如 "dut"
    scope_id: str                        # 实例的作用域 ID
    parent_scope: str                    # 父作用域
    port_connections: Dict[str, str]    # 端口连接映射


@dataclass
class SignalRef:
    """信号引用
    
    代表一次信号引用（读取或写入）。
    """
    signal_name: str                     # 原始名称
    resolved_scope: str                  # 解析到的作用域 ID
    resolved_name: str                   # 解析后的完整名称
    ref_context: RefContext             # 引用上下文
    
    is_lhs: bool = False                # 是否是左值（被驱动）
    is_rhs: bool = False                # 是否是右值（被读取）
    
    # 附加信息
    is_cross_module: bool = False       # 是否跨模块引用
    is_cross_instance: bool = False     # 是否跨实例引用（如 dut.signal）
    line: int = 0
    
    # 复杂表达式信息
    in_complex_expression: bool = False  # 是否在复杂表达式中
    expression_depth: int = 0            # 表达式嵌套深度


@dataclass
class ScopeInfo:
    """作用域信息
    
    代表一个完整的作用域（模块、always_ff 块等）。
    """
    scope_id: str                       # 唯一标识，如 "top.u_dut.always_ff_0"
    kind: ScopeKind
    
    # 层级关系
    parent_scope: Optional[str] = None
    children: List[str] = field(default_factory=list)  # 子作用域 IDs
    
    # 作用域内的声明和引用
    declared_signals: Dict[str, SignalDecl] = field(default_factory=dict)
    local_refs: List[SignalRef] = field(default_factory=list)
    
    # 实例信息（如果是模块实例）
    instance_of: Optional[str] = None   # 模块名（如果是实例）
    instance_name: Optional[str] = None  # 实例名
    
    # 端口信息（如果是模块/接口定义）
    ports_input: List[str] = field(default_factory=list)
    ports_output: List[str] = field(default_factory=list)
    ports_inout: List[str] = field(default_factory=list)
    
    # 实例层级路径
    hierarchy_path: str = ""            # 完整层级路径，如 "top.u_dut"
    
    def add_signal(self, sig: SignalDecl):
        """添加信号声明"""
        self.declared_signals[sig.name] = sig
    
    def get_signal(self, name: str) -> Optional[SignalDecl]:
        """查找信号声明"""
        return self.declared_signals.get(name)
    
    @property
    def all_signals(self) -> List[str]:
        """所有声明的信号"""
        return list(self.declared_signals.keys())


@dataclass  
class ScopeTree:
    """作用域树
    
    包含完整的设计作用域层级信息。
    """
    root_scope: str                     # 根作用域 ID
    scopes: Dict[str, ScopeInfo] = field(default_factory=dict)  # scope_id → ScopeInfo
    instances: Dict[str, InstanceInfo] = field(default_factory=dict)  # instance_name → InstanceInfo
    
    def add_scope(self, scope: ScopeInfo):
        """添加作用域"""
        self.scopes[scope.scope_id] = scope
        if scope.parent_scope and scope.scope_id not in self.scopes.get(scope.parent_scope, ScopeInfo("dummy", ScopeKind.MODULE)).children:
            parent = self.scopes.get(scope.parent_scope)
            if parent:
                parent.children.append(scope.scope_id)
    
    def get_scope(self, scope_id: str) -> Optional[ScopeInfo]:
        """获取作用域"""
        return self.scopes.get(scope_id)
    
    def get_parent(self, scope_id: str) -> Optional[str]:
        """获取父作用域"""
        scope = self.scopes.get(scope_id)
        return scope.parent_scope if scope else None
    
    def get_children(self, scope_id: str) -> List[str]:
        """获取子作用域"""
        scope = self.scopes.get(scope_id)
        return scope.children if scope else []
    
    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        """检查是否是祖先作用域"""
        current = descendant
        while current:
            if current == ancestor:
                return True
            current = self.get_parent(current)
        return False
    
    def resolve_hierarchy_path(self, path: str, start_scope: str) -> Optional[str]:
        """解析 HDL 层级路径
        
        例如: "dut.reg_a" 从 top.u_top 开始解析
        """
        parts = path.split('.')
        current = start_scope
        
        for part in parts:
            # 在当前作用域的子实例中查找
            scope = self.scopes.get(current)
            if not scope:
                return None
            
            # 查找名为 part 的子实例
            found = False
            for child_id in scope.children:
                child = self.scopes.get(child_id)
                if child and child.instance_name == part:
                    current = child.scope_id
                    found = True
                    break
            
            if not found:
                return None
        
        return current
