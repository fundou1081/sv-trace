"""
ResetDomainAnalyzer - 复位域分析器
分析复位信号的分布、同步/异步、负载等
"""
import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
from collections import defaultdict


@dataclass
class ResetSource:
    """复位源"""
    name: str
    type: str           # "input", "internal", "power_on"
    polarity: str     # "active_low", "active_high"
    async_or_sync: str = "sync"  # "async", "sync"
    
    line_number: int = 0


@dataclass
class ResetDomain:
    """复位域"""
    name: str
    reset_signals: List[str] = field(default_factory=list)
    async_resets: List[str] = field(default_factory=list)
    sync_resets: List[str] = field(default_factory=list)
    
    # 被复位的组件
    components: List[str] = field(default_factory=list)


@dataclass
class ResetLoad:
    """复位负载"""
    signal: str
    reset: str
    reset_type: str    # "sync", "async"
    edge_level: str  # "edge", "level"


@dataclass
class ResetStats:
    """统计"""
    num_sources: int = 0
    num_domains: int = 0
    num_async_resets: int = 0
    num_sync_resets: int = 0
    max_fanout: int = 0


@dataclass
class ResetDomainResult:
    """结果"""
    sources: List[ResetSource] = field(default_factory=list)
    domains: Dict[str, ResetDomain] = field(default_factory=dict)
    loads: List[ResetLoad] = field(default_factory=list)
    stats: ResetStats = field(default_factory=ResetStats)
    
    def visualize(self) -> str:
        lines = ["=" * 60, "RESET DOMAIN ANALYSIS", "=" * 60]
        
        lines.append(f"\n📊 Summary:")
        lines.append(f"  Sources: {self.stats.num_sources}")
        lines.append(f"  Domains: {self.stats.num_domains}")
        lines.append(f"  Async Resets: {self.stats.num_async_resets}")
        lines.append(f"  Sync Resets: {self.stats.num_sync_resets}")
        
        # 复位源
        if self.sources:
            lines.append(f"\n🔄 Reset Sources:")
            for s in self.sources:
                lines.append(f"  {s.name} ({s.type}, {s.async_or_sync})")
        
        # 复位域
        if self.domains:
            lines.append(f"\n🌊 Reset Domains:")
            for name, domain in self.domains.items():
                lines.append(f"  {name}:")
                if domain.async_resets:
                    lines.append(f"    async: {', '.join(domain.async_resets)}")
                if domain.sync_resets:
                    lines.append(f"    sync: {', '.join(domain.sync_resets)}")
        
        # 复位负载
        if self.loads:
            lines.append(f"\n📥 Reset Loads:")
            for load in self.loads[:10]:
                lines.append(f"  {load.signal} <- {load.reset} ({load.reset_type})")
        
        lines.append("=" * 60)
        return "\n".join(lines)


