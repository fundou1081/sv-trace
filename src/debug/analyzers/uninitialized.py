"""UninitializedDetector - 检测未初始化寄存器。

检测 always_ff 块中没有复位或初始化的寄存器。

Example:
    >>> from debug.analyzers.uninitialized import UninitializedDetector
    >>> from parse import SVParser
    >>> parser = SVParser()
    >>> parser.parse_file("design.sv")
    >>> detector = UninitializedDetector(parser)
    >>> issues = detector.detect("data_out")
    >>> for issue in issues:
    ...     print(f"{issue.issue_type}: {issue.description}")
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from typing import List, Dict
from dataclasses import dataclass


@dataclass
class UninitializedIssue:
    """未初始化问题数据类。
    
    Attributes:
        signal: 信号名
        issue_type: 问题类型 (no_reset/no_init/conditional)
        description: 问题描述
        severity: 严重级别 (high/medium/low)
    """
    signal: str
    issue_type: str  # no_reset, no_init, conditional
    description: str
    severity: str  # high, medium, low
    
    @staticmethod
    def extract_from_text(source: str):
        """从源码文本提取未初始化信号。
        
        Args:
            source: SystemVerilog 源代码字符串
        
        Returns:
            UninitializedDetector: 检测器实例
        """
        import pyslang
        
        try:
            tree = pyslang.SyntaxTree.fromText(source)
            
            class TextParser:
                def __init__(self, tree):
                    self.trees = {"input.sv": tree}
            
            return UninitializedDetector(TextParser(tree))
        except Exception as e:
            print(f"Uninitialized detect error: {e}")
            return None


class UninitializedDetector:
    """未初始化寄存器检测器。
    
    检测 always_ff 块中没有复位或初始化的寄存器。

    Attributes:
        parser: SVParser 实例
        _driver_tracer: 驱动追踪器（懒加载）
        _load_tracer: 负载追踪器（懒加载）
    
    Example:
        >>> detector = UninitializedDetector(parser)
        >>> issues = detector.detect("data_out")
    """
    
    def __init__(self, parser):
        """初始化检测器。
        
        Args:
            parser: SVParser 实例
        """
        self.parser = parser
        self._driver_tracer = None
        self._load_tracer = None
    
    def _get_tracers(self):
        """懒加载 tracer。
        
        Returns:
            Tuple[DriverTracer, LoadTracer]: 追踪器元组
        """
        if not self._driver_tracer:
            from trace.driver import DriverTracer
            self._driver_tracer = DriverTracer(self.parser)
        if not self._load_tracer:
            from trace.load import LoadTracer
            self._load_tracer = LoadTracer(self.parser)
        return self._driver_tracer, self._load_tracer
    
    def detect(self, signal: str) -> List[UninitializedIssue]:
        """检测单个信号的未初始化问题。
        
        Args:
            signal: 信号名
        
        Returns:
            List[UninitializedIssue]: 问题列表
        """
        issues = []
        
        driver_tracer, load_tracer = self._get_tracers()
        drivers = driver_tracer.find_driver(signal)
        
        # 检查是否为 always_ff 驱动
        ff_drivers = [d for d in drivers if 'always_ff' in str(type(d)).lower()]
        if not ff_drivers:
            return issues
        
        # 检查是否有复位分支
        has_reset = False
        has_init = False
        
        for d in ff_drivers:
            sources = getattr(d, 'sources', [])
            for src in sources:
                src_str = str(src).lower()
                if 'reset' in src_str or 'rst' in src_str:
                    has_reset = True
                if 'init' in src_str or '0' in src_str:
                    has_init = True
        
        if not has_reset:
            issues.append(UninitializedIssue(
                signal=signal,
                issue_type="no_reset",
                description=f"Register '{signal}' has no reset path in always_ff",
                severity="high"
            ))
        
        if not has_init and not has_reset:
            issues.append(UninitializedIssue(
                signal=signal,
                issue_type="no_init",
                description=f"Register '{signal}' has no initialization value",
                severity="medium"
            ))
        
        return issues
    
    def detect_all(self) -> List[UninitializedIssue]:
        """检测所有信号的未初始化问题。
        
        Returns:
            List[UninitializedIssue]: 所有问题
        """
        all_issues = []
        
        for fname, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            root = tree.root
            if not hasattr(root, 'members') or not root.members:
                continue
            
            for i in range(len(root.members)):
                member = root.members[i]
                if 'ModuleDeclaration' not in str(type(member)):
                    continue
                
                signals = self._find_ff_signals(member)
                for sig in signals:
                    issues = self.detect(sig)
                    all_issues.extend(issues)
        
        return all_issues
    
    def _find_ff_signals(self, module) -> List[str]:
        """查找模块中的 always_ff 信号。
        
        Args:
            module: 模块节点
        
        Returns:
            List[str]: 信号名列表
        """
        signals = []
        
        if not hasattr(module, 'members') or not module.members:
            return signals
        
        for j in range(len(module.members)):
            stmt = module.members[j]
            if not stmt:
                continue
            
            if 'DataDeclaration' in str(type(stmt)):
                if hasattr(stmt, 'declarators') and stmt.declarators:
                    try:
                        for decl in stmt.declarators:
                            if hasattr(decl, 'name') and decl.name:
                                name = decl.name
                                if hasattr(name, 'value'):
                                    signals.append(str(name.value).strip())
                                else:
                                    signals.append(str(name).strip())
                    except:
                        pass
        
        return signals
