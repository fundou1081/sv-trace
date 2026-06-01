"""Extractors 基类和 SemanticGraph

提供所有 Extractor 的基类和通用数据结构。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
from enum import Enum

from scope.models import ScopeTree, SignalRef, RefContext
from scope.symbol_table import SymbolTable


class ConfidenceLevel(Enum):
    """置信度等级"""
    HIGH = "high"         # 完全可信
    MEDIUM = "medium"     # 部分可信（如跨模块引用）
    LOW = "low"          # 可信度低（如复杂表达式）
    UNCERTAIN = "uncertain"  # 不可信


@dataclass
class LoadPoint:
    """负载点
    
    表示: signal 被 load_by 加载
    """
    signal: str       # 被加载的信号 (lhs)
    load_by: str     # 加载来源 (rhs)
    context: str      # 上下文 (always_ff, always_comb, assign)
    line: int = 0
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    caveats: List[str] = field(default_factory=list)


@dataclass
class DriverPoint:
    """驱动点
    
    表示: signal 被 driver 驱动
    """
    signal: str       # 被驱动的信号
    driver: str       # 驱动来源
    kind: str          # 驱动类型 (always_ff, always_comb, continuous)
    line: int = 0
    clock: str = ""   # 关联时钟
    reset: str = ""   # 关联复位
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    caveats: List[str] = field(default_factory=list)


@dataclass
class Connection:
    """端口连接"""
    from_instance: str  # 源实例
    from_port: str      # 源端口
    to_instance: str    # 目标实例
    to_port: str        # 目标端口
    signal: str = ""    # 连接的信号
    line: int = 0


class SemanticGraph:
    """语义关系图
    
    所有 Extractor 的输出聚合。
    """
    
    def __init__(self, scope_tree: ScopeTree, symbol_table: SymbolTable):
        self.scope_tree = scope_tree
        self.symbol_table = symbol_table
        
        # 负载关系: signal → [LoadPoint]
        self.loads: Dict[str, List[LoadPoint]] = {}
        
        # 驱动关系: signal → [DriverPoint]
        self.drivers: Dict[str, List[DriverPoint]] = {}
        
        # 连接关系
        self.connections: List[Connection] = []
        
        # 所有涉及的信号
        self._all_signals: Set[str] = set()
    
    def add_load(self, signal: str, load_by: str, context: str, line: int = 0):
        """添加负载关系"""
        lp = LoadPoint(signal=signal, load_by=load_by, context=context, line=line)
        
        if signal not in self.loads:
            self.loads[signal] = []
        
        # 防重
        for existing in self.loads[signal]:
            if existing.load_by == load_by and existing.context == context:
                return
        
        self.loads[signal].append(lp)
        self._all_signals.add(signal)
        self._all_signals.add(load_by)
    
    def add_driver(self, signal: str, driver: str, kind: str, line: int = 0, 
                   clock: str = "", reset: str = ""):
        """添加驱动关系"""
        dp = DriverPoint(
            signal=signal, driver=driver, kind=kind, 
            line=line, clock=clock, reset=reset
        )
        
        if signal not in self.drivers:
            self.drivers[signal] = []
        
        # 允许多驱动: 不做去重，每条驱动关系都保留
        # 注意: 这意味着同一信号的多个 always_ff 赋值会产生多个 DriverPoint
        self.drivers[signal].append(dp)
        self._all_signals.add(signal)
        self._all_signals.add(driver)
    
    def add_connection(self, from_instance: str, from_port: str,
                       to_instance: str, to_port: str, signal: str = "", line: int = 0):
        """添加连接关系"""
        conn = Connection(
            from_instance=from_instance, from_port=from_port,
            to_instance=to_instance, to_port=to_port,
            signal=signal, line=line
        )
        self.connections.append(conn)
        self._all_signals.add(signal)
    
    def get_load(self, signal: str) -> List[LoadPoint]:
        """获取信号的负载"""
        return self.loads.get(signal, [])
    
    def get_driver(self, signal: str) -> List[DriverPoint]:
        """获取信号的驱动"""
        return self.drivers.get(signal, [])
    
    @property
    def all_signals(self) -> List[str]:
        """所有涉及的信号"""
        return sorted(list(self._all_signals))
    
    def find_load_signals(self) -> List[str]:
        """获取所有被加载的信号（作为 lhs 的信号）"""
        return sorted(list(self.loads.keys()))
    
    def find_driver_signals(self) -> List[str]:
        """获取所有被驱动的信号"""
        return sorted(list(self.drivers.keys()))


class Extractor(ABC):
    """Extractor 基类
    
    所有语义提取器的基类。
    符合铁律 18: 接收 ScopeTree，使用 pyslang.visit()
    """
    
    def __init__(self, scope_tree: ScopeTree, symbol_table: SymbolTable, graph: SemanticGraph, warn_handler=None):
        self.scope = scope_tree
        self.symbols = symbol_table
        self.graph = graph
        self._current_scope_id: str = ""
        self.warn_handler = warn_handler  # 统一警告处理器 (铁律3)
    
    @abstractmethod
    def extract(self, tree) -> None:
        """执行提取，子类必须实现"""
        pass
    
    def resolve_signal(self, name: str, scope_id: str = "") -> Optional[SignalRef]:
        """解析信号引用"""
        if not scope_id:
            scope_id = self._current_scope_id or "root"
        return self.symbols.resolve_reference(name, scope_id)
    
    def _current_scope(self):
        """获取当前作用域"""
        return self.scope.get_scope(self._current_scope_id)
    
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
