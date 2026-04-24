"""
DataPath Analyzer - 数据流深度追踪
支持 assign + always_comb/always_ff + if/case + 循环 + 流水线
"""
import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional
from collections import deque


@dataclass
class DataPathNode:
    signal: str
    drivers: List[str] = field(default_factory=list)  # 上游信号
    exprs: List[str] = field(default_factory=list)     # 驱动表达式
    driver_kinds: List[str] = field(default_factory=list)  # 驱动类型


@dataclass 
class PipelineStage:
    """流水线阶段"""
    name: str
    signals: List[str] = field(default_factory=list)
    clock: Optional[str] = None
    enable: Optional[str] = None
    reset: Optional[str] = None


@dataclass
class DataPath:
    nodes: Dict[str, DataPathNode] = field(default_factory=dict)
    chain: List[str] = field(default_factory=list)
    stages: List[PipelineStage] = field(default_factory=list)
    
    def visualize(self) -> str:
        lines = ["=== Data Path Analysis ==="]
        
        # 流水线阶段
        if self.stages:
            lines.append(f"\n[Pipeline Stages]")
            for i, stage in enumerate(self.stages):
                sigs = ", ".join(stage.signals) if stage.signals else "(none)"
                clk = f", clk={stage.clock}" if stage.clock else ""
                en = f", en={stage.enable}" if stage.enable else ""
                lines.append(f"  Stage {i+1}: {sigs}{clk}{en}")
        
        # 数据流链
        if self.chain:
            lines.append(f"\n[Data Flow] {' → '.join(self.chain)}")
        
        # 依赖关系 - 按 topological 排序显示
        if self.nodes:
            lines.append(f"\n[Dependencies]")
            # 排序：按依赖层级
            sorted_sigs = self._topological_sort()
            for sig in sorted_sigs:
                node = self.nodes[sig]
                if node.exprs:
                    expr = node.exprs[0] if len(node.exprs) == 1 else f"{{{' | '.join(node.exprs)}}}"
                    kind = node.driver_kinds[0] if node.driver_kinds else ""
                    lines.append(f"  {sig} ← {kind} {expr}")
                else:
                    lines.append(f"  {sig} ← [input]")
        
        return '\n'.join(lines)
    
    def _topological_sort(self) -> List[str]:
        """Topological sort of signals by dependency"""
        # 简单实现：按深度排序
        depth = {}
        
        def get_depth(sig):
            if sig in depth:
                return depth[sig]
            node = self.nodes.get(sig)
            if not node or not node.drivers:
                depth[sig] = 0
                return 0
            d = 1 + max([get_depth(d) for d in node.drivers if d in self.nodes], default=0)
            depth[sig] = d
            return d
        
        for sig in self.nodes:
            get_depth(sig)
        
        return sorted(self.nodes.keys(), key=lambda x: depth.get(x, 0), reverse=True)


