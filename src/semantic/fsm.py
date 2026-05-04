"""
FSM - 状态机相关语义类型
"""
from dataclasses import dataclass, field
from typing import List, Optional
import pyslang

from .base import SemanticItem, SemanticKind


@dataclass
class FSMState:
    """FSM 状态"""
    kind: SemanticKind = field(default=SemanticKind.FSM_STATE)
    node: pyslang.SyntaxNode = None
    
    state_name: str = ""             # 状态名
    state_encoding: Optional[int] = None  # 状态编码 (可选)
    
    # FSM 上下文
    fsm_path: str = ""              # FSM 路径
    state_index: int = 0             # 状态索引
    
    # 转换
    transitions: List[str] = field(default_factory=list)  # 目标状态名列表
    
    module_path: str = ""


@dataclass
class FSMTransition:
    """FSM 状态转换"""
    kind: SemanticKind = field(default=SemanticKind.FSM_TRANSITION)
    node: pyslang.SyntaxNode = None
    
    from_state: str = ""             # 起始状态
    to_state: str = ""              # 目标状态
    
    condition: str = ""               # 转换条件
    
    fsm_path: str = ""               # FSM 路径
    module_path: str = ""
    
    @property
    def is_default(self) -> bool:
        """是否是默认转换"""
        return self.condition == "" or self.condition == "default"


@dataclass
class FSMBlock:
    """FSM 块 (完整的FSM)"""
    kind: SemanticKind = field(default=SemanticKind.FSM_BLOCK)
    node: pyslang.SyntaxNode = None
    
    fsm_path: str = ""               # FSM 路径
    state_variable: str = ""         # 状态变量路径
    
    # 状态
    states: List[FSMState] = field(default_factory=list)
    current_state: Optional[str] = None  # 当前状态名
    reset_state: Optional[str] = None    # 复位状态
    
    # 转换
    transitions: List[FSMTransition] = field(default_factory=list)
    
    # FSM 类型
    fsm_style: str = "sequential"   # sequential/onehot/gray
    
    module_path: str = ""
    line_number: int = 0
    
    def get_state(self, name: str) -> Optional[FSMState]:
        """获取状态"""
        for state in self.states:
            if state.state_name == name:
                return state
        return None
    
    def get_transitions_from(self, state_name: str) -> List[FSMTransition]:
        """获取从某状态出发的转换"""
        return [t for t in self.transitions if t.from_state == state_name]
    
    def get_transitions_to(self, state_name: str) -> List[FSMTransition]:
        """获取到某状态的转换"""
        return [t for t in self.transitions if t.to_state == state_name]


__all__ = ['FSMState', 'FSMTransition', 'FSMBlock']
