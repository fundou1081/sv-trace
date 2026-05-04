"""
Base Classes - 语义类型基类
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import pyslang


class SemanticKind(Enum):
    """语义类型枚举"""
    # 时钟域
    CLOCK_DOMAIN = "clock_domain"
    REGISTER_SIGNAL = "register_signal"
    CLOCKED_ALWAYS_FF = "clocked_always_ff"
    
    # 端口
    PORT_SIGNAL = "port_signal"
    
    # FSM
    FSM_BLOCK = "fsm_block"
    FSM_STATE = "fsm_state"
    FSM_TRANSITION = "fsm_transition"
    
    # 驱动/负载
    DRIVER_SIGNAL = "driver_signal"
    DRIVER_CONNECTION = "driver_connection"
    LOAD_SIGNAL = "load_signal"
    
    # 复位
    RESET_SIGNAL = "reset_signal"
    RESET_DOMAIN = "reset_domain"


@dataclass
class SemanticItem:
    """语义项基类"""
    kind: SemanticKind
    node: pyslang.SyntaxNode  # 底层 pyslang 节点
    module_path: str = ""     # 所在模块路径
    
    @property
    def node_kind(self) -> str:
        """获取底层 pyslang kind 名称"""
        return self.node.kind.name if self.node else ""
    
    @property
    def line_number(self) -> Optional[int]:
        """获取行号"""
        if self.node and hasattr(self.node, 'location') and self.node.location:
            return self.node.location.line
        return None
    
    def __repr__(self):
        return f"{self.kind.value}: {self.module_path}"


def filter_by_kind(items: list[SemanticItem], kind: SemanticKind) -> list:
    """按语义类型筛选"""
    return [item for item in items if item.kind == kind]


def filter_by_node_kind(items: list[SemanticItem], node_kind: str) -> list:
    """按 pyslang node kind 筛选"""
    return [item for item in items if item.node_kind == node_kind]


__all__ = ['SemanticItem', 'SemanticKind', 'filter_by_kind', 'filter_by_node_kind']
