"""FSM Items - 状态机语义类型

按项目纪律：实现 __post_init__ 提取状态机信息
"""

from dataclasses import dataclass, field
from typing import Set, ClassVar, List
import pyslang

from .base import SemanticItem


# 使用公共工具函数
from .utils import extract_identifier as _extract_identifier




@dataclass
class FSMStateItem(SemanticItem):
    """FSM 状态"""
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'CaseStatement',
        'CaseItem',
    }
    
    state_name: str = ""
    state_value: int = 0
    
    def __post_init__(self):
        if not self.node:
            return
        
        # 从 case item 提取状态名
        self.state_name = _extract_identifier(self.node)
        
        # 尝试提取值
        if hasattr(self.node, 'condition'):
            cond = self.node.condition
            if cond:
                try:
                    self.state_value = int(str(cond))
                except:
                    self.state_value = 0


@dataclass
class FSMStateRegister(FSMStateItem):
    """FSM 状态寄存器"""
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'CaseStatement',
    }
    
    current_state: str = ""
    next_state: str = ""
    state_encoding: str = "binary"


@dataclass
class FSMTransitionItem(SemanticItem):
    """FSM 状态转换"""
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'AssignmentExpression',
    }
    
    from_state: str = ""
    to_state: str = ""
    condition: str = ""
    
    def __post_init__(self):
        if not self.node:
            return
        # 简化：提取完整表达式作为条件
        self.condition = str(self.node)


__all__ = ['FSMStateItem', 'FSMStateRegister', 'FSMTransitionItem']
