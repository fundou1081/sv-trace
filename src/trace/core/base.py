"""ASTWalker - 公共AST遍历基类

解决 trace 模块中重复的 AST 遍历代码问题。

遵循开发纪律:
- 铁律5: 原子化必须保持 - 提取公共逻辑，不破坏原子化设计
- 铁律1: AST 唯一数据源 - 使用 pyslang visit API
- 铁律2: 位精确性不可妥协

Example:
    >>> from trace.core.base import ASTWalker
    >>> from trace.driver import DriverCollector
    >>> 
    >>> # DriverCollector 继承 ASTWalker
    >>> class DriverCollector(ASTWalker):
    ...     def __init__(self, parser):
    ...         super().__init__(parser)
    ...         self.drivers = {}
    ...         self._collect()
"""

import sys
import os
from typing import Iterator, Callable, Any, List, Optional, Set
from dataclasses import dataclass

import pyslang
from pyslang import SyntaxKind

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from trace.parse_warn import ParseWarningHandler, WarningLevel


@dataclass
class WalkResult:
    """遍历结果"""
    file: str = ""
    line: int = 0
    node: Any = None
    parent: Any = None
    depth: int = 0


class ASTWalker:
    """公共AST遍历基类
    
    提供统一的 AST 遍历能力，消除各模块重复的 walk 逻辑。
    
    Attributes:
        parser: SVParser 实例
        warn_handler: 警告处理器
        verbose: 是否打印警告
    """
    
    def __init__(self, parser, verbose: bool = True):
        """初始化 ASTWalker
        
        Args:
            parser: SVParser 实例
            verbose: 是否打印警告信息
        """
        self.parser = parser
        self.verbose = verbose
        self.warn_handler = ParseWarningHandler(
            verbose=verbose,
            component=self.__class__.__name__
        )
        self._unsupported_encountered: Set[str] = set()
    
    def walk_all(self, callback: Callable[[pyslang.SyntaxNode, WalkResult], bool]) -> None:
        """遍历所有解析树的 AST
        
        Args:
            callback: 回调函数，签名 (node, result) -> bool
                     返回 True 继续遍历，False 停止
        """
        for fname, tree in self.parser.trees.items():
            self.walk_file(fname, callback)
    
    def walk_file(self, fname: str, callback: Callable[[pyslang.SyntaxNode, WalkResult], bool]) -> None:
        """遍历单个文件的 AST
        
        Args:
            fname: 文件名
            callback: 回调函数
        """
        tree = self.parser.trees.get(fname)
        if not tree or not tree.root:
            self.warn_handler.warn_info(
                f"文件 {fname} 解析树为空",
                context="ASTWalker.walk_file"
            )
            return
        
        try:
            result = WalkResult(file=fname)
            tree.root.visit(lambda node: self._visit_wrapper(node, result, callback))
        except Exception as e:
            self.warn_handler.warn_error(
                "TreeVisit", e,
                context=f"file={fname}",
                component="ASTWalker"
            )
    
    def _visit_wrapper(self, node: pyslang.SyntaxNode, result: WalkResult, 
                       callback: Callable) -> pyslang.VisitAction:
        """visit 回调包装器"""
        try:
            result.node = node
            result.line = self._get_line(node)
            
            # 更新深度
            if hasattr(node, 'parent') and node.parent:
                result.depth = self._calc_depth(node)
            
            should_continue = callback(node, result)
            
            if should_continue:
                return pyslang.VisitAction.Advance
            else:
                return pyslang.VisitAction.Skip
        except Exception as e:
            self.warn_handler.warn_error(
                "NodeVisit", e,
                context=f"node={node.kind if hasattr(node, 'kind') else type(node).__name__}",
                component="ASTWalker"
            )
            return pyslang.VisitAction.Advance
    
    def _get_line(self, node: pyslang.SyntaxNode) -> int:
        """获取节点所在行号"""
        try:
            if hasattr(node, 'sourceRange') and node.sourceRange:
                rng = node.sourceRange
                if hasattr(rng, 'start') and hasattr(rng.start, 'line'):
                    return rng.start.line
        except Exception:
            pass
        return 0
    
    def _calc_depth(self, node: pyslang.SyntaxNode) -> int:
        """计算节点深度"""
        depth = 0
        current = node
        while hasattr(current, 'parent') and current.parent:
            depth += 1
            current = current.parent
            if depth > 100:  # 防止循环
                break
        return depth
    
    def iter_children(self, node) -> Iterator[pyslang.SyntaxNode]:
        """安全遍历子节点
        
        Args:
            node: pyslang AST 节点
            
        Yields:
            子节点
        """
        if node is None:
            return
        
        try:
            if isinstance(node, list):
                for child in node:
                    yield from self.iter_children(child)
            elif hasattr(node, '__iter__') and not isinstance(node, str):
                try:
                    for child in node:
                        yield child
                except TypeError:
                    pass
            else:
                yield node
        except Exception:
            pass
    
    def iter_all_nodes(self, root) -> Iterator[pyslang.SyntaxNode]:
        """深度优先遍历所有节点
        
        Args:
            root: AST 根节点
            
        Yields:
            所有节点
        """
        def walk(n):
            yield n
            for child in self.iter_children(n):
                yield from walk(child)
        
        yield from walk(root)
    
    def find_kind(self, root, kind: SyntaxKind) -> List[pyslang.SyntaxNode]:
        """查找指定类型的节点
        
        Args:
            root: AST 根节点
            kind: SyntaxKind 枚举值
            
        Returns:
            匹配节点的列表
        """
        results = []
        for node in self.iter_all_nodes(root):
            if hasattr(node, 'kind') and node.kind == kind:
                results.append(node)
        return results
    
    def check_unsupported(self, node, unsupported_map: dict) -> None:
        """检查不支持的语法类型
        
        Args:
            node: AST 节点
            unsupported_map: 不支持类型映射 {TypeName: suggestion}
        """
        if node is None:
            return
        
        kind_name = node.kind.name if hasattr(node, 'kind') else type(node).__name__
        
        if kind_name in unsupported_map:
            if kind_name not in self._unsupported_encountered:
                self.warn_handler.warn_unsupported(
                    kind_name,
                    context=type(self).__name__,
                    suggestion=unsupported_map[kind_name],
                    component=type(self).__name__
                )
                self._unsupported_encountered.add(kind_name)