class ResetDomainAnalyzer:
    """复位域分析器"""
    
    # 复位关键字
    RESET_KEYWORDS = ['rst', 'reset', 'rst_n', 'rst_p', 'reset_n', 'reset_p']
    RESET_PATTERNS = [
        r'\b(\w*rst\w*)\b',
        r'\breset\b',
    ]
    
    def __init__(self, parser):
        self.parser = parser
        self.result = ResetDomainResult()
        self._analyze()
    
    def _analyze(self):
        """分析复位"""
        
        for fname, tree in self.parser.trees.items():
            code = self._get_code(fname)
            if not code:
                continue
            
            lines = code.split('\n')
            
            # 1. 提取复位输入端口
            self._extract_reset_inputs(lines, fname)
            
            # 2. 提取 always_ff 中的复位
            self._extract_ff_resets(lines, fname)
            
            # 3. 提取复位负载
            self._extract_reset_loads(lines, fname)
        
        # 4. 构建复位域
        self._build_domains()
        
        # 计算统计
        self._calculate_stats()
    
    def _get_code(self, fname: str) -> str:
        if fname in self.parser.trees:
            tree = self.parser.trees[fname]
            if hasattr(tree, 'source') and tree.source:
                return tree.source
        
        try:
            with open(fname) as f:
                return f.read()
        except:
            return ""
    
    def _extract_reset_inputs(self, lines: List[str], fname: str):
        """提取复位输入端口"""
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            if stripped.startswith('//'):
                continue
            
            # 检查 input 声明
            if stripped.startswith('input'):
                for kw in self.RESET_KEYWORDS:
                    if kw in stripped.lower():
                        # 提取信号名
                        match = re.search(rf'input\s+(?:logic\s+)?(?:\[\d+:\d+\]\s+)?(\w+)', stripped)
                        if match:
                            name = match.group(1)
                            
                            # 判断极性
                            polarity = "active_high"
                            if '_n' in name or '_p' in name:
                                if name.endswith('_n'):
                                    polarity = "active_low"
                            
                            # 判断同步/异步
                            # 简化：在 always_ff @(posedge clk or negedge rst) 为异步
                            async_or_sync = "sync"  # 默认
                            
                            self.result.sources.append(ResetSource(
                                name=name,
                                type="input",
                                polarity=polarity,
                                async_or_sync=async_or_sync,
                                line_number=i
                            ))
    
    def _extract_ff_resets(self, lines: List[str], fname: str):
        """从 always_ff 提取复位"""
        
        in_ff = False
        current_clock = ""
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            if stripped.startswith('always_ff'):
                in_ff = True
                continue
            
            if stripped.startswith('endmodule') or stripped.startswith('end'):
                in_ff = False
                continue
            
            if in_ff:
                # 提取时钟
                if '@(posedge' in stripped or '@(negedge' in stripped:
                    match = re.search(r'@\(pos?edge\s+(\w+)', stripped)
                    if match:
                        current_clock = match.group(1)
                
                # 提取复位 (同步)
                if 'if (' in stripped or 'if(' in stripped:
                    # 检查是否有复位条件
                    for kw in self.RESET_KEYWORDS:
                        if kw in stripped.lower():
                            # 这可能是同步复位
                            match = re.search(rf'if\s*\(\s*(!?{kw}\w*)', stripped, re.IGNORECASE)
                            if match:
                                rst = match.group(1)
                                polarity = "active_low" if rst.startswith('!') else "active_high"
                                
                                self.result.sources.append(ResetSource(
                                    name=rst.lstrip('!'),
                                    type="sync_ff",
                                    polarity=polarity,
                                    async_or_sync="sync",
                                    line_number=i
                                ))
                
                # 检查异步复位
                if 'negedge' in stripped or 'posedge' in stripped:
                    for kw in self.RESET_KEYWORDS:
                        if kw in stripped.lower():
                            match = re.search(rf'@\(pos?edge\s+(\w+)\s+or\s+pos?edge\s+(\w+)', stripped)
                            if match:
                                # 异步复位
                                rst = match.group(2)
                                
                                self.result.sources.append(ResetSource(
                                    name=rst,
                                    type="async_ff",
                                    polarity="active_low" if 'n' in rst else "active_high",
                                    async_or_sync="async",
                                    line_number=i
                                ))
    
    def _extract_reset_loads(self, lines: List[str], fname: str):
        """提取复位负载"""
        
        in_ff = False
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            if stripped.startswith('always_ff'):
                in_ff = True
                continue
            
            if stripped.startswith('endmodule') or stripped.startswith('end'):
                in_ff = False
                continue
            
            if in_ff:
                # 查找被复位的信号 (在 if (!rst) 块内)
                if 'if' in stripped and any(kw in stripped.lower() for kw in self.RESET_KEYWORDS):
                    # 提取赋值目标
                    match = re.search(r'<=\s*(\w+)', stripped)
                    if match:
                        signal = match.group(1)
                        
                        # 判断是同步还是异步
                        reset_type = "sync"
                        in_async = "or negedge" in lines[i-2] if i > 1 else False
                        
                        self.result.loads.append(ResetLoad(
                            signal=signal,
                            reset="detected",
                            reset_type=reset_type,
                            edge_level="edge"
                        ))
    
    def _build_domains(self):
        """构建复位域"""
        
        # 按复位信号分组
        reset_to_signals = defaultdict(list)
        
        for load in self.result.loads:
            reset_to_signals[load.reset].append(load.signal)
        
        # 为每个复位源创建域
        for source in self.result.sources:
            name = source.name
            
            domain = ResetDomain(name=name)
            
            if source.async_or_sync == "async":
                domain.async_resets.append(name)
            else:
                domain.sync_resets.append(name)
            
            # 添加负载
            if name in reset_to_signals:
                domain.components.extend(reset_to_signals[name])
            
            self.result.domains[name] = domain
    
    def _calculate_stats(self):
        """计算统计"""
        stats = self.result.stats
        
        stats.num_sources = len(self.result.sources)
        stats.num_domains = len(self.result.domains)
        stats.num_async_resets = sum(1 for s in self.result.sources if s.async_or_sync == "async")
        stats.num_sync_resets = sum(1 for s in self.result.sources if s.async_or_sync == "sync")
        
        if self.result.loads:
            stats.max_fanout = max(len([l for l in self.result.loads if l.reset == r]) 
                                   for r in set(l.reset for l in self.result.loads))
    
    def get_reset_domains(self) -> Dict[str, ResetDomain]:
        return self.result.domains
    
    def get_async_resets(self) -> List[ResetSource]:
        return [s for s in self.result.sources if s.async_or_sync == "async"]
    
    def get_sync_resets(self) -> List[ResetSource]:
        return [s for s in self.result.sources if s.async_or_sync == "sync"]


def analyze_reset_domain(parser) -> ResetDomainResult:
    """便捷函数"""
    analyzer = ResetDomainAnalyzer(parser)
    return analyzer.result
