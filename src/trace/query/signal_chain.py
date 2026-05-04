"""SignalChainQuery - 信号完整链路追踪

场景A: 给定信号，追踪其完整链路：drivers → 数据传递 → loads

功能:
- 找到信号的所有上游驱动源
- 找到信号的所有下游负载
- 构建完整的驱动-数据流-负载链路
- 识别时钟/复位路径

遵循开发纪律:
- 铁律1: AST 唯一数据源 - 使用 pyslang visit API
- 铁律2: 位精确性不可妥协 - 保留位选择信息
- 铁律3: 不可信则不输出 - 返回 confidence 和 caveats
- 铁律5: 原子化必须保持 - 组合现有模块，而非重新实现

Example:
    >>> from parse import SVParser
    >>> from trace.query import SignalChainQuery
    >>> 
    >>> parser = SVParser()
    >>> parser.parse_file("design.sv")
    >>> 
    >>> query = SignalChainQuery(parser)
    >>> result = query.trace("data_out", module="Top")
    >>> 
    >>> if result.confidence == "high":
    ...     chain = result.data
    ...     print(f"Drivers: {chain.drivers}")
    ...     print(f"Loads: {chain.loads}")
"""

import sys
import os
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from trace.core.interfaces import TraceResult, DriverInfo, LoadInfo

# 组合现有模块，而非重新实现
from trace.driver import DriverCollector
from trace.load_ext import LoadTracerExt


@dataclass
class SignalChainResult:
    """信号链路追踪结果
    
    Attributes:
        root_signal: 根信号名
        root_module: 根信号所在模块
        drivers: 上游驱动列表
        loads: 下游负载列表
        data_path_signals: 数据传递路径上的中间信号
        clock_signals: 相关的时钟信号
        reset_signals: 相关的复位信号
        confidence: 置信度
        caveats: 不确定性说明
    """
    root_signal: str
    root_module: str
    drivers: List[DriverInfo] = field(default_factory=list)
    loads: List[LoadInfo] = field(default_factory=list)
    data_path_signals: List[str] = field(default_factory=list)
    clock_signals: List[str] = field(default_factory=list)
    reset_signals: List[str] = field(default_factory=list)
    confidence: str = "high"
    caveats: List[str] = field(default_factory=list)
    
    @property
    def has_clock_path(self) -> bool:
        """是否有时钟路径"""
        return len(self.clock_signals) > 0
    
    @property
    def has_reset_path(self) -> bool:
        """是否有复位路径"""
        return len(self.reset_signals) > 0
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "root_signal": self.root_signal,
            "root_module": self.root_module,
            "drivers": [
                {"signal": d.signal, "module": d.module, "kind": d.kind, "sources": d.sources}
                for d in self.drivers
            ],
            "loads": [
                {"signal": l.signal, "module": l.module, "context": l.context}
                for l in self.loads
            ],
            "data_path_signals": self.data_path_signals,
            "clock_signals": self.clock_signals,
            "reset_signals": self.reset_signals,
            "confidence": self.confidence,
            "caveats": self.caveats,
        }


