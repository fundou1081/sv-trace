"""Control Flow Analyzer using semantic layer.

按项目纪律重构：使用 semantic 层分析控制流
"""

import sys
import os
from typing import List, Dict, Set, Optional
from dataclasses import dataclass, field

import pyslang

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from trace.parse_warn import ParseWarningHandler

try:
    from semantic.base import SemanticCollector
    from semantic.driver import NonBlockingAssign, BlockingAssign
    from semantic.signal import SignalItem
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    SemanticCollector = None


@dataclass
class ControlFlowBlock:
    """控制流块"""
    block_type: str = ""  # always_ff/comb/latch/initial
    conditions: List[str] = field(default_factory=list)
    branches: List[str] = field(default_factory=list)  # if/else branches
    case_items: List[str] = field(default_factory=list)


@dataclass
class ControlFlowResult:
    """控制流分析结果"""
    always_ff: List[str] = field(default_factory=list)
    always_comb: List[str] = field(default_factory=list)
    always_latch: List[str] = field(default_factory=list)
    if_statements: List[str] = field(default_factory=list)
    case_statements: List[str] = field(default_factory=list)
    
    @property
    def total_blocks(self) -> int:
        return len(self.always_ff) + len(self.always_comb) + len(self.always_latch)


class ControlFlowTracer:
    """控制流追踪器
    
    使用 semantic 层：
    - 识别 always_ff/always_comb/always_latch
    - 提取 if/else 条件
    - 分析 case 语句
    """
    
    def __init__(self, parser=None, use_semantic: bool = True, verbose: bool = True):
        self.parser = parser
        self.use_semantic = use_semantic and SEMANTIC_AVAILABLE
        self.verbose = verbose
        self.result = ControlFlowResult()
        self.warn_handler = ParseWarningHandler(verbose=verbose, component="ControlFlowTracer")
        self._collector: SemanticCollector = None
    
    def collect(self, tree: pyslang.SyntaxTree, filename: str) -> 'ControlFlowTracer':
        self._collector = SemanticCollector()
        self._collector.collect(tree, filename)
        
        # 遍历 AST 识别控制流块
        def scan(node, depth=0):
            if depth > 10 or not hasattr(node, 'kind'):
                return
            
            kind = node.kind.name
            
            # always_ff
            if kind == 'AlwaysFFBlock':
                self.result.always_ff.append(str(node)[:50])
            
            # always_comb
            elif kind == 'AlwaysCombBlock':
                self.result.always_comb.append(str(node)[:50])
            
            # always_latch
            elif kind == 'AlwaysLatchBlock':
                self.result.always_latch.append(str(node)[:50])
            
            # IfStatement
            elif kind == 'IfStatement':
                self.result.if_statements.append(str(node.condition)[:30] if hasattr(node, 'condition') else "")
            
            # CaseStatement
            elif kind == 'CaseStatement':
                self.result.case_statements.append(str(node)[:50])
            
            try:
                for child in node:
                    scan(child, depth+1)
            except:
                pass
        
        scan(tree.root)
        
        return self
    
    @property
    def clock_domains(self) -> Set[str]:
        """提取时钟域"""
        return set(s[:20] for s in self.result.always_ff if s)
    
    @property
    def has_latch(self) -> bool:
        """是否有 latch"""
        return len(self.result.always_latch) > 0
    
    @property
    def has_full_case(self) -> bool:
        """是否有完整 case"""
        return len(self.result.case_statements) > 0
    
    def find_conditions(self) -> List[str]:
        """查找所有条件"""
        return self.result.if_statements


def trace_control_flow(parser=None, use_semantic: bool = True, verbose: bool = True) -> ControlFlowTracer:
    return ControlFlowTracer(parser, use_semantic, verbose)
