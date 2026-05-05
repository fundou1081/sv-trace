"""Connection Tracer using semantic layer."""

import sys
import os
from typing import List, Dict, Optional
from dataclasses import dataclass, field

import pyslang

from trace.parse_warn import ParseWarningHandler

try:
    from semantic.base import SemanticCollector
    from semantic.connection import InstanceItem, PortConnectionItem, NetConnection
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    SemanticCollector = None


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
    """连接追踪器"""
    
    def __init__(self, trees: dict = None, use_semantic: bool = True, verbose: bool = True):
        self.trees = trees or {}
        self.use_semantic = use_semantic and SEMANTIC_AVAILABLE
        self.verbose = verbose
        self.connections: List[Connection] = []
        self.instances: List[Instance] = []
        self.warn_handler = ParseWarningHandler(verbose=verbose, component="ConnectionTracer")
        self._collector: Optional[SemanticCollector] = None
    
    def collect(self, tree: pyslang.SyntaxTree, filename: str) -> 'ConnectionTracer':
        self._collector = SemanticCollector()
        self._collector.collect(tree, filename)
        
        # 实例
        for item in self._collector.get_by_type(InstanceItem):
            inst = Instance(
                name=item.instance_name or "",
                module_type=item.module_type or ""
            )
            self.instances.append(inst)
        
        # 连接
        for item in self._collector.get_by_type(PortConnectionItem):
            conn = Connection(
                source=item.signal or "",
                dest=item.port_name or "",
                port=item.port_name or ""
            )
            self.connections.append(conn)
        
        return self
    
    @property
    def all_instances(self) -> List[Instance]:
        return self.instances


def trace_connections(parser=None, use_semantic: bool = True, verbose: bool = True) -> ConnectionTracer:
    return ConnectionTracer(use_semantic=use_semantic, verbose=verbose)
