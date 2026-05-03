"""ClockDomainAnalyzer - 时钟域分析。

分析设计中的时钟域，检测跨时钟域路径和 CDC 问题。

Example:
    >>> from debug.analyzers.clock_domain import ClockDomainAnalyzer
    >>> from parse import SVParser
    >>> parser = SVParser()
    >>> parser.parse_file("design.sv")
    >>> analyzer = ClockDomainAnalyzer(parser)
    >>> report = analyzer.analyze()
    >>> print(analyzer.get_report())
"""
import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class ClockInfo:
    """时钟信息数据类。
    
    Attributes:
        name: 时钟名
        frequency: 频率 (MHz)
        period: 周期 (ns)
        source: 来源 (always_ff/PLL/外部)
        module: 所属模块
    """
    name: str
    frequency: float = 0.0
    period: float = 0.0
    source: str = ""
    module: str = ""


@dataclass
class ResetInfo:
    """复位信息数据类。
    
    Attributes:
        name: 复位名
        async_: 是否异步
        polarity: 极性 (HIGH/LOW)
        module: 所属模块
    """
    name: str
    async_: bool = False
    polarity: str = "HIGH"
    module: str = ""


@dataclass
class ClockDomain:
    """时钟域数据类。
    
    Attributes:
        clock: 时钟信息
        registers: 寄存器列表
        associated_resets: 关联的复位
    """
    clock: ClockInfo
    registers: List[str] = None
    associated_resets: List[ResetInfo] = None
    
    def __post_init__(self):
        if self.registers is None:
            self.registers = []
        if self.associated_resets is None:
            self.associated_resets = []


class ClockDomainAnalyzer:
    """时钟域分析器。
    
    分析设计中的时钟域、复位和跨时钟域路径。

    Attributes:
        parser: SVParser 实例
        clock_domains: 时钟域字典
        reset_info: 复位信息字典
        crossings: 跨时钟域路径列表
    
    Example:
        >>> analyzer = ClockDomainAnalyzer(parser)
        >>> report = analyzer.analyze()
    """
    
    def __init__(self, parser):
        """初始化分析器。
        
        Args:
            parser: SVParser 实例
        """
        self.parser = parser
        self.clock_domains: Dict[str, ClockDomain] = {}
        self.reset_info: Dict[str, ResetInfo] = {}
        self.crossings: List[Dict] = []
        self._analyze()
    
    def _analyze(self):
        """执行分析。"""
        self._find_clocks()
        self._find_resets()
        self._find_clock_domain_crossings()
    
    def _find_clocks(self):
        """查找所有时钟。"""
        for fname, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            root = tree.root
            if not hasattr(root, 'members'):
                continue
            
            for i in range(len(root.members)):
                member = root.members[i]
                if 'ModuleDeclaration' not in str(type(member)):
                    continue
                
                mod_name = self._get_module_name(member)
                
                if hasattr(member, 'members') and member.members:
                    for j in range(len(member.members)):
                        stmt = member.members[j]
                        if not stmt:
                            continue
                        
                        stmt_str = str(stmt)
                        
                        # 检测 always_ff 时钟
                        if 'always_ff' in stmt_str:
                            clock_match = re.search(r"@(posedge|negedge)\s+(\w+)", stmt_str)
                            if clock_match:
                                clk_name = clock_match.group(2)
                                if clk_name not in self.clock_domains:
                                    self.clock_domains[clk_name] = ClockDomain(
                                        clock=ClockInfo(
                                            name=clk_name,
                                            source="always_ff",
                                            module=mod_name
                                        )
                                    )
    
    def _find_resets(self):
        """查找所有复位。"""
        for fname, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            root = tree.root
            if not hasattr(root, 'members'):
                continue
            
            for i in range(len(root.members)):
                member = root.members[i]
                if 'ModuleDeclaration' not in str(type(member)):
                    continue
                
                mod_name = self._get_module_name(member)
                
                if hasattr(member, 'members') and member.members:
                    for j in range(len(member.members)):
                        stmt = member.members[j]
                        if not stmt:
                            continue
                        
                        stmt_str = str(stmt)
                        
                        # 检测 always_ff 复位
                        if 'always_ff' in stmt_str:
                            # 检测异步复位
                            async_match = re.search(r"@(.*?)\s+if\s*\(\s*(\w+)", stmt_str)
                            if async_match:
                                reset_name = async_match.group(2).strip()
                                if reset_name not in self.reset_info:
                                    self.reset_info[reset_name] = ResetInfo(
                                        name=reset_name,
                                        async_=True,
                                        polarity="HIGH",
                                        module=mod_name
                                    )
    
    def _find_clock_domain_crossings(self):
        """查找跨时钟域路径。"""
        # TODO: 实现跨时钟域路径检测
        pass
    
    def _get_module_name(self, module_node) -> str:
        """获取模块名。"""
        if hasattr(module_node, 'header') and module_node.header:
            if hasattr(module_node.header, 'name') and module_node.header.name:
                name = module_node.header.name
                if hasattr(name, 'value'):
                    return str(name.value).strip()
                return str(name).strip()
        return ""
    
    def get_report(self) -> str:
        """获取分析报告。
        
        Returns:
            str: 格式化的报告字符串
        """
        lines = []
        lines.append("=" * 60)
        lines.append("CLOCK DOMAIN ANALYSIS")
        lines.append("=" * 60)
        
        lines.append(f"\n[Clock Domains] ({len(self.clock_domains)})")
        for name, domain in self.clock_domains.items():
            lines.append(f"  {name}: {domain.clock.source} ({domain.clock.module})")
        
        lines.append(f"\n[Resets] ({len(self.reset_info)})")
        for name, reset in self.reset_info.items():
            async_str = "async" if reset.async_ else "sync"
            lines.append(f"  {name}: {async_str} {reset.polarity} ({reset.module})")
        
        return "\n".join(lines)
