"""
Base Classes - 语义类型基类

设计要点:
- 每种语义通过 SUPPORTED_KINDS 声明支持的 AST 类型
- 可扩展：新增语义类型无需修改收集器
"""

from dataclasses import dataclass, field
from typing import Set, Optional, Type, List, ClassVar
import pyslang


@dataclass
class SemanticItem:
    """语义项基类"""
    node: pyslang.SyntaxNode
    module_path: str = ""
    
    # 类属性：子类声明支持的 pyslang kind
    SUPPORTED_KINDS: ClassVar[Set[str]] = set()
    
    @classmethod
    def matches(cls, node) -> bool:
        """检查节点是否匹配此语义类型"""
        if cls == SemanticItem:
            return False
        return node.kind.name in cls.SUPPORTED_KINDS
    
    @property
    def kind_name(self) -> str:
        """获取原始 AST kind 名称"""
        return self.node.kind.name if self.node else ""
    
    @property
    def line_number(self) -> Optional[int]:
        """获取行号"""
        if self.node and hasattr(self.node, 'location') and self.node.location:
            return self.node.location.line
        return None
    
    def __repr__(self):
        return f"{self.__class__.__name__}({self.module_path})"


class SemanticCollector:
    """
    语义收集器 - 从 pyslang AST 提取语义类型
    
    设计特点:
    - 自动遍历 AST
    - 每个 SemanticItem 子类通过 SUPPORTED_KINDS 声明自己支持的 kind
    - 无需修改收集器即可扩展新的语义类型
    """
    
    def __init__(self):
        self.items: List[SemanticItem] = []
        self._semantic_classes: List[Type[SemanticItem]] = []
    
    def register(self, cls: Type[SemanticItem]) -> None:
        """注册语义类型类"""
        if cls not in self._semantic_classes:
            self._semantic_classes.append(cls)
    
    def collect(self, tree: pyslang.SyntaxTree, filename: str) -> 'SemanticCollector':
        """从 SyntaxTree 收集语义"""
        self.items.clear()
        
        # 注册所有子类
        for cls in SemanticItem.__subclasses__():
            self.register(cls)
        
        # 遍历 AST
        def visitor(node):
            for cls in self._semantic_classes:
                if cls.matches(node):
                    try:
                        item = cls(node, module_path=self._get_module_path(node))
                        self.items.append(item)
                    except:
                        pass
            return pyslang.VisitAction.Advance
        
        tree.root.visit(visitor)
        return self
    
    def _get_module_path(self, node) -> str:
        """获取节点所在模块路径"""
        # 向上遍历找 ModuleDeclaration
        parent = node.parent
        while parent:
            if parent.kind.name == 'ModuleDeclaration':
                for child in parent:
                    if child.kind.name == 'Identifier':
                        return str(child.value) if hasattr(child, 'value') else str(child)
            parent = parent.parent
        return ""
    
    def get_by_type(self, cls: Type[SemanticItem]) -> List[SemanticItem]:
        """按类型获取"""
        return [item for item in self.items if isinstance(item, cls)]
    
    def get_by_kind(self, kind: str) -> List[SemanticItem]:
        """按原始 AST kind 获取"""
        return [item for item in self.items if item.kind_name == kind]
    
    @property
    def signal_items(self) -> List['SignalItem']:
        return self.get_by_type(SignalItem)
    
    @property
    def driver_signals(self) -> List['DriverSignal']:
        return self.get_by_type(DriverSignal)


# Import for type hints
from .signal import SignalItem
from .driver import DriverSignal


__all__ = ['SemanticItem', 'SemanticCollector']