class DataPathAnalyzer:
    def __init__(self, parser):
        self.parser = parser
        self._driver = None
    
    def _get_driver(self):
        if not self._driver:
            from .driver import DriverTracer
            self._driver = DriverTracer(self.parser)
        return self._driver
    
    def analyze(self, signal: str, max_depth: int = 20) -> DataPath:
        driver = self._get_driver()
        
        # 收集所有信号
        all_signals = self._collect_signals()
        
        if not all_signals:
            return DataPath()
        
        # 构建节点图
        nodes = self._build_nodes(all_signals)
        
        # 追踪链 - 从 signal 追溯到 input
        chain = self._build_chain(signal, nodes, max_depth)
        
        # 识别流水线阶段
        stages = self._detect_pipeline_stages(nodes)
        
        return DataPath(nodes=nodes, chain=chain, stages=stages)
    
    def analyze_module(self) -> DataPath:
        """分析整个模块的数据流"""
        all_signals = self._collect_signals()
        
        if not all_signals:
            return DataPath()
        
        nodes = self._build_nodes(all_signals)
        stages = self._detect_pipeline_stages(nodes)
        
        return DataPath(nodes=nodes, chain=[], stages=stages)
    
    def _build_nodes(self, all_signals: Set[str]) -> Dict[str, DataPathNode]:
        """构建所有信号节点"""
        driver = self._get_driver()
        nodes = {}
        
        for sig in all_signals:
            drivers = driver.get_drivers(sig)
            
            if not drivers:
                nodes[sig] = DataPathNode(signal=sig)
                continue
            
            all_upstreams = set()
            all_exprs = []
            all_kinds = []
            
            for d in drivers:
                expr = " ".join(d.sources).strip()
                all_exprs.append(expr)
                all_kinds.append(d.kind.name)
                
                # 从表达式提取信号
                for u in self._extract_signals(expr, sig):
                    if u in all_signals:
                        all_upstreams.add(u)
            
            nodes[sig] = DataPathNode(
                signal=sig,
                drivers=list(all_upstreams),
                exprs=all_exprs,
                driver_kinds=all_kinds
            )
        
        return nodes
    
    def _collect_signals(self) -> Set[str]:
        all_signals = set()
        
        for tree in self.parser.trees.values():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            root = tree.root
            members = getattr(root, 'members', None)
            if not members:
                continue
            
            for i in range(len(members)):
                member = members[i]
                
                if 'ModuleDeclaration' not in str(type(member)):
                    continue
                
                mod_members = getattr(member, 'members', None)
                if not mod_members:
                    continue
                
                for j in range(len(mod_members)):
                    mm = mod_members[j]
                    
                    if 'DataDeclaration' not in str(type(mm)):
                        continue
                    
                    declarators = getattr(mm, 'declarators', None)
                    if declarators:
                        try:
                            for decl in declarators:
                                if hasattr(decl, 'name'):
                                    name = decl.name.value if hasattr(decl.name, 'value') else str(decl.name)
                                    all_signals.add(name)
                        except TypeError:
                            pass
        
        return all_signals
    
    def _build_chain(self, signal: str, nodes: Dict[str, DataPathNode], 
                     max_depth: int) -> List[str]:
        """从 signal 追溯到根源 - BFS"""
        if signal not in nodes:
            return [signal]
        
        chain = [signal]
        visited = set([signal])
        queue = deque([(signal, 0)])
        
        while queue:
            current, depth = queue.popleft()
            
            if depth >= max_depth:
                continue
            
            node = nodes.get(current)
            if not node:
                continue
            
            for upstream in node.drivers:
                if upstream not in visited:
                    visited.add(upstream)
                    chain.append(upstream)
                    queue.append((upstream, depth + 1))
        
        return list(reversed(chain))
    
    def _detect_pipeline_stages(self, nodes: Dict[str, DataPathNode]) -> List[PipelineStage]:
        """检测流水线阶段 - 基于 register 链"""
        stages = []
        
        # 找到所有 ALWAYS_FF 驱动的信号
        ff_signals = {}  # signal -> 驱动它的上游信号列表
        
        for sig, node in nodes.items():
            if 'ALWAYS_FF' in node.driver_kinds:
                ff_signals[sig] = node.drivers
        
        if not ff_signals:
            return stages
        
        # 构建延迟链
        # 找到链的起点（驱动源不是 ALWAYS_FF 的）
        ff_drivers = set(ff_signals.keys())
        
        # 起点：被 ALWAYS_FF 驱动但驱动源不是 ALWAYS_FF 的信号
        stage_map = {}  # signal -> stage_index
        
        def get_stage(sig):
            """递归获取信号的阶段"""
            if sig in stage_map:
                return stage_map[sig]
            
            if sig not in ff_signals:
                # 不是 FF 驱动的，尝试找到它的上游 FF
                node = nodes.get(sig)
                if node and node.drivers:
                    # 找最远的 FF 上游
                    max_stage = -1
                    for up in node.drivers:
                        if up in ff_signals:
                            max_stage = max(max_stage, get_stage(up) + 1)
                    stage_map[sig] = max_stage if max_stage >= 0 else 0
                else:
                    stage_map[sig] = 0
                return stage_map[sig]
            
            # 是 FF 驱动的
            upstreams = ff_signals[sig]
            if not upstreams:
                stage_map[sig] = 0  # 初级 stage
                return 0
            
            # 找上游的最大 stage + 1
            max_stage = -1
            for up in upstreams:
                if up in ff_signals:
                    max_stage = max(max_stage, get_stage(up) + 1)
                else:
                    # 上游不是 FF，可能连接到组合逻辑
                    max_stage = max(max_stage, 0)
            
            stage_map[sig] = max_stage if max_stage >= 0 else 0
            return stage_map[sig]
        
        # 计算所有 FF 信号的 stage
        for sig in ff_signals:
            get_stage(sig)
        
        # 按 stage 分组
        stage_dict = {}
        for sig, stage_idx in stage_map.items():
            if stage_idx not in stage_dict:
                stage_dict[stage_idx] = []
            stage_dict[stage_idx].append(sig)
        
        # 转换为 PipelineStage 列表
        for idx in sorted(stage_dict.keys()):
            stage = PipelineStage(
                name=f"Stage{idx+1}",
                signals=stage_dict[idx]
            )
            stages.append(stage)
        
        return stages
    
    def _extract_signals(self, expr: str, exclude: str) -> List[str]:
        """从表达式提取信号"""
        if not expr:
            return []
        
        keywords = {
            'if', 'else', 'case', 'endcase', 'begin', 'end', 'for', 'while', 
            'posedge', 'negedge', 'and', 'or', 'not', 'null', 'true', 'false',
            'module', 'endmodule', 'logic', 'assign', 'wire', 'return',
            'int', 'bit', 'byte', 'shortint', 'longint', 'time',
        }
        
        signals = []
        pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'
        
        for match in re.finditer(pattern, expr):
            name = match.group()
            if name != exclude and name not in keywords:
                signals.append(name)
        
        return signals


# 便捷函数
def trace_datapath(parser, signal: str) -> DataPath:
    return DataPathAnalyzer(parser).analyze(signal)
