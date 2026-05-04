"""
FSM Items - 状态机语义类型

实际的 pyslang kind:
- StandardCaseItem: case 分支 (state: ...)
- DefaultCaseItem: default 分支
- CaseGenerate: case 语句
- Identifier: 标识符
"""

from dataclasses import dataclass, field
from typing import Set, ClassVar, List, Optional
import pyslang

from .base import SemanticItem


@dataclass
class FSMStateItem(SemanticItem):
    """
    FSM 状态项
    
    多种 AST 来源:
    - StandardCaseItem: case 分支
    - DefaultCaseItem: default 分支
    - Identifier: 状态标识符
    """
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'StandardCaseItem',
        'DefaultCaseItem',
        'Identifier',
    }
    
    state_name: str = ""
    state_encoding: Optional[int] = None
    fsm_path: str = ""
    
    @property
    def is_default(self) -> bool:
        return self.kind_name == 'DefaultCaseItem'


@dataclass
class FSMTransitionItem(SemanticItem):
    """
    FSM 状态转换
    
    AST: StandardCaseItem / DefaultCaseItem
    """
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'StandardCaseItem',
        'DefaultCaseItem',
    }
    
    from_state: str = ""
    to_state: str = ""
    condition: str = ""
    fsm_path: str = ""
    
    @property
    def is_default(self) -> bool:
        return self.kind_name == 'DefaultCaseItem'


__all__ = ['FSMStateItem', 'FSMTransitionItem']
