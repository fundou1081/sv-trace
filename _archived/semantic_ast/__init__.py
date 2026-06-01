"""
semantic_ast - 语义 AST 模块

基于 pyslang 的语义增强 AST，用于替代 SyntaxTree + ScopeTree + SymbolTable 分离架构。

核心设计:
- 语义节点内聚 scope/type/driver 信息
- 支持 generate 展开
- 跨模块符号解析
- 驱动/负载关系直接内聚在节点中
"""

from semantic_ast.nodes import (
    SemanticNodeKind,
    SemanticSignalNode,
    SemanticDriverRef,
    SemanticLoadRef,
    SemanticScopeNode,
    SemanticAST,
    ConfidenceLevel,
)
from semantic_ast.builder import SemanticASTBuilder
from semantic_ast.expr_parser import (
    get_identifier_text,
    collect_expression_identifiers,
    extract_driver_info,
)
from semantic_ast.graph import SemanticRelationGraph
from semantic_ast.resolver import SymbolResolver, ResolvedSymbol, ModuleInterface
from semantic_ast.comparator import compare_outputs, DiffResult, run_benchmark_comparison

__all__ = [
    # 节点类型
    'SemanticNodeKind',
    'SemanticSignalNode',
    'SemanticDriverRef',
    'SemanticLoadRef',
    'SemanticScopeNode',
    'SemanticAST',
    'ConfidenceLevel',
    # 构建器
    'SemanticASTBuilder',
    # 表达式解析
    'get_identifier_text',
    'collect_expression_identifiers',
    'extract_driver_info',
    # 语义图
    'SemanticRelationGraph',
    # 符号解析
    'SymbolResolver',
    'ResolvedSymbol',
    'ModuleInterface',
    # 对比工具
    'compare_outputs',
    'DiffResult',
    'run_benchmark_comparison',
]