"""Traceable 接口定义

所有 trace 模块的输出必须实现此接口。

遵循开发纪律:
- 铁律4: 模型即契约 - 每个字段必须有对应的AST填充代码
- 铁律6: Schema 即宪法 - 输出必须遵循 Schema 定义
- 铁律10: API 返回必须有置信度标注

Example:
    >>> from trace.core.interfaces import Traceable, TraceResult
    >>> 
    >>> class MyResult(Traceable):
    ...     def __init__(self):
    ...         self._confidence = "high"
    ...         self._caveats = []
    ...     
    ...     @property
    ...     def node_id(self) -> str:
    ...         return "module.signal"
    ...     
    ...     @property
    ...     def confidence(self) -> str:
    ...         return self._confidence
    ...     
    ...     @property
    ...     def caveats(self) -> List[str]:
    ...         return self._caveats
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Any


class Traceable(ABC):
    """可追踪接口 - 所有 trace 输出必须实现此接口
    
    Attributes:
        node_id: 唯一标识，格式: module.signal[bit]
        confidence: 置信度: high/medium/uncertain
        caveats: 不确定性说明列表
    """
    
    @property
    @abstractmethod
    def node_id(self) -> str:
        """唯一标识
        
        Returns:
            str: 格式为 "module.signal" 或 "module.signal[bit]"
        """
        pass
    
    @property
    @abstractmethod
    def confidence(self) -> str:
        """置信度
        
        Returns:
            str: high/medium/uncertain
        """
        pass
    
    @property
    @abstractmethod
    def caveats(self) -> List[str]:
        """不确定性说明
        
        当 confidence 不是 high 时必须提供详细信息。
        
        Returns:
            List[str]: 说明列表
        """
        pass


@dataclass
class TraceResult:
    """通用追踪结果包装器
    
    所有 API 返回必须使用此包装器，确保包含置信度和警告信息。
    """
    data: Any = None                    # 实际数据
    confidence: str = "high"           # 置信度
    caveats: List[str] = field(default_factory=list)  # 不确定性说明
    warnings: List[str] = field(default_factory=list)  # 警告信息
    
    def __post_init__(self):
        """验证置信度"""
        valid = {"high", "medium", "uncertain"}
        if self.confidence not in valid:
            raise ValueError(f"confidence must be one of {valid}, got {self.confidence}")
    
    @property
    def is_trusted(self) -> bool:
        """数据是否可信"""
        return self.confidence == "high" and not self.caveats
    
    @classmethod
    def ok(cls, data: Any) -> "TraceResult":
        """创建成功结果"""
        return cls(data=data, confidence="high")
    
    @classmethod
    def uncertain(cls, data: Any, reason: str) -> "TraceResult":
        """创建不确定结果"""
        return cls(data=data, confidence="uncertain", caveats=[reason])
    
    @classmethod
    def warn(cls, data: Any, warning: str) -> "TraceResult":
        """创建带警告的结果"""
        return cls(data=data, confidence="medium", warnings=[warning])


@dataclass
class SignalInfo:
    """信号基本信息"""
    name: str
    module: str
    width: Optional[tuple] = None  # (msb, lsb)
    bit_range: Optional[str] = None  # "[7:0]"
    
    @property
    def node_id(self) -> str:
        """生成唯一标识"""
        if self.bit_range:
            return f"{self.module}.{self.name}{self.bit_range}"
        return f"{self.module}.{self.name}"


@dataclass
class DriverInfo:
    """驱动信息 - 实现 Traceable"""
    signal: str
    module: str
    kind: str                    # always_ff, always_comb, assign
    sources: List[str] = field(default_factory=list)
    clock: str = ""
    reset: str = ""
    enable: str = ""
    condition: str = ""
    lines: List[int] = field(default_factory=list)
    confidence: str = "high"
    caveats: List[str] = field(default_factory=list)
    
    @property
    def node_id(self) -> str:
        return f"{self.module}.{self.signal}"


@dataclass
class LoadInfo:
    """负载信息 - 实现 Traceable"""
    signal: str
    module: str
    context: str                 # 出现上下文
    line: int = 0
    condition: str = ""
    confidence: str = "high"
    caveats: List[str] = field(default_factory=list)
    
    @property
    def node_id(self) -> str:
        return f"{self.module}.{self.signal}"


@dataclass
class ConnectionInfo:
    """连接信息 - 实现 Traceable"""
    source_module: str
    source_signal: str
    dest_module: str
    dest_signal: str
    port_direction: str = ""    # input, output, inout
    confidence: str = "high"
    caveats: List[str] = field(default_factory=list)
    
    @property
    def node_id(self) -> str:
        return f"{self.source_module}.{self.source_signal}->{self.dest_module}.{self.dest_signal}"
