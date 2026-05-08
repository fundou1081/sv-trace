"""Semantic 增强层数据模型

EnrichedSemanticGraph 和相关类型定义。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

from extractors.base import SemanticGraph, LoadPoint, DriverPoint, ConfidenceLevel


@dataclass
class EnrichedLoadPoint:
    """增强后的负载点
    
    在 LoadPoint 基础上添加置信度和描述。
    """
    raw: LoadPoint
    
    # Enricher 自动填充
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    caveats: List[str] = field(default_factory=list)
    description: str = ""
    
    # AGENT 填充
    business_meaning: str = ""
    tags: List[str] = field(default_factory=list)
    user_notes: str = ""


@dataclass
class EnrichedDriverPoint:
    """增强后的驱动点
    
    在 DriverPoint 基础上添加置信度和描述。
    """
    raw: DriverPoint
    
    # Enricher 自动填充
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    caveats: List[str] = field(default_factory=list)
    description: str = ""
    
    # AGENT 填充
    business_meaning: str = ""
    tags: List[str] = field(default_factory=list)
    user_notes: str = ""


@dataclass
class EnrichedSignal:
    """增强后的信号
    
    代表一个经过语义增强的信号。
    """
    signal_name: str
    resolved_name: str = ""
    scope_id: str = ""
    
    # Enricher 自动填充
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    caveats: List[str] = field(default_factory=list)
    description: str = ""
    
    # AGENT 填充
    business_meaning: str = ""
    tags: List[str] = field(default_factory=list)
    user_notes: str = ""
    
    # 关联关系
    loads: List[EnrichedLoadPoint] = field(default_factory=list)
    drivers: List[EnrichedDriverPoint] = field(default_factory=list)


@dataclass
class EnrichedSemanticGraph:
    """增强后的语义图
    
    在 SemanticGraph 基础上添加语义增强信息。
    
    符合铁律 21: Semantic 层消费 extractors 输出的 SemanticGraph，
    不得直接遍历 AST。
    """
    base: SemanticGraph
    
    # 增强后的信号信息 (signal_name → EnrichedSignal)
    enriched_signals: Dict[str, EnrichedSignal] = field(default_factory=dict)
    
    # AGENT 上下文引用
    agent_context: Optional['AgentContext'] = None
    
    def get_enriched_signal(self, signal: str) -> Optional[EnrichedSignal]:
        """获取增强后的信号"""
        return self.enriched_signals.get(signal)
    
    def add_enriched_signal(self, sig: EnrichedSignal):
        """添加增强后的信号"""
        self.enriched_signals[sig.signal_name] = sig
    
    @property
    def all_signals(self) -> List[str]:
        """所有涉及的信号"""
        return self.base.all_signals
    
    def find_signals_by_tag(self, tag: str) -> List[str]:
        """按标签查找信号"""
        return [
            sig for sig, es in self.enriched_signals.items()
            if tag in es.tags
        ]
    
    def find_signals_by_confidence(self, confidence: ConfidenceLevel) -> List[str]:
        """按置信度查找信号"""
        return [
            sig for sig, es in self.enriched_signals.items()
            if es.confidence == confidence
        ]
