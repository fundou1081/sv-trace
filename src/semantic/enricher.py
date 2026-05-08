"""SemanticEnricher - 语义增强器

在 extractors 输出的 SemanticGraph 基础上做语义增强。
符合铁律 21: Semantic 层消费 SemanticGraph，不得直接遍历 AST。
"""

from typing import Dict, List, Optional

from extractors.base import (
    SemanticGraph,
    LoadPoint,
    DriverPoint,
    ConfidenceLevel,
)
from semantic.models import (
    EnrichedSemanticGraph,
    EnrichedSignal,
    EnrichedLoadPoint,
    EnrichedDriverPoint,
)
from semantic.agent_interface import AgentContext


class SemanticEnricher:
    """语义增强器
    
    在 SemanticGraph 基础上添加：
    - 置信度评估
    - 自然语言描述
    - caveats 标注
    - AGENT 业务语义填充
    
    符合铁律 21: 消费 SemanticGraph，不遍历 AST
    符合铁律 22: 必须标注 confidence 和 caveats
    """
    
    def __init__(self, base_graph: SemanticGraph):
        self.graph = base_graph
    
    def enrich(self, agent_context: Optional[AgentContext] = None) -> EnrichedSemanticGraph:
        """执行语义增强
        
        Args:
            agent_context: AGENT 上下文（可选）
        
        Returns:
            EnrichedSemanticGraph: 增强后的语义图
        """
        enriched = EnrichedSemanticGraph(
            base=self.graph,
            enriched_signals={},
            agent_context=agent_context,
        )
        
        # 1. 为每个信号创建 EnrichedSignal
        for sig_name in self.graph.all_signals:
            esig = self._enrich_signal(sig_name, agent_context)
            enriched.add_enriched_signal(esig)
        
        # 2. 填充关系
        for sig_name in self.graph.all_signals:
            esig = enriched.get_enriched_signal(sig_name)
            
            # 填充 load 关系
            for lp in self.graph.get_load(sig_name):
                elp = self._enrich_load_point(lp, agent_context)
                esig.loads.append(elp)
            
            # 填充 driver 关系
            for dp in self.graph.get_driver(sig_name):
                edp = self._enrich_driver_point(dp, agent_context)
                esig.drivers.append(edp)
        
        return enriched
    
    def _enrich_signal(self, sig_name: str, agent_ctx: Optional[AgentContext]) -> EnrichedSignal:
        """为单个信号创建 EnrichedSignal"""
        # 评估置信度
        confidence = self._assess_confidence(sig_name)
        caveats = self._assess_caveats(sig_name)
        
        # AGENT 覆盖置信度
        if agent_ctx:
            override = agent_ctx.get_confidence_override(sig_name)
            if override:
                confidence = ConfidenceLevel(override)
        
        # 生成描述
        description = self._generate_description(sig_name)
        
        # AGENT 填充
        business_meaning = agent_ctx.get_business_meaning(sig_name) if agent_ctx else ""
        tags = agent_ctx.get_tags(sig_name) if agent_ctx else []
        user_notes = agent_ctx.get_user_note(sig_name) if agent_ctx else ""
        
        return EnrichedSignal(
            signal_name=sig_name,
            confidence=confidence,
            caveats=caveats,
            description=description,
            business_meaning=business_meaning,
            tags=tags,
            user_notes=user_notes,
        )
    
    def _enrich_load_point(self, lp: LoadPoint, agent_ctx: Optional[AgentContext]) -> EnrichedLoadPoint:
        """为负载点创建 EnrichedLoadPoint"""
        # 评估置信度
        confidence = self._assess_load_confidence(lp)
        caveats = self._assess_load_caveats(lp)
        
        # 生成描述
        description = f"{lp.signal} 被 {lp.load_by} 加载 ({lp.context})"
        
        # AGENT 覆盖置信度
        if agent_ctx:
            override = agent_ctx.get_confidence_override(f"{lp.signal}←{lp.load_by}")
            if override:
                confidence = ConfidenceLevel(override)
            bm = agent_ctx.get_business_meaning(f"{lp.signal}←{lp.load_by}")
            if bm:
                description = bm
        
        return EnrichedLoadPoint(
            raw=lp,
            confidence=confidence,
            caveats=caveats,
            description=description,
        )
    
    def _enrich_driver_point(self, dp: DriverPoint, agent_ctx: Optional[AgentContext]) -> EnrichedDriverPoint:
        """为驱动点创建 EnrichedDriverPoint"""
        # 评估置信度
        confidence = self._assess_driver_confidence(dp)
        caveats = self._assess_driver_caveats(dp)
        
        # 生成描述
        parts = [f"{dp.signal} 被 {dp.driver} 驱动 ({dp.kind})"]
        if dp.clock:
            parts.append(f", 时钟: {dp.clock}")
        if dp.reset:
            parts.append(f", 复位: {dp.reset}")
        description = "".join(parts)
        
        # AGENT 覆盖置信度
        if agent_ctx:
            override = agent_ctx.get_confidence_override(f"{dp.signal}→{dp.driver}")
            if override:
                confidence = ConfidenceLevel(override)
        
        return EnrichedDriverPoint(
            raw=dp,
            confidence=confidence,
            caveats=caveats,
            description=description,
        )
    
    def _assess_confidence(self, sig_name: str) -> ConfidenceLevel:
        """评估信号解析的置信度"""
        # 简单策略：如果信号在多个作用域中被引用，降低置信度
        load_points = self.graph.get_load(sig_name)
        driver_points = self.graph.get_driver(sig_name)
        
        # 多驱动 → 低置信度
        if len(driver_points) > 3:
            return ConfidenceLevel.MEDIUM
        
        # 无驱动 → 可能未初始化
        if not driver_points:
            return ConfidenceLevel.MEDIUM
        
        return ConfidenceLevel.HIGH
    
    def _assess_caveats(self, sig_name: str) -> List[str]:
        """列出信号的不确定项"""
        caveats = []
        
        driver_points = self.graph.get_driver(sig_name)
        
        # 多驱动
        if len(driver_points) > 3:
            caveats.append(f"存在 {len(driver_points)} 个驱动源，可能存在多驱动冲突")
        
        # 无驱动
        if not driver_points:
            caveats.append("信号未被驱动，可能未初始化或悬空")
        
        return caveats
    
    def _assess_load_confidence(self, lp: LoadPoint) -> ConfidenceLevel:
        """评估负载点的置信度"""
        # 组合逻辑中读取信号 → 置信度降低
        if lp.context == 'always_comb':
            return ConfidenceLevel.MEDIUM
        
        return ConfidenceLevel.HIGH
    
    def _assess_load_caveats(self, lp: LoadPoint) -> List[str]:
        """列出负载点的不确定项"""
        caveats = []
        
        if lp.context == 'always_comb':
            caveats.append("always_comb 可能在综合时被合并到其他逻辑")
        
        return caveats
    
    def _assess_driver_confidence(self, dp: DriverPoint) -> ConfidenceLevel:
        """评估驱动点的置信度"""
        # 无时钟 → 可能是 latch 或组合逻辑
        if dp.kind == 'always_ff' and not dp.clock:
            return ConfidenceLevel.LOW
        
        if dp.kind == 'always_comb':
            return ConfidenceLevel.MEDIUM
        
        return ConfidenceLevel.HIGH
    
    def _assess_driver_caveats(self, dp: DriverPoint) -> List[str]:
        """列出驱动点的不确定项"""
        caveats = []
        
        if dp.kind == 'always_ff' and not dp.clock:
            caveats.append("always_ff 缺少时钟关联")
        
        if dp.kind == 'always_comb':
            caveats.append("always_comb 驱动可能在综合时被优化")
        
        return caveats
    
    def _generate_description(self, sig_name: str) -> str:
        """生成信号的自然语言描述"""
        load_points = self.graph.get_load(sig_name)
        driver_points = self.graph.get_driver(sig_name)
        
        parts = []
        
        if driver_points:
            if len(driver_points) == 1:
                dp = driver_points[0]
                parts.append(f"由 {dp.driver} 驱动 ({dp.kind})")
            else:
                parts.append(f"被 {len(driver_points)} 个源驱动")
        
        if load_points:
            if len(load_points) == 1:
                parts.append(f"被 {load_points[0].load_by} 读取")
            else:
                parts.append(f"被 {len(load_points)} 个信号读取")
        
        if not parts:
            return f"{sig_name} 暂无关联关系"
        
        return f"{sig_name}: " + ", ".join(parts)
