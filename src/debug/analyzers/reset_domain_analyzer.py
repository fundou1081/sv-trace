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


# =============================================================================
# 复位完整性检查增强
# =============================================================================

@dataclass
class ResetTreeNode:
    """复位树节点"""
    signal: str
    fanout: int = 0
    level: int = 0
    children: List[str] = field(default_factory=list)
    parent: str = ""


@dataclass
class ResetIntegrityReport:
    """复位完整性报告"""
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    reset_tree: Dict[str, ResetTreeNode] = field(default_factory=dict)
    power_on_sequence: List[str] = field(default_factory=list)
    coverage: float = 0.0


class ResetIntegrityChecker:
    """复位完整性检查器"""
    
    def __init__(self, parser):
        self.parser = parser
        self.reset_sources: List[ResetSource] = []
        self.reset_loads: List[ResetLoad] = []
        self._collect()
    
    def _collect(self):
        """收集复位信息"""
        analyzer = ResetDomainAnalyzer(self.parser)
        self.reset_sources = analyzer.result.sources
        self.reset_loads = analyzer.result.loads
    
    def check(self) -> ResetIntegrityReport:
        """执行完整性检查"""
        report = ResetIntegrityReport()
        
        # 1. 检查复位类型混合
        self._check_reset_mixing(report)
        
        # 2. 检查复位树
        self._check_reset_tree(report)
        
        # 3. 检查负载均衡
        self._check_fanout_balance(report)
        
        # 4. 检查同步复位vs异步复位
        self._check_async_vs_sync(report)
        
        # 5. 生成上电序列
        self._generate_power_on_sequence(report)
        
        # 6. 计算覆盖率
        self._calculate_coverage(report)
        
        # 7. 生成建议
        self._generate_recommendations(report)
        
        return report
    
    def _check_reset_mixing(self, report: ResetIntegrityReport):
        """检查同一信号使用混合复位"""
        signals_with_both = []
        
        signal_resets: Dict[str, List[str]] = defaultdict(list)
        for load in self.reset_loads:
            signal_resets[load.signal].append(load.reset_type)
        
        for sig, types in signal_resets.items():
            if 'sync' in types and 'async' in types:
                signals_with_both.append(sig)
        
        if signals_with_both:
            report.issues.append(
                f"发现{len(signals_with_both)}个信号同时使用同步和异步复位: {signals_with_both[:5]}"
            )
    
    def _check_reset_tree(self, report: ResetIntegrityReport):
        """检查复位树结构"""
        # 构建复位树
        reset_tree: Dict[str, ResetTreeNode] = {}
        
        for source in self.reset_sources:
            node = ResetTreeNode(
                signal=source.name,
                level=0,
                fanout=0
            )
            # 计算fanout
            for load in self.reset_loads:
                if load.reset == source.name or load.reset in source.name:
                    node.fanout += 1
            reset_tree[source.name] = node
            report.reset_tree[source.name] = node
        
        # 检查不平衡
        fanouts = [n.fanout for n in reset_tree.values()]
        if fanouts:
            max_fanout = max(fanouts)
            min_fanout = min(fanouts)
            
            if max_fanout > min_fanout * 10:
                report.warnings.append(
                    f"复位树不平衡: 最大fanout={max_fanout}, 最小fanout={min_fanout}"
                )
    
    def _check_fanout_balance(self, report: ResetIntegrityReport):
        """检查复位负载均衡"""
        reset_fanout: Dict[str, int] = defaultdict(int)
        
        for load in self.reset_loads:
            for source in self.reset_sources:
                if load.reset in source.name or source.name in load.reset:
                    reset_fanout[source.name] += 1
        
        for reset, fanout in reset_fanout.items():
            if fanout > 100:
                report.warnings.append(
                    f"复位信号'{reset}'扇出过大({fanout})，建议拆分"
                )
            if fanout == 0:
                report.warnings.append(f"复位信号'{reset}'未被使用")
    
    def _check_async_vs_sync(self, report: ResetIntegrityReport):
        """检查异步vs同步复位"""
        async_count = sum(1 for s in self.reset_sources if s.async_or_sync == "async")
        sync_count = sum(1 for s in self.reset_sources if s.async_or_sync == "sync")
        
        if async_count > sync_count * 2:
            report.warnings.append(
                f"异步复位使用过多({async_count})，考虑使用更多同步复位以简化时序收敛"
            )
        
        # 检查异步复位风险
        async_resets = [s for s in self.reset_sources if s.async_or_sync == "async"]
        for ar in async_resets:
            if ar.polarity == "active_low":
                report.warnings.append(
                    f"异步低有效复位'{ar.name}'可能导致亚稳态，建议使用同步复位"
                )
    
    def _generate_power_on_sequence(self, report: ResetIntegrityReport):
        """生成上电序列"""
        sequence = []
        
        # 1. 外部电源稳定
        sequence.append("1. 外部电源稳定")
        
        # 2. 时钟稳定
        sequence.append("2. 时钟稳定")
        
        # 3. 异步复位释放
        async_resets = [s for s in self.reset_sources if s.async_or_sync == "async"]
        for ar in async_resets:
            sequence.append(f"3. 释放异步复位 {ar.name}")
        
        # 4. 同步复位释放
        sync_resets = [s for s in self.reset_sources if s.async_or_sync == "sync"]
        for sr in sync_resets:
            sequence.append(f"4. 释放同步复位 {sr.name}")
        
        # 5. 电路工作
        sequence.append("5. 电路开始正常工作")
        
        report.power_on_sequence = sequence
    
    def _calculate_coverage(self, report: ResetIntegrityReport):
        """计算复位覆盖率"""
        # 统计应该被复位的寄存器
        from debug.analyzers.clock_domain import ClockDomainAnalyzer
        
        cda = ClockDomainAnalyzer(self.parser)
        regs = cda.get_all_registers()
        
        if not regs:
            report.coverage = 100.0
            return
        
        # 被复位的寄存器
        reset_signals = set(s.name for s in self.reset_sources)
        reset_load_signals = set(l.signal for l in self.reset_loads)
        
        # 覆盖率 = 被复位的寄存器 / 总寄存器
        reset_count = len(reset_load_signals)
        total_regs = len(regs)
        
        coverage = (reset_count / total_regs * 100) if total_regs > 0 else 100.0
        report.coverage = min(coverage, 100.0)
    
    def _generate_recommendations(self, report: ResetIntegrityReport):
        """生成改进建议"""
        # 基于问题生成建议
        if any("混合" in i for i in report.issues):
            report.recommendations.append(
                "避免对同一信号同时使用同步和异步复位"
            )
        
        if any("扇出过大" in w for w in report.warnings):
            report.recommendations.append(
                "对高扇出复位信号使用复位树缓冲器"
            )
        
        if any("亚稳态" in w for w in report.warnings):
            report.recommendations.append(
                "考虑将异步复位改为同步复位以改善时序"
            )
        
        if report.coverage < 80:
            report.recommendations.append(
                f"复位覆盖率({report.coverage:.1f}%)偏低，确保所有关键寄存器都有复位"
            )
        
        if not report.recommendations:
            report.recommendations.append("复位设计良好")


