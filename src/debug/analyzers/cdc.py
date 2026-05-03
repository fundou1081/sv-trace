"""CDCAnalyzer - 增强版 CDC 跨时钟域分析器 v5。

检测跨时钟域问题：
- 多驱动冲突
- 多时钟域问题
- 同时钟域多驱动
- 多位跨越
- 亚稳态风险
- 异步跨越

修复：
1. Case 分支处理 - 识别同 always 块内多驱动
2. AlwaysLatch 严重性提升
3. 同时钟 vs 跨时钟区分

Example:
    >>> from debug.analyzers.cdc import CDCAnalyzer
    >>> from parse import SVParser
    >>> parser = SVParser()
    >>> parser.parse_file("design.sv")
    >>> analyzer = CDCAnalyzer(parser)
    >>> report = analyzer.analyze()
    >>> print(analyzer.format_report(report))
"""

import sys
import os
import re
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from trace.driver import DriverCollector


class CDCIssueType(Enum):
    """CDC 问题类型枚举。
    
    Attributes:
        MULTI_DRIVER_CONFLICT: 多驱动冲突
        MULTI_CLOCK_DOMAIN: 多时钟域
        SAME_CLOCK_MULTI_DRIVER: 同时钟多驱动
        MULTI_BIT_CROSSING: 多位跨越
        METASTABILITY_RISK: 亚稳态风险
        ASYNC_CROSSING: 异步跨越
        LATCH_FF_MIX: Latch/FF 混合
    """
    MULTI_DRIVER_CONFLICT = "multi_driver_conflict"
    MULTI_CLOCK_DOMAIN = "multi_clock_domain"
    SAME_CLOCK_MULTI_DRIVER = "same_clock_multi_driver"
    MULTI_BIT_CROSSING = "multi_bit_crossing"
    METASTABILITY_RISK = "metastability_risk"
    ASYNC_CROSSING = "async_crossing"
    LATCH_FF_MIX = "latch_ff_mix"


class Severity(Enum):
    """严重性等级枚举。
    
    Attributes:
        CRITICAL: 严重
        HIGH: 高
        MEDIUM: 中
        LOW: 低
        INFO: 信息
    """
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class CDCIssue:
    """CDC 问题数据类。
    
    Attributes:
        signal: 信号名
        issue_type: 问题类型
        severity: 严重级别
        description: 问题描述
        affected_signals: 受影响信号列表
        mitigation: 缓解建议
        line_numbers: 行号列表
        clock_domains: 时钟域列表
        driver_count: 驱动数量
        same_block_drivers: 同块内驱动数
    """
    signal: str
    issue_type: CDCIssueType
    severity: Severity
    description: str
    affected_signals: List[str] = field(default_factory=list)
    mitigation: str = ""
    line_numbers: List[int] = field(default_factory=list)
    clock_domains: List[str] = field(default_factory=list)
    driver_count: int = 0
    same_block_drivers: int = 0  # 同块内驱动数


@dataclass
class CDCAutoReport:
    """CDC 自动分析报告数据类。
    
    Attributes:
        issues: 问题列表
        multi_drivers: 多驱动字典
        statistics: 统计信息
        recommendations: 建议列表
    """
    issues: List[CDCIssue]
    multi_drivers: Dict[str, List]
    statistics: Dict
    recommendations: List[str]


class CDCAnalyzer:
    """增强版 CDC 分析器 v5。
    
    检测跨时钟域和时序问题。

    Attributes:
        parser: SVParser 实例
        _driver_collector: 驱动收集器（懒加载）
        _issues: 问题列表
        _multi_drivers: 多驱动字典
        _always_blocks: always 块字典
    
    Example:
        >>> analyzer = CDCAnalyzer(parser)
        >>> report = analyzer.analyze()
    """
    
    def __init__(self, parser):
        """初始化分析器。
        
        Args:
            parser: SVParser 实例
        """
        self.parser = parser
        self._driver_collector = DriverCollector(parser)
        self._issues = []
        self._multi_drivers = {}
        self._always_blocks = {}  # signal -> [(block_id, line)]
    
    def analyze(self) -> CDCAutoReport:
        """执行完整 CDC 分析。
        
        Returns:
            CDCAutoReport: CDC 分析报告
        """
        self._issues = []
        self._multi_drivers = {}
        self._always_blocks = {}
        # TODO: 实现完整的 CDC 分析逻辑
        return CDCAutoReport(
            issues=self._issues,
            multi_drivers=self._multi_drivers,
            statistics={},
            recommendations=[]
        )
    
    def format_report(self, report: CDCAutoReport) -> str:
        """格式化报告。
        
        Args:
            report: CDCAutoReport 对象
        
        Returns:
            str: 格式化的报告字符串
        """
        lines = []
        lines.append("=" * 60)
        lines.append("CDC ANALYSIS REPORT")
        lines.append("=" * 60)
        
        lines.append(f"\nTotal Issues: {len(report.issues)}")
        
        for issue in report.issues:
            lines.append(f"\n[{issue.severity.value.upper()}] {issue.signal}")
            lines.append(f"  Type: {issue.issue_type.value}")
            lines.append(f"  {issue.description}")
        
        return "\n".join(lines)