class SignalChainQuery:
    """信号完整链路追踪查询
    
    组合 DriverCollector 和 LoadTracerExt，提供完整的信号链路追踪。
    遵循原子化设计：复用现有模块，不重复实现。
    """
    
    # 时钟/复位信号模式
    CLOCK_PATTERNS = {
        'clk', 'clock', '_clk', '_clock', 'clk_', 'clkin', 'clk_out',
        'i_clk', 'i_clock', 'o_clk', 'o_clock'
    }
    RESET_PATTERNS = {
        'rst', 'reset', '_rst', '_reset', '_rst_n', '_reset_n',
        'preset', 'presetn', 'n', '_n'
    }
    
    def __init__(self, parser, verbose: bool = True):
        """初始化
        
        Args:
            parser: SVParser 实例
            verbose: 是否打印警告
        """
        self.parser = parser
        self.verbose = verbose
        
        # 复用现有模块 (原子化设计)
        self._driver_collector = DriverCollector(parser, verbose=verbose)
        # 使用 LoadTracerExt (带反向查找功能)
        self._load_tracer = LoadTracerExt(parser)
        
        # 信号元信息
        self._signal_modules: Dict[str, str] = {}
        self._clock_signals: Set[str] = set()
        self._reset_signals: Set[str] = set()
        self._enable_signals: Set[str] = set()
        self._reset_signals: Set[str] = set()
        
        # 收集模块信息
        self._collect_module_info()
    
    def _collect_module_info(self) -> None:
        """收集模块和信号信息"""
        for fname, tree in self.parser.trees.items():
            if not tree or not tree.root:
                continue
            self._extract_module_signals(tree.root)
        
        # 分类时钟/复位信号
        self._classify_clock_reset()
    
    def _extract_module_signals(self, root) -> None:
        """从 AST 提取模块和信号信息
        
        使用 pyslang 官方 API (node.declarators) 而非手动遍历 children。
        遵循铁律1: AST 唯一数据源。
        """
        current_module = ""
        
        def visitor(node):
            nonlocal current_module
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else ""
                
                # 模块声明
                if kind_name == 'ModuleDeclaration':
                    if hasattr(node, 'header') and hasattr(node.header, 'name'):
                        name = node.header.name
                        if hasattr(name, 'text'):
                            current_module = name.text.strip()
                        else:
                            current_module = str(name).strip()
                
                # 数据声明 - 使用 pyslang 的 node.declarators API
                elif kind_name == 'DataDeclaration':
                    declarators = getattr(node, 'declarators', None)
                    if declarators:
                        for decl in declarators:
                            decl_name = self._get_name(decl)
                            if decl_name:
                                self._signal_modules[decl_name] = current_module
                
                # 端口声明
                elif kind_name in {'PortDeclaration', 'ImplicitAnsiPort', 
                                   'InterfacePortDeclaration'}:
                    name = self._get_name(node)
                    if name:
                        self._signal_modules[name] = current_module
                
            except Exception:
                pass
            return True  # 继续遍历
        
        root.visit(visitor)
    
    def _get_name(self, node) -> Optional[str]:
        """获取节点名称 (带 strip)"""
        try:
            if hasattr(node, 'name') and node.name:
                if hasattr(node.name, 'text'):
                    return node.name.text.strip()
                return str(node.name).strip()
            if hasattr(node, 'member') and node.member:
                if hasattr(node.member, 'text'):
                    return node.member.text.strip()
            if hasattr(node, 'text'):
                return node.text.strip()
        except Exception:
            pass
        return None
    
    def _classify_clock_reset(self) -> None:
        """分类时钟、复位和使能信号
        
        基于 AST 分析的启发式分类：
        1. 时钟: 在 posedge/negedge 事件中，但不在 if 条件中
        2. 复位: 在 posedge/negedge 事件中，也在 if 条件中
        3. 使能: 在 if 条件中，但不在事件中
        
        辅助: 如果 AST 分析无法分类，使用名称模式匹配。
        """
        # 基于 AST 分析收集信号使用特征
        event_signals = set()
        condition_signals = set()
        
        for fname, tree in self.parser.trees.items():
            if not tree or not tree.root:
                continue
            self._analyze_signal_usage(tree.root, event_signals, condition_signals)
        
        # 基于使用特征分类
        # 时钟: 在事件中，不在条件中
        for sig in event_signals - condition_signals:
            if sig in self._signal_modules:
                self._clock_signals.add(sig)
        
        # 复位: 在事件中，也在条件中
        for sig in event_signals & condition_signals:
            if sig in self._signal_modules:
                self._reset_signals.add(sig)
        
        # 使能: 在条件中，不在事件中
        for sig in condition_signals - event_signals:
            if sig in self._signal_modules:
                self._enable_signals.add(sig)
        
        # 辅助: 名称模式匹配 (处理未被 AST 分析到的信号)
        # 使用单词边界匹配，避免部分匹配问题
        import re
        clock_re = re.compile(r'.*(_clk$|_clock$|clk$|clock$|i_clk$|o_clk$|i_clock$|o_clock$|^clk)', re.IGNORECASE)
        reset_re = re.compile(r'.*(_rst$|_reset$|rst$|reset$|_rst_n$|_reset_n$|preset$|presetn$)', re.IGNORECASE)
        
        for sig in self._signal_modules:
            if sig in self._clock_signals or sig in self._reset_signals:
                continue
            if clock_re.match(sig):
                self._clock_signals.add(sig)
            if reset_re.match(sig):
                self._reset_signals.add(sig)
    
    def _analyze_signal_usage(self, root, event_signals: set, condition_signals: set) -> None:
        """分析 AST 中信号的使用场景
        
        基于 AST 的启发式分类：
        - 时钟: 在 posedge/negedge 事件控制中，但不在 if 条件中
        - 复位: 在 posedge/negedge 事件控制中，也在 if 条件中
        - 使能: 在 if 条件中，但不在事件控制中
        
        Args:
            root: AST 根节点
            event_signals: 输出 - 在事件控制中的信号集合
            condition_signals: 输出 - 在条件判断中的信号集合
        """
        import pyslang
        
        def collect_ids(node, result_set):
            """收集节点中的所有标识符"""
            if node is None:
                return
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else ''
                if 'Identifier' in kind_name:
                    sig = str(node).strip()
                    if sig:
                        result_set.add(sig)
                for child in node:
                    collect_ids(child, result_set)
            except:
                pass
        
        def visitor(node):
            kind_name = node.kind.name if hasattr(node.kind, 'name') else ''
            
            # 收集事件控制中的信号 (posedge/negedge)
            if kind_name == 'SignalEventExpression':
                collect_ids(node, event_signals)
            
            # 收集条件判断中的信号 (仅 ConditionalStatement 的 predicate)
            # 注意：只收集 if 条件中的信号，不收集整个 always 块中的信号
            if kind_name == 'ConditionalStatement':
                pred = getattr(node, 'predicate', None)
                if pred:
                    collect_ids(pred, condition_signals)
            
            return pyslang.VisitAction.Advance
        
        root.visit(visitor)
    
    def trace(self, signal: str, module: str = None, 
              max_depth: int = 10) -> TraceResult:
        """追踪信号完整链路
        
        Args:
            signal: 信号名
            module: 所在模块 (可选)
            max_depth: 最大追溯深度
            
        Returns:
            TraceResult[SignalChainResult]: 追踪结果
        """
        # 确定模块
        target_module = module or self._signal_modules.get(signal, "")
        
        if not target_module:
            return TraceResult.uncertain(
                data=None,
                reason=f"Signal '{signal}' not found in any module"
            )
        
        # 收集驱动 (使用现有模块)
        drivers = self._collect_drivers(signal, target_module, max_depth)
        
        # 收集负载 (使用 LoadTracerExt)
        loads = self._collect_loads(signal, target_module, max_depth)
        
        # 构建数据路径信号
        data_signals = self._build_data_path(drivers, loads)
        
        # 评估置信度
        confidence, caveats = self._assess_confidence(
            signal, target_module, drivers, loads
        )
        
        result = SignalChainResult(
            root_signal=signal,
            root_module=target_module,
            drivers=drivers,
            loads=loads,
            data_path_signals=data_signals,
            clock_signals=list(self._clock_signals),
            reset_signals=list(self._reset_signals),
            confidence=confidence,
            caveats=caveats,
        )
        
        return TraceResult(data=result, confidence=confidence, caveats=caveats)
    
    def _collect_drivers(self, signal: str, module: str,
                        max_depth: int) -> List[DriverInfo]:
        """收集驱动信息 - 委托给 DriverCollector"""
        result = []
        visited = set()
        
        def collect(sig: str, depth: int):
            if depth >= max_depth or sig in visited:
                return
            visited.add(sig)
            
            # 使用 DriverCollector
            drivers = self._driver_collector.find_driver(sig)
            for d in drivers:
                # 转换为 DriverInfo
                info = DriverInfo(
                    signal=d.signal,
                    module=d.module,
                    kind=d.kind.name.lower() if hasattr(d.kind, 'name') else str(d.kind),
                    sources=d.sources,
                    clock=d.clock,
                    reset=d.reset,
                    enable=d.enable,
                    condition=d.condition,
                    lines=d.lines,
                    confidence=self._assess_driver_confidence(d),
                    caveats=[],
                )
                result.append(info)
                
                # 递归收集上游
                for src in d.sources:
                    collect(src, depth + 1)
        
        collect(signal, 0)
        return result
    
    def _collect_loads(self, signal: str, module: str,
                      max_depth: int) -> List[LoadInfo]:
        """收集负载信息 - 使用 LoadTracerExt.reverse_lookup
        
        LoadTracerExt.reverse_lookup(sig) 返回使用 sig 作为驱动的 LoadPoint。
        LoadPoint.signal = 被驱动的信号 (目标)
        LoadPoint.driver = 驱动源 (即 sig)
        """
        result = []
        visited = set()
        
        def collect(sig: str, depth: int):
            if depth >= max_depth or sig in visited:
                return
            visited.add(sig)
            
            # 使用 reverse_lookup (反向查找: 谁使用 sig 作为源)
            loads = self._load_tracer.reverse_lookup(sig)
            for load in loads:
                # load.signal = 被驱动的信号, load.driver = 驱动源 (即 sig)
                info = LoadInfo(
                    signal=load.signal,  # 被驱动的信号
                    module=module,
                    context=f"{load.driver_type}",  # 驱动类型
                    line=0,
                    condition=load.condition if hasattr(load, 'condition') else "",
                    confidence="high" if load.driver_type else "medium",
                    caveats=[] if load.driver_type else ["Unknown driver type"],
                )
                result.append(info)
        
        collect(signal, 0)
        return result
    
    def _assess_driver_confidence(self, driver) -> str:
        """评估驱动信息的置信度"""
        if not driver.sources:
            return "uncertain"
        return "high"
    
    def _build_data_path(self, drivers: List[DriverInfo],
                        loads: List[LoadInfo]) -> List[str]:
        """构建数据路径"""
        signals = set()
        for d in drivers:
            signals.update(d.sources)
        for l in loads:
            signals.add(l.signal)
        return list(signals)
    
    def _assess_confidence(self, signal: str, module: str,
                          drivers: List[DriverInfo],
                          loads: List[LoadInfo]) -> Tuple[str, List[str]]:
        """评估置信度"""
        caveats = []
        
        if not drivers and not loads:
            caveats.append(f"No drivers or loads found for {signal} in {module}")
            return "uncertain", caveats
        
        # 检查是否有空 sources
        drivers_with_empty_sources = sum(1 for d in drivers if not d.sources)
        if drivers_with_empty_sources > 0:
            caveats.append(
                f"{drivers_with_empty_sources} driver(s) have empty sources - "
                "RHS extraction may be incomplete"
            )
        
        if not drivers:
            caveats.append(f"No drivers found for {signal}")
        
        if not loads:
            caveats.append(f"No loads found for {signal}")
        
        confidence = "high"
        if caveats:
            confidence = "medium" if drivers else "uncertain"
        
        return confidence, caveats