# 添加便捷方法
def check_reset_integrity(parser) -> ResetIntegrityReport:
    """便捷函数"""
    checker = ResetIntegrityChecker(parser)
    return checker.check()


__all__ = [
    'ResetDomainAnalyzer',
    'ResetDomainResult',
    'ResetSource',
    'ResetDomain',
    'ResetLoad',
    'ResetStats',
    'ResetIntegrityChecker',
    'ResetIntegrityReport',
    'ResetTreeNode',
    'check_reset_integrity',
]


# === pyslang 版本方法 (2026-04-29) ===

def extract_reset_signals_from_text(code: str) -> List[dict]:
    """从源码提取复位相关信号 (使用 pyslang)"""
    import pyslang
    from pyslang import SyntaxKind
    
    results = []
    
    def collect(node):
        kind_name = node.kind.name
        
        # 检查是否是 input 端口且名字包含 reset
        if kind_name == 'ImplicitAnsiPort':
            header = getattr(node, 'header', None)
            if header:
                direction = getattr(header, 'direction', None)
                if direction and 'Input' in direction.kind.name:
                    decl = getattr(node, 'declarator', None)
                    if decl:
                        name = str(decl.name) if hasattr(decl, 'name') else ''
                        if 'rst' in name.lower() or 'reset' in name.lower():
                            results.append({
                                'name': name,
                                'kind': 'reset_input',
                                'type': 'input'
                            })
        
        return pyslang.VisitAction.Advance
    
    try:
        tree = pyslang.SyntaxTree.fromText(code)
        tree.root.visit(collect)
    except Exception as e:
        pass
    
    return results


def extract_async_reset_from_text(code: str) -> List[dict]:
    """从源码提取异步复位 always_ff 块 (使用 pyslang)"""
    import pyslang
    from pyslang import SyntaxKind
    
    results = []
    
    def collect(node):
        kind_name = node.kind.name
        
        if 'AlwaysFf' in kind_name:
            # 检查是否有异步复位 (or negedge rst)
            item_str = str(node)
            if 'or' in item_str.lower() and ('rst' in item_str.lower() or 'reset' in item_str.lower()):
                results.append({
                    'kind': 'async_always_ff',
                    'expr': item_str[:60].replace('\n', ' ')
                })
        
        return pyslang.VisitAction.Advance
    
    try:
        tree = pyslang.SyntaxTree.fromText(code)
        tree.root.visit(collect)
    except Exception as e:
        pass
    
    return results
