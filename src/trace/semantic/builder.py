"""
Trace Semantic Builder - 语义层适配器
"""

from typing import Dict, List, Optional
import pyslang

from semantic import (
    SemanticCollector,
    SignalItem,
    PortItem,
    DriverSignal,
    NonBlockingAssign,
    BlockingAssign,
    ContinuousAssign,
    FSMStateItem,
    ClockDomainItem,
    RegisterItem,
)

from core.models import Driver, DriverKind, AssignKind


class TraceSemanticBuilder:
    """Trace 模块语义构建器"""
    
    def __init__(self, trees: dict, verbose: bool = False):
        self.trees = trees
        self.verbose = verbose
        self.collector = SemanticCollector()
        self._drivers: Dict[str, List[Driver]] = {}
        self._signals: Dict[str, SignalItem] = {}
        self._module_path = ""
        self._built = False
    
    def build(self) -> 'TraceSemanticBuilder':
        for filename, tree in self.trees.items():
            if not tree or not tree.root:
                continue
            self._module_path = self._extract_module_name(tree.root)
            self.collector.collect(tree, filename)
        
        self._build_signals()
        self._build_drivers()
        self._built = True
        return self
    
    def _extract_module_name(self, root) -> str:
        for node in root:
            if node.kind.name == 'ModuleHeader':
                for child in node:
                    if child.kind.name == 'Identifier':
                        return str(child.value) if hasattr(child, 'value') else str(child)
        return "unknown"
    
    def _find_identifier_in_node(self, node) -> str:
        """从节点及其子节点中查找标识符"""
        for child in node:
            kn = child.kind.name
            # Identifier 或 IdentifierName 都可以
            if kn in ('Identifier', 'IdentifierName'):
                return str(child.value) if hasattr(child, 'value') else str(child)
        return ""
    
    def _build_signals(self) -> None:
        for item in self.collector.get_by_type(SignalItem):
            name = self._find_identifier_in_node(item.node)
            if name:
                path = f"{self._module_path}.{name}"
                item.path = path
                self._signals[path] = item
    
    def _build_drivers(self) -> None:
        for item in self.collector.get_by_type(DriverSignal):
            # 从 NonblockingAssignmentExpression 的第一个子节点获取左值
            name = ""
            for child in item.node:
                kn = child.kind.name
                if kn in ('Identifier', 'IdentifierName'):
                    name = str(child.value) if hasattr(child, 'value') else str(child)
                    break
            
            if name:
                path = f"{self._module_path}.{name}"
                item.signal_path = path
                
                kind = AssignKind.Nonblocking if item.is_nonblocking else AssignKind.Blocking
                driver = Driver(
                    signal=path,
                    kind=DriverKind.AlwaysFF,
                    sources=[],
                    module=self._module_path,
                    lines=[item.line_number] if item.line_number else [],
                    assign_kind=kind,
                )
                if path not in self._drivers:
                    self._drivers[path] = []
                self._drivers[path].append(driver)
    
    def get_drivers(self, pattern: str = '*') -> List[Driver]:
        if pattern == '*':
            result = []
            for drivers in self._drivers.values():
                result.extend(drivers)
            return result
        result = []
        for path, drivers in self._drivers.items():
            if pattern in path:
                result.extend(drivers)
        return result
    
    def find_driver(self, signal: str) -> List[Driver]:
        return self._drivers.get(signal, [])
    
    def get_signal(self, path: str) -> Optional[SignalItem]:
        return self._signals.get(path)
    
    def get_clocks(self) -> List[SignalItem]:
        return [s for s in self._signals.values() if s.is_clock]
    
    def get_resets(self) -> List[SignalItem]:
        return [s for s in self._signals.values() if s.is_reset]
    
    def get_registers(self) -> List[RegisterItem]:
        return self.collector.get_by_type(RegisterItem)
    
    def get_fsm_states(self) -> List[FSMStateItem]:
        return self.collector.get_by_type(FSMStateItem)
    
    def get_clock_domains(self) -> List[ClockDomainItem]:
        return self.collector.get_by_type(ClockDomainItem)


class DriverCollector:
    """兼容旧接口"""
    
    def __init__(self, trees: dict, verbose: bool = False):
        self.verbose = verbose
        self.trees = trees
        self.builder = TraceSemanticBuilder(trees, verbose).build()
        self.drivers = self.builder._drivers
    
    def get_drivers(self, pattern: str = '*') -> List[Driver]:
        return self.builder.get_drivers(pattern)
    
    def find_driver(self, signal: str) -> List[Driver]:
        return self.builder.find_driver(signal)
    
    def get_all_signals(self) -> List[str]:
        return list(self.builder._signals.keys())


__all__ = ['TraceSemanticBuilder', 'DriverCollector']
