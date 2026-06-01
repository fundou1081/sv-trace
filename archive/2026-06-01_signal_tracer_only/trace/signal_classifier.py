"""SignalClassifier - 信号分类器 (重构版)

将信号自动分类为 clock/reset/data/control/port/status
基于 SVManager 和 DriverTracer

按项目纪律重构:
- 输入: SVManager  
- 复用 DriverTracer 的时钟/复位提取
"""

import re
from enum import Enum
from dataclasses import dataclass, field
from typing import Set, Optional, Dict


class SignalCategory(Enum):
    """信号分类"""
    CLOCK = "clock"
    RESET = "reset" 
    DATA = "data"
    CONTROL = "control"
    PORT = "port"
    STATUS = "status"
    UNKNOWN = "unknown"


@dataclass
class SignalInfo:
    """信号信息"""
    name: str
    category: SignalCategory = SignalCategory.UNKNOWN
    drivers: list = field(default_factory=list)


class SignalClassifier:
    """信号分类器 (重构版)"""
    
    def __init__(self, parser: Optional['SVManager'] = None, verbose: bool = True):
        self.parser = parser
        self.verbose = verbose
        self._clocks = set()
        self._resets = set()
        self._data = set()
        self._control = set()
        self._signals: Dict[str, SignalInfo] = {}
    
    @property
    def all_clocks(self) -> Set[str]:
        return self._clocks
    
    @property
    def all_resets(self) -> Set[str]:
        return self._resets
    
    def all_data_signals(self) -> Set[str]:
        return self._data
    
    def all_control_signals(self) -> Set[str]:
        return self._control
    
    def classify_all(self, parser: 'SVManager') -> 'SignalClassifier':
        """对所有信号分类
        
        Args:
            parser: SVManager 实例
            
        Returns:
            self
        """
        from trace.driver import DriverCollector
        from core.models import DriverKind
        
        self._clocks.clear()
        self._resets.clear()
        self._signals.clear()
        
        if not parser or not parser.trees:
            return self
        
        # 1. 从 DriverTracer 获取 clock/reset 信号
        for filepath, tree in parser.trees.items():
            dc = DriverCollector(parser)
            dc.collect(tree, filepath)
            
            for sig in dc.drivers:
                drivers = dc.drivers[sig]
                
                # 检查是否有 AlwaysFF 类型的驱动（时序逻辑才有真正的clock/reset）
                has_clock = False
                has_reset = False
                
                for d in drivers:
                    # 只有 AlwaysFF 类型的才算时序逻辑
                    if d.kind == DriverKind.AlwaysFF:
                        if d.clock:
                            has_clock = True
                        if d.reset:
                            has_reset = True
                
                # 只有 AlwaysFF 有 clock+reset 才分类为 clock 信号
                if has_clock and has_reset:
                    if sig not in self._signals:
                        self._signals[sig] = SignalInfo(
                            name=sig,
                            category=SignalCategory.CLOCK,
                            drivers=drivers
                        )
                    self._clocks.add(sig)
                    self._resets.add(sig)
                elif has_clock:
                    # 有clock但没有reset的分类为一般的时序信号
                    if sig not in self._signals:
                        self._signals[sig] = SignalInfo(
                            name=sig,
                            category=SignalCategory.CLOCK,
                            drivers=drivers
                        )
                    self._clocks.add(sig)
                elif has_reset:
                    if sig not in self._signals:
                        self._signals[sig] = SignalInfo(
                            name=sig,
                            category=SignalCategory.RESET,
                            drivers=drivers
                        )
                    self._resets.add(sig)
        
        # 2. 对其他信号按模式匹配分类
        self._classify_by_pattern()
        
        return self
    
    def _classify_by_pattern(self):
        """通过模式匹配分类未分类的信号"""
        # 数据信号模式
        DATA_PATTERNS = ['data', 'din', 'dout', 'wdata', 'rdata']
        # 控制信号模式
        CONTROL_PATTERNS = ['valid', 'ready', 'enable', 'start', 'stop']
        
        for sig in self._signals:
            if self._signals[sig].category != SignalCategory.UNKNOWN:
                continue
            
            matched = False
            
            # Data
            for p in DATA_PATTERNS:
                if p in sig.lower():
                    self._signals[sig].category = SignalCategory.DATA
                    self._data.add(sig)
                    matched = True
                    break
            
            if matched:
                continue
            
            # Control  
            for p in CONTROL_PATTERNS:
                if p in sig.lower():
                    self._signals[sig].category = SignalCategory.CONTROL
                    self._control.add(sig)
                    matched = True
                    break
