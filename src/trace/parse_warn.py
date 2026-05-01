"""
Parse Warning System - 解析警告系统
用于捕获和报告 parser 不支持的语法结构或处理异常

模块提供统一的警告处理机制，帮助在解析过程中及时发现还不支持的语法结构。

Example:
    >>> from trace.parse_warn import ParseWarningHandler, warn_unsupported
    >>> handler = ParseWarningHandler(verbose=True)
    >>> handler.warn_unsupported("ClassDeclaration", context="file.sv")
"""

import sys
import os
import traceback
from typing import Optional, Set, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum
import time


class WarningLevel(Enum):
    """警告级别枚举"""
    INFO = "INFO"      # 信息
    WARN = "WARN"      # 警告 - 不支持的语法
    ERROR = "ERROR"    # 错误 - 处理异常
    UNKNOWN = "UNKNOWN"  # 未知节点类型


@dataclass
class ParseWarning:
    """解析警告数据类
    
    Attributes:
        level: 警告级别
        component: 组件名，如 "ConnectionTracer"
        message: 警告信息
        node_kind: 节点类型
        context: 上下文信息
        suggestion: 建议
        timestamp: 时间戳
    """
    level: WarningLevel
    component: str
    message: str
    node_kind: str = ""
    context: str = ""
    suggestion: str = ""
    timestamp: float = field(default_factory=time.time)
    
    def __str__(self):
        parts = [f"[{self.level.value}]", f"[{self.component}]"]
        if self.node_kind:
            parts.append(f"<{self.node_kind}>")
        parts.append(self.message)
        if self.context:
            parts.append(f"@ {self.context}")
        if self.suggestion:
            parts.append(f"=> {self.suggestion}")
        return " ".join(parts)


class ParseWarningHandler:
    """解析警告处理器
    
    用于收集和报告解析过程中的警告信息。
    
    Attributes:
        verbose: 是否打印警告信息
        component: 默认组件名
    
    Example:
        >>> handler = ParseWarningHandler(verbose=True, component="MyParser")
        >>> handler.warn_unsupported("InterfaceDeclaration", context="top.sv")
        >>> handler.print_warning_report()
    """
    
    # 已知的支持类型
    SUPPORTED_KINDS: Set[str] = set()
    
    # 已知不支持的语法
    KNOWN_UNSUPPORTED: Dict[str, str] = {
        "InterfaceDeclaration": "interface声明 - 部分支持",
        "ProgramDeclaration": "program声明 - 部分支持",
        "PackageDeclaration": "package声明 - 部分支持",
        "ClassDeclaration": "class声明 - 部分支持",
        "CovergroupDeclaration": "covergroup - 不支持",
        "ModportItem": "modport - 部分支持",
        "InterfacePortDeclaration": "interface端口 - 部分支持",
        "PropertyDeclaration": "property声明 - 不支持",
        "SequenceDeclaration": "sequence声明 - 不支持",
        "ClockingBlock": "clocking block - 不支持",
        "ConstraintBlock": "constraint块 - 部分支持",
        "RandSequenceExpression": "rand sequence - 不支持",
        "Unexpected": "意外节点",
    }
    
    def __init__(self, verbose: bool = True, component: str = "Parser"):
        """初始化警告处理器
        
        Args:
            verbose: 是否打印警告到标准输出
            component: 默认组件名
        """
        self.warnings: List[ParseWarning] = []
        self.verbose = verbose
        self.component = component
        self._seen_kinds: Set[str] = set()
        self._stats: Dict[str, int] = {}
    
    def warn_unsupported(
        self,
        node_kind: str,
        context: str = "",
        suggestion: str = "",
        component: Optional[str] = None
    ) -> None:
        """警告不支持的语法结构
        
        Args:
            node_kind: 节点类型名称
            context: 上下文信息（如文件名、行号）
            suggestion: 处理建议
            component: 组件名（默认为 self.component）
        """
        comp = component or self.component
        
        if node_kind in self.KNOWN_UNSUPPORTED:
            msg = f"不支持的语法类型: {self.KNOWN_UNSUPPORTED[node_kind]}"
            if not suggestion:
                suggestion = "请确认解析结果完整性"
        else:
            msg = "遇到未处理的节点类型"
            if not suggestion:
                suggestion = "可能需要更新解析器以支持此语法"
            
            level = WarningLevel.UNKNOWN
            warn = ParseWarning(
                level=level,
                component=comp,
                message=msg,
                node_kind=node_kind,
                context=context,
                suggestion=suggestion
            )
            self.warnings.append(warn)
            self._update_stats(node_kind)
            
            if self.verbose:
                print(f"⚠️ {warn}")
            return
        
        level = WarningLevel.WARN
        warn = ParseWarning(
            level=level,
            component=comp,
            message=msg,
            node_kind=node_kind,
            context=context,
            suggestion=suggestion
        )
        self.warnings.append(warn)
        self._update_stats(node_kind)
        
        if self.verbose:
            print(f"⚠️ {warn}")
    
    def warn_error(
        self,
        operation: str,
        exc: Exception,
        context: str = "",
        component: Optional[str] = None
    ) -> None:
        """警告解析错误
        
        Args:
            operation: 操作名称
            exc: 异常对象
            context: 上下文信息
            component: 组件名
        """
        comp = component or self.component
        
        exc_type = type(exc).__name__
        exc_msg = str(exc)
        
        tb_str = ""
        if hasattr(exc, '__traceback__'):
            tb_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
            tb_str = "".join(tb_lines[-5:])
        
        msg = f"解析异常: {exc_type}: {exc_msg}"
        
        warn = ParseWarning(
            level=WarningLevel.ERROR,
            component=comp,
            message=msg,
            context=context,
            suggestion=f"检查 {operation} 实现"
        )
        self.warnings.append(warn)
        self._update_stats(f"ERROR_{operation}")
        
        if self.verbose:
            print(f"❌ {warn}")
            if tb_str and self.verbose:
                for line in tb_str.strip().split('\n')[-5:]:
                    print(f"   {line}")
    
    def warn_info(
        self,
        message: str,
        context: str = "",
        component: Optional[str] = None
    ) -> None:
        """信息日志
        
        Args:
            message: 信息内容
            context: 上下文信息
            component: 组件名
        """
        comp = component or self.component
        
        warn = ParseWarning(
            level=WarningLevel.INFO,
            component=comp,
            message=message,
            context=context
        )
        
        if self.verbose:
            print(f"ℹ️ {warn}")
    
    def _update_stats(self, kind: str) -> None:
        """更新统计"""
        self._stats[kind] = self._stats.get(kind, 0) + 1
    
    def get_unhandled_kinds(self) -> Dict[str, int]:
        """获取所有未处理的节点类型及其出现次数
        
        Returns:
            Dict[str, int]: 节点类型到出现次数的映射
        """
        return dict(self._stats)
    
    def get_report(self) -> str:
        """生成警告报告
        
        Returns:
            str: 格式化的警告报告字符串
        """
        lines = ["=" * 60, "PARSE WARNING REPORT", "=" * 60]
        
        if not self.warnings:
            lines.append("No warnings.")
        else:
            lines.append(f"Total warnings: {len(self.warnings)}")
            lines.append("")
            
            by_level = {}
            for w in self.warnings:
                by_level[w.level] = by_level.get(w.level, 0) + 1
            
            lines.append("By level:")
            for level, count in sorted(by_level.items(), key=lambda x: -x[1]):
                lines.append(f"  {level.value}: {count}")
            
            lines.append("")
            lines.append("By node kind:")
            for kind, count in sorted(self._stats.items(), key=lambda x: -x[1])[:20]:
                lines.append(f"  {kind}: {count}")
            
            lines.append("")
            lines.append("Recent warnings:")
            for w in self.warnings[-10:]:
                lines.append(f"  {w}")
        
        lines.append("=" * 60)
        return "\n".join(lines)
    
    def print_report(self) -> None:
        """打印警告报告到标准输出"""
        print(self.get_report())


# 全局默认处理器
_default_handler: Optional[ParseWarningHandler] = None


def get_handler() -> ParseWarningHandler:
    """获取全局警告处理器（单例模式）
    
    Returns:
        ParseWarningHandler: 全局警告处理器实例
    """
    global _default_handler
    if _default_handler is None:
        _default_handler = ParseWarningHandler()
    return _default_handler


def warn_unsupported(
    node_kind: str,
    context: str = "",
    suggestion: str = "",
    component: Optional[str] = None
) -> None:
    """快捷函数：警告不支持的语法
    
    Args:
        node_kind: 节点类型名称
        context: 上下文信息
        suggestion: 处理建议
        component: 组件名
    """
    get_handler().warn_unsupported(node_kind, context, suggestion, component)


def warn_error(
    operation: str,
    exc: Exception,
    context: str = "",
    component: Optional[str] = None
) -> None:
    """快捷函数：警告解析错误
    
    Args:
        operation: 操作名称
        exc: 异常对象
        context: 上下文信息
        component: 组件名
    """
    get_handler().warn_error(operation, exc, context, component)


def reset_handler() -> None:
    """重置全局处理器（用于测试）"""
    global _default_handler
    _default_handler = None
