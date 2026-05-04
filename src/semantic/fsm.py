"""
FSM Items - 状态机语义类型

支持的 AST kind:
- Identifier: case 语句中的状态名 (data_flow.state)
- CaseItem: case 分支项 (data_flow.IDLE: ...)
- EnumLiteral: 枚举字面量
- VariableDeclarator: 状态寄存器声明 (logic [7:0] state;)
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
    - Identifier: case 中的状态名
    - CaseItem: case 分支
    - EnumLiteral: 枚举字面量
    - VariableDeclarator: 状态寄存器
    """
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'Identifier',
        'CaseItem',
        'EnumLiteral',
        'VariableDeclarator',
    }
    
    state_name: str = ""
    state_encoding: Optional[int] = None
    fsm_path: str = ""
    state_index: int = 0
    
    def _extract_state_name(self) -> str:
        """提取状态名"""
        for child in self.node:
            if child.kind.name == 'Identifier':
                return str(child.value) if hasattr(child, 'value') else str(child)
            if child.kind.name == 'EnumLiteral':
                return str(child.value) if hasattr(child, 'value') else str(child)
        return ""


@dataclass
class FSMTransitionItem(SemanticItem):
    """
    FSM 状态转换
    
    AST 来源: CaseItem (包含 from/to 信息)
    """
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'CaseItem',
    }
    
    from_state: str = ""
    to_state: str = ""
    condition: str = ""
    fsm_path: str = ""
    
    @property
    def is_default(self) -> bool:
        return self.condition in ("", "default", "*")


__all__ = ['FSMStateItem', 'FSMTransitionItem']
