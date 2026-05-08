"""Agent Context - AGENT 上下文接口

AGENT 通过此接口填充业务语义信息。
"""

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class AgentContext:
    """AGENT 上下文
    
    用于存储 AGENT 填充的业务语义信息。
    
    AGENT 可以通过此接口为信号添加：
    - business_meaning: 商业含义（如"这是数据有效信号"）
    - tags: 标签（如 ["clock", "reset", "data_valid"]）
    - user_notes: 用户备注
    - confidence_overrides: 置信度覆盖
    
    符合铁律 21: AGENT 通过此接口填充业务语义，
    Semantic 层负责将这些信息聚合到 EnrichedSemanticGraph。
    """
    
    def __init__(self):
        # signal → business meaning
        self._business_meanings: Dict[str, str] = {}
        
        # signal → tags
        self._tags: Dict[str, List[str]] = {}
        
        # signal → user notes
        self._user_notes: Dict[str, str] = {}
        
        # signal → confidence override
        self._confidence_overrides: Dict[str, str] = {}
        
        # signal → metadata (其他任意信息)
        self._metadata: Dict[str, Dict] = {}
    
    def set_business_meaning(self, signal: str, meaning: str):
        """设置信号的商业含义"""
        self._business_meanings[signal] = meaning
    
    def get_business_meaning(self, signal: str) -> str:
        """获取信号的商业含义"""
        return self._business_meanings.get(signal, "")
    
    def set_tags(self, signal: str, tags: List[str]):
        """设置信号标签"""
        self._tags[signal] = tags
    
    def add_tag(self, signal: str, tag: str):
        """添加单个标签"""
        if signal not in self._tags:
            self._tags[signal] = []
        if tag not in self._tags[signal]:
            self._tags[signal].append(tag)
    
    def get_tags(self, signal: str) -> List[str]:
        """获取信号标签"""
        return self._tags.get(signal, [])
    
    def set_user_note(self, signal: str, note: str):
        """设置用户备注"""
        self._user_notes[signal] = note
    
    def get_user_note(self, signal: str) -> str:
        """获取用户备注"""
        return self._user_notes.get(signal, "")
    
    def set_confidence_override(self, signal: str, confidence: str):
        """设置置信度覆盖
        
        Args:
            signal: 信号名
            confidence: "high", "medium", "low", "uncertain"
        """
        self._confidence_overrides[signal] = confidence
    
    def get_confidence_override(self, signal: str) -> Optional[str]:
        """获取置信度覆盖"""
        return self._confidence_overrides.get(signal)
    
    def set_metadata(self, signal: str, key: str, value):
        """设置任意元数据"""
        if signal not in self._metadata:
            self._metadata[signal] = {}
        self._metadata[signal][key] = value
    
    def get_metadata(self, signal: str, key: str, default=None):
        """获取元数据"""
        return self._metadata.get(signal, {}).get(key, default)
    
    def has_signal(self, signal: str) -> bool:
        """检查是否有该信号的上下文"""
        return (
            signal in self._business_meanings or
            signal in self._tags or
            signal in self._user_notes or
            signal in self._confidence_overrides
        )
    
    def get_signals(self) -> List[str]:
        """获取所有有上下文的信号"""
        signals = set()
        signals.update(self._business_meanings.keys())
        signals.update(self._tags.keys())
        signals.update(self._user_notes.keys())
        signals.update(self._confidence_overrides.keys())
        return sorted(list(signals))
    
    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "business_meanings": self._business_meanings,
            "tags": self._tags,
            "user_notes": self._user_notes,
            "confidence_overrides": self._confidence_overrides,
            "metadata": self._metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AgentContext':
        """从字典恢复"""
        ctx = cls()
        ctx._business_meanings = data.get("business_meanings", {})
        ctx._tags = data.get("tags", {})
        ctx._user_notes = data.get("user_notes", {})
        ctx._confidence_overrides = data.get("confidence_overrides", {})
        ctx._metadata = data.get("metadata", {})
        return ctx
    
    def to_json(self, path: str):
        """保存到文件"""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def from_json(cls, path: str) -> 'AgentContext':
        """从文件加载"""
        with open(path) as f:
            data = json.load(f)
        return cls.from_dict(data)
