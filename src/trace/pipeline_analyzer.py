"""
PipelineAnalyzer - 流水线结构分析器
基于 DataPathAnalyzer 实现，增强handshaking 检测
"""
import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional


@dataclass 
class StageInfo:
    """流水线阶段信息"""
    name: str
    registers: List[str] = field(default_factory=list)
    combinational: List[str] = field(default_factory=list)
    clock: Optional[str] = None
    reset: Optional[str] = None
    enable: Optional[str] = None
    stage_id: int = 0


@dataclass
class HandshakeSignal:
    """Handshaking 信号"""
    name: str
    direction: str
    type: str
    associated: Optional[str] = None


@dataclass
class HandshakeChannel:
    """Handshaking 通道"""
    name: str
    source_stage: str
    dest_stage: str
    valid_signal: Optional[str] = None
    ready_signal: Optional[str] = None
    data_signals: List[str] = field(default_factory=list)
    protocol: str = "valid_ready"


@dataclass
class PipelineStats:
    """流水线统计"""
    total_stages: int = 0
    total_registers: int = 0
    max_fanout: int = 0
    critical_path_depth: int = 0
    has_handshaking: bool = False


@dataclass
class PipelineInfo:
    """完整的流水线信息"""
    name: str
    stages: List[StageInfo] = field(default_factory=list)
    handshakes: List[HandshakeChannel] = field(default_factory=list)
    stats: PipelineStats = field(default_factory=PipelineStats)
    data_path: List[str] = field(default_factory=list)
    
    def get_stage_names(self) -> List[str]:
        return [s.name for s in self.stages]
    
    def visualize(self) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("PIPELINE ANALYSIS")
        lines.append("=" * 60)
        
        lines.append(f"\n📊 Summary: {self.stats.total_stages} stages, "
                  f"{self.stats.total_registers} registers")
        
        if self.stages:
            lines.append(f"\n🔄 Stages:")
            for stage in self.stages:
                reg_str = ", ".join(stage.registers[:3])
                if len(stage.registers) > 3:
                    reg_str += f"... +{len(stage.registers)-3}"
                lines.append(f"  [{stage.stage_id}] {stage.name}")
                lines.append(f"      regs: {reg_str}")
                if stage.clock:
                    lines.append(f"      clk: {stage.clock}")
                if stage.enable:
                    lines.append(f"      en: {stage.enable}")
        
        if self.handshakes:
            lines.append(f"\n🤝 Handshaking Channels:")
            for hs in self.handshakes:
                lines.append(f"  {hs.source_stage} -> {hs.dest_stage}")
                if hs.valid_signal:
                    lines.append(f"      valid: {hs.valid_signal}")
                if hs.ready_signal:
                    lines.append(f"      ready: {hs.ready_signal}")
        
        if self.data_path:
            lines.append(f"\n📈 Data Flow:")
            flow_str = " -> ".join(self.data_path[:8])
            if len(self.data_path) > 8:
                flow_str += " -> ..."
            lines.append(f"  {flow_str}")
        
        lines.append("=" * 60)
        return "\n".join(lines)


class PipelineAnalyzer:
    """流水线分析器 - 基于 DataPathAnalyzer"""
    
    def __init__(self, parser):
        self.parser = parser
        self._datapath = None
    
    def _get_datapath(self):
        if not self._datapath:
            from trace.datapath import DataPathAnalyzer
            self._datapath = DataPathAnalyzer(self.parser)
        return self._datapath
    
    def analyze(self, module_name: str = None, 
               signal: str = None) -> PipelineInfo:
        """分析流水线"""
        info = PipelineInfo(name=module_name or "pipeline")
        
        # 1. 使用 DataPathAnalyzer 获取 stages
        if signal:
            dp = self._get_datapath()
            result = dp.analyze(signal, max_depth=20)
            
            # 转换 stages
            if result.stages:
                for i, s in enumerate(result.stages):
                    stage = StageInfo(
                        name=s.name,
                        registers=s.signals,
                        clock=s.clock,
                        enable=s.enable,
                        reset=s.reset,
                        stage_id=i
                    )
                    info.stages.append(stage)
        
        # 2. 如果没有指定信号，尝试分析所有 FF 信号
        if not signal and module_name:
            info = self._analyze_module(module_name)
        
        # 3. 计算统计
        info.stats = self._compute_stats(info.stages)
        
        return info
    
    def _analyze_module(self, module_name: str) -> PipelineInfo:
        """分析整个模块"""
        info = PipelineInfo(name=module_name)
        
        # 使用 datapath 分析所有信号
        dp = self._get_datapath()
        
        # 收集所有逻辑信号
        all_signals = set()
        for fname, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            self._collect_signals(tree.root, all_signals)
        
        # 对每个信号进行深度分析
        stage_map = {}
        
        for sig in list(all_signals)[:20]:  # 限制数量
            try:
                result = dp.analyze(sig, max_depth=5)
                if result.stages:
                    stage_map[sig] = result.stages
            except:
                pass
        
        # 转换为 StageInfo
        all_stages = []
        for sig, stages in stage_map.items():
            for s in stages:
                if s.signals:
                    stage = StageInfo(
                        name=s.name,
                        registers=s.signals,
                        clock=s.clock,
                        enable=s.enable,
                        stage_id=len(all_stages)
                    )
                    all_stages.append(stage)
        
        # 去重
        seen = set()
        unique = []
        for s in all_stages:
            if s.name not in seen:
                seen.add(s.name)
                unique.append(s)
        
        info.stages = unique[:10]  # 限制
        
        return info
    
    def _collect_signals(self, node, signals: Set):
        """收集信号定义"""
        if node is None:
            return
        
        # ModuleDeclaration
        if 'ModuleDeclaration' in type(node).__name__:
            if hasattr(node, 'members') and node.members:
                for m in node.members:
                    self._collect_signals(m, signals)
        
        # VariableDeclarations
        elif 'VariableDeclarations' in type(node).__name__:
            decl = getattr(node, 'declarators', [])
            if decl:
                for d in decl:
                    if hasattr(d, 'name'):
                        signals.add(str(d.name))
        
        # 递归
        for attr in ['members', 'items', 'body']:
            if hasattr(node, attr):
                children = getattr(node, attr)
                if children and hasattr(children, '__iter__'):
                    for child in children:
                        self._collect_signals(child, signals)
    
    def _compute_stats(self, stages: List[StageInfo]) -> PipelineStats:
        """计算统计"""
        stats = PipelineStats()
        
        stats.total_stages = len(stages)
        
        for s in stages:
            stats.total_registers += len(s.registers)
        
        if stages:
            max_regs = max(len(s.registers) for s in stages)
            stats.max_fanout = max_regs
        
        stats.has_handshaking = any('valid' in s.name.lower() or 'ready' in s.name.lower() 
                           for s in stages)
        
        return stats
    
    def analyze_signal(self, signal: str) -> PipelineInfo:
        """分析单个信号的数据路径"""
        return self.analyze(signal=signal)


def analyze_pipeline(parser, signal: str = None, 
                   module_name: str = None) -> PipelineInfo:
    """便捷函数"""
    analyzer = PipelineAnalyzer(parser)
    return analyzer.analyze(module_name, signal)
