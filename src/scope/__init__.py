"""Scope 体系 - 作用域树和符号表

提供 Pass 1 的核心数据结构：
- ScopeTree: 完整的作用域层级树
- SymbolTable: 符号表管理
- ScopeBuilder: AST → ScopeTree 转换器

符合铁律 18-20
"""

from scope.models import (
    ScopeKind,
    ScopeInfo,
    SignalDecl,
    SignalRef,
)
from scope.symbol_table import SymbolTable
from scope.builder import ScopeBuilder

__all__ = [
    'ScopeKind',
    'ScopeInfo',
    'SignalDecl',
    'SignalRef',
    'SymbolTable',
    'ScopeBuilder',
]
