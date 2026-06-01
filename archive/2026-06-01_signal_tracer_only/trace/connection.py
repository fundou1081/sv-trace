"""ConnectionTracer - 端口连接追踪器

按项目纪律重构 - 连接关系提取
符合铁律 17: 提取逻辑封装为独立 Visitor 类

底层使用新的 extractors/ 架构，对外保持 ConnectionTracer API 兼容。
"""

from dataclasses import dataclass
import os
from typing import List, Dict, Optional, Set

import pyslang

from trace.parse_warn import ParseWarningHandler

from scope import ScopeBuilder
from scope.models import ScopeTree, ScopeKind
from scope.symbol_table import SymbolTable
from extractors import SemanticGraph, ConnectionExtractor


@dataclass
class Connection:
    """连接"""
    source: str = ""
    dest: str = ""
    port: str = ""
    context: str = ""


@dataclass
class Instance:
    """模块实例"""
    name: str = ""
    module_type: str = ""


class ConnectionTracer:
    """收集设计中所有模块实例和端口连接信息
    
    底层使用 3-Pass 架构，对外保持 ConnectionTracer API 兼容。
    """
    
    def __init__(self, trees: dict = None, use_semantic: bool = True, verbose: bool = True):
        self.trees = trees or {}
        self.verbose = verbose
        self.connections: List[Connection] = []
        self.instances: List[Instance] = []
        self.warn_handler = ParseWarningHandler(verbose=verbose, component="ConnectionTracer")
        
        # 新架构
        self._graph: SemanticGraph = None
        self._scope_tree: ScopeTree = None
        self._symbol_table: SymbolTable = None
        self._collected = False
    
    def collect(self, tree: pyslang.SyntaxTree, filename: str) -> 'ConnectionTracer':
        """收集连接信息"""
        if not self._collected:
            self._build_pipeline(tree)
            self._collected = True
        return self
    
    def _build_pipeline(self, tree: pyslang.SyntaxTree):
        """执行 3-Pass 流程"""
        # Pass 1: ScopeBuilder
        builder = ScopeBuilder()
        self._scope_tree, self._symbol_table = builder.build(tree)
        
        # Pass 2: Extractors
        self._graph = SemanticGraph(self._scope_tree, self._symbol_table)
        ConnectionExtractor(self._scope_tree, self._symbol_table, self._graph).extract(tree)
        
        # 聚合到 instances 和 connections
        self._populate_from_graph()
    
    def _populate_from_graph(self):
        """从 SemanticGraph 聚合数据到旧 API"""
        # 从 connections 提取实例信息
        inst_map: Dict[str, Instance] = {}
        
        for conn in self._graph.connections:
            # 收集实例 (module_type 暂不填充，因为 Connection 没有这个字段)
            if conn.to_instance and conn.to_instance not in inst_map:
                inst_map[conn.to_instance] = Instance(
                    name=conn.to_instance,
                    module_type=""  # 新架构不填充此字段，连接信息从 Connection 获取
                )
        
        self.instances = list(inst_map.values())
        self.connections = [
            Connection(source=conn.signal, dest=conn.to_port, port=conn.to_port)
            for conn in self._graph.connections
        ]
    
    @property
    def all_instances(self) -> List[Instance]:
        return self.instances


def trace_connections(parser=None, use_semantic: bool = True, verbose: bool = True) -> ConnectionTracer:
    return ConnectionTracer(parser=parser, use_semantic=use_semantic, verbose=verbose)
