"""TestabilityAnalyzer - 可测试性分析器。

评估设计对测试的友好程度：
- 可控性 (Controllability)
- 可观测性 (Observability)
- 扫描链就绪 (Scan Chain Ready)
- ATPG 覆盖率

Example:
    >>> from debug.analyzers.testability_analyzer import TestabilityAnalyzer
    >>> from parse import SVParser
    >>> parser = SVParser()
    >>> parser.parse_file("design.sv")
    >>> analyzer = TestabilityAnalyzer(parser)
    >>> result = analyzer.analyze()
    >>> print(analyzer.get_report())
"""
import sys
import os
import re
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from trace.driver import DriverCollector
from trace.load import LoadTracer


@dataclass
class ControllabilityScore:
    """可控性评分数据类。
    
    Attributes:
        direct: 直接可控数量 (input 直接驱动)
        indirect: 间接可控数量 (需要通过组合逻辑)
        difficult: 难可控数量 (需要特殊序列)
        total: 总信号数
        score: 可控性评分 (0-100)
    """
    direct: int = 0
    indirect: int = 0
    difficult: int = 0
    total: int = 0
    score: float = 0.0
    
    def calculate(self) -> float:
        """计算可控性评分。
        
        Returns:
            float: 评分 (0-100)
        """
        if self.total > 0:
            self.score = (self.direct * 100 + self.indirect * 50 + self.difficult * 10) / self.total
        return self.score


@dataclass
class ObservabilityScore:
    """可观测性评分数据类。
    
    Attributes:
        direct: 直接可观测数量 (output 直接输出)
        indirect: 间接可观测数量 (通过状态信号)
        difficult: 难观测数量 (需要复杂序列)
        total: 总信号数
        score: 可观测性评分 (0-100)
    """
    direct: int = 0
    indirect: int = 0
    difficult: int = 0
    total: int = 0
    score: float = 0.0


@dataclass
class ScanChainInfo:
    """扫描链信息数据类。
    
    Attributes:
        name: 扫描链名称
        length: 链长度 (寄存器数量)
        is_scanable: 是否可扫描
        ready: 是否就绪
    """
    name: str
    length: int = 0
    is_scanable: bool = False
    ready: bool = False


@dataclass
class TestabilityResult:
    """可测试性分析结果数据类。
    
    Attributes:
        module_name: 模块名
        controllability: 可控性评分
        observability: 可观测性评分
        scan_chains: 扫描链信息列表
        scan_ready: 是否扫描就绪
        atpg_coverage: ATPG 覆盖率估计
    """
    module_name: str
    controllability: ControllabilityScore = None
    observability: ObservabilityScore = None
    scan_chains: List[ScanChainInfo] = field(default_factory=list)
    scan_ready: bool = False
    atpg_coverage: float = 0.0
    
    def __post_init__(self):
        if self.controllability is None:
            self.controllability = ControllabilityScore()
        if self.observability is None:
            self.observability = ObservabilityScore()


class TestabilityAnalyzer:
    """可测试性分析器。
    
    评估设计对测试的友好程度。

    Attributes:
        parser: SVParser 实例
        results: 分析结果字典
    
    Example:
        >>> analyzer = TestabilityAnalyzer(parser)
        >>> result = analyzer.analyze()
    """
    
    def __init__(self, parser):
        """初始化分析器。
        
        Args:
            parser: SVParser 实例
        """
        self.parser = parser
        self.results: Dict[str, TestabilityResult] = {}
    
    def analyze(self) -> Dict[str, TestabilityResult]:
        """执行可测试性分析。
        
        Returns:
            Dict[str, TestabilityResult]: 模块名到结果的映射
        """
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
                result = self._analyze_module(member, mod_name)
                self.results[mod_name] = result
        
        return self.results
    
    def _analyze_module(self, module, module_name: str) -> TestabilityResult:
        """分析单个模块。
        
        Args:
            module: 模块节点
            module_name: 模块名
        
        Returns:
            TestabilityResult: 分析结果
        """
        result = TestabilityResult(module_name=module_name)
        
        # TODO: 实现完整的可测试性分析
        # 1. 收集所有信号
        # 2. 计算可控性
        # 3. 计算可观测性
        # 4. 检查扫描链
        
        return result
    
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
        lines.append("TESTABILITY ANALYSIS REPORT")
        lines.append("=" * 60)
        
        for mod_name, result in self.results.items():
            lines.append(f"\n📦 {mod_name}")
            lines.append(f"  Controllability: {result.controllability.score:.1f}/100")
            lines.append(f"  Observability: {result.observability.score:.1f}/100")
            lines.append(f"  Scan Ready: {'Yes' if result.scan_ready else 'No'}")
            lines.append(f"  ATPG Coverage: {result.atpg_coverage:.1f}%")
        
        return "\n".join(lines)
