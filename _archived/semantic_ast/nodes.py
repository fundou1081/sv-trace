"""
semantic_ast.nodes - 语义节点类型定义

定义所有语义 AST 使用的节点类型。
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any


class SemanticNodeKind(Enum):
    """语义节点类型"""
    MODULE = "module"
    INTERFACE = "interface"
    PACKAGE = "package"
    CLASS = "class"
    FUNCTION = "function"
    TASK = "task"
    SIGNAL = "signal"
    INSTANCE = "instance"
    ALWAYS_FF = "always_ff"
    ALWAYS_COMB = "always_comb"
    ALWAYS_LATCH = "always_latch"
    ALWAYS = "always"
    CONTINUOUS_ASSIGN = "continuous_assign"
    PROCEDURAL_ASSIGN = "procedural_assign"
    PORT_INPUT = "port_input"
    PORT_OUTPUT = "port_output"
    PORT_INOUT = "port_inout"
    GENERATE_IF = "generate_if"
    GENERATE_FOR = "generate_for"
    GENERATE_CASE = "generate_case"


class ConfidenceLevel(Enum):
    """置信度等级"""
    HIGH = "high"         # 完全可信
    MEDIUM = "medium"     # 部分可信
    LOW = "low"           # 可信度低
    UNCERTAIN = "uncertain"  # 不可信


@dataclass
class SemanticDriverRef:
    """语义驱动引用
    
    表示一个驱动源到信号的引用关系。
    """
    source_expr: str = ""              # 驱动源表达式 (完整字符串)
    source_scope: str = ""            # 驱动所在作用域
    kind: str = ""                     # always_ff, always_comb, continuous
    clock: str = ""                   # 关联时钟信号
    reset: str = ""                   # 关联复位信号
    line: int = 0                     # 代码行号
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    caveats: List[str] = field(default_factory=list)
    
    def __repr__(self):
        return (f"DriverRef({self.source_expr} [{self.kind}]"
                f"@{self.line} conf={self.confidence.value})")


@dataclass
class SemanticLoadRef:
    """语义负载引用
    
    表示一个信号被哪些表达式引用（加载）。
    """
    load_expr: str = ""                # 负载表达式
    load_scope: str = ""              # 引用所在作用域
    context: str = ""                 # always_comb, assign 等
    line: int = 0                     # 代码行号
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    caveats: List[str] = field(default_factory=list)
    
    def __repr__(self):
        return f"LoadRef({self.load_expr} [{self.context}]@{self.line})"


@dataclass
class SemanticSignalNode:
    """语义信号节点
    
    替代传统的 (signal_name + ScopeTree + SymbolTable) 三元组。
    所有信号相关的语义信息都内聚在这个节点里。
    
    与旧架构对比:
    - 旧: signal_name + 查询 ScopeTree + 查询 SymbolTable
    - 新: SemanticSignalNode.signal_name, .scope_id, .data_type, .drivers[], .loads[]
    """
    name: str                          # 原始名称
    resolved_name: str = ""            # 解析后的完整名称 (含层级)
    scope_id: str = ""                 # 所在作用域 ID
    
    # 类型信息
    data_type: str = "logic"
    width: int = 1
    is_signed: bool = False
    dimensions: List[str] = field(default_factory=list)
    
    # 端口方向 (如果是端口)
    port_direction: Optional[str] = None  # input, output, inout
    
    # 信号声明位置
    declaration_line: int = 0
    last_driver_line: int = 0  # 最后一次驱动的行号
    
    # 驱动关系 (内聚化) - 这个信号被谁驱动
    drivers: List[SemanticDriverRef] = field(default_factory=list)
    
    # 负载关系 (内聚化) - 这个信号被谁使用
    loads: List[SemanticLoadRef] = field(default_factory=list)
    
    # 置信度
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    caveats: List[str] = field(default_factory=list)
    
    # 指向 pyslang 原始节点的引用
    _node: Optional[Any] = field(default=None, repr=False)
    
    def add_driver(self, driver: SemanticDriverRef):
        self.drivers.append(driver)
    
    def add_load(self, load: SemanticLoadRef):
        self.loads.append(load)
    
    @property
    def is_driven(self) -> bool:
        """是否有驱动源"""
        return len(self.drivers) > 0
    
    @property
    def is_multi_driven(self) -> bool:
        """是否被多驱动"""
        return len(self.drivers) > 1
    
    @property
    def all_driver_sources(self) -> List[str]:
        """所有驱动源表达式"""
        return [d.source_expr for d in self.drivers]
    
    def __repr__(self):
        driven_str = f"({len(self.drivers)} drivers)" if self.drivers else ""
        return f"Signal({self.name}{driven_str} @{self.scope_id})"


@dataclass
class SemanticScopeNode:
    """语义作用域节点
    
    代表一个完整的作用域（模块、always_ff 块等）。
    与旧 ScopeInfo 对比，这个节点直接持有 signals 字典。
    """
    scope_id: str                      # 唯一标识，如 "top.u_dut.always_ff_0"
    kind: SemanticNodeKind
    
    # 层级关系
    name: str = ""                     # 作用域名称
    hierarchy_path: str = ""            # 完整层级路径，如 "top.u_dut"
    parent_scope: Optional[str] = None
    children: List[str] = field(default_factory=list)  # 子作用域 IDs
    
    # 作用域内的信号 (内聚化，不再需要查 SymbolTable)
    signals: Dict[str, SemanticSignalNode] = field(default_factory=dict)
    
    # 实例信息（如果是模块实例）
    instance_of: Optional[str] = None   # 模块名（如果是实例）
    instance_name: Optional[str] = None  # 实例名
    
    # 端口信息（如果是模块/接口定义）
    ports_input: List[str] = field(default_factory=list)
    ports_output: List[str] = field(default_factory=list)
    ports_inout: List[str] = field(default_factory=list)
    
    # 指向 pyslang 原始节点的引用
    _node: Optional[Any] = field(default=None, repr=False)
    
    def add_signal(self, sig: SemanticSignalNode):
        self.signals[sig.name] = sig
    
    def get_signal(self, name: str) -> Optional[SemanticSignalNode]:
        return self.signals.get(name)
    
    @property
    def all_signals(self) -> List[str]:
        return list(self.signals.keys())
    
    def __repr__(self):
        return f"Scope({self.scope_id} [{self.kind.value}])"


@dataclass
class SemanticAST:
    """语义 AST 图
    
    替代 SemanticGraph + ScopeTree + SymbolTable 的分离架构。
    
    特点:
    - scopes 字典包含所有作用域
    - signals 全局信号池，按完全限定名索引
    - 驱动/负载关系直接内聚在 SemanticSignalNode 中
    """
    scopes: Dict[str, SemanticScopeNode] = field(default_factory=dict)
    
    # 全局信号池: resolved_name → SemanticSignalNode
    _global_signals: Dict[str, SemanticSignalNode] = field(default_factory=dict)
    
    # 根模块名
    root_module: str = ""
    
    # 源文件信息
    source_file: str = ""
    
    def add_scope(self, scope: SemanticScopeNode):
        self.scopes[scope.scope_id] = scope
    
    def get_scope(self, scope_id: str) -> Optional[SemanticScopeNode]:
        return self.scopes.get(scope_id)
    
    def add_global_signal(self, sig: SemanticSignalNode, resolved_name: str):
        """添加全局信号"""
        self._global_signals[resolved_name] = sig
    
    def get_global_signal(self, name: str) -> Optional[SemanticSignalNode]:
        """获取全局信号"""
        return self._global_signals.get(name)
    
    def get_signal_resolved(self, name: str, scope_id: str) -> Optional[SemanticSignalNode]:
        """在指定作用域及父作用域链中解析信号"""
        scope = self.get_scope(scope_id)
        while scope:
            sig = scope.signals.get(name)
            if sig:
                return sig
            scope = self.get_scope(scope.parent_scope) if scope.parent_scope else None
        return self._global_signals.get(name)
    
    def find_signals_by_driver(self, driver_expr: str) -> List[SemanticSignalNode]:
        """查找被指定驱动源驱动的所有信号"""
        results = []
        for sig in self._global_signals.values():
            for drv in sig.drivers:
                if drv.source_expr == driver_expr:
                    results.append(sig)
                    break
        return results
    
    def find_signals_by_load(self, load_expr: str) -> List[SemanticSignalNode]:
        """查找加载指定表达式的所有信号"""
        results = []
        for sig in self._global_signals.values():
            for ld in sig.loads:
                if ld.load_expr == load_expr:
                    results.append(sig)
                    break
        return results
    
    @property
    def all_signals(self) -> List[SemanticSignalNode]:
        return list(self._global_signals.values())
    
    def __repr__(self):
        return (f"SemanticAST(scopes={len(self.scopes)}, "
                f"signals={len(self._global_signals)})")