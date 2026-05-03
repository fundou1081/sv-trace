"""MultiDriverDetector - 多驱动检测器 (完整版)。

检测信号多驱动问题，提供详细的驱动分析。

Example:
    >>> from debug.analyzers.multi_driver_detector import MultiDriverDetector
    >>> detector = MultiDriverDetector(parser)
    >>> result = detector.detect_all()
    >>> print(detector.format_report(result))
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from typing import Dict, List
from dataclasses import dataclass
from enum import Enum


class DriverType(Enum):
    """驱动类型枚举。
    
    Attributes:
        CONTINUOUS: 连续赋值 (assign)
        ALWAYS_FF: 时序逻辑 (always_ff)
        ALWAYS_COMB: 组合逻辑 (always_comb)
        ALWAYS_LATCH: 锁存逻辑 (always_latch)
        PROCEDURAL: 过程赋值
    """
    CONTINUOUS = "continuous"
    ALWAYS_FF = "always_ff"
    ALWAYS_COMB = "always_comb"
    ALWAYS_LATCH = "always_latch"
    PROCEDURAL = "procedural"


@dataclass
class DriverSource:
    """驱动源数据类。
    
    Attributes:
        driver_type: 驱动类型
        expression: 驱动表达式
        location: 位置
        module: 所属模块
    """
    driver_type: DriverType
    expression: str
    location: str = ""
    module: str = ""


@dataclass
class MultiDriverResult:
    """多驱动结果数据类。
    
    Attributes:
        signal: 信号名
        drivers: 驱动源列表
        has_conflict: 是否有冲突
        severity: 严重级别
    """
    signal: str
    drivers: List[DriverSource]
    has_conflict: bool
    severity: str


class MultiDriverDetector:
    """多驱动检测器。
    
    检测信号被多个源驱动的问题。

    Attributes:
        parser: SVParser 实例
    
    Example:
        >>> detector = MultiDriverDetector(parser)
        >>> result = detector.detect_all()
    """
    
    def __init__(self, parser):
        """初始化检测器。
        
        Args:
            parser: SVParser 实例
        """
        self.parser = parser
    
    def detect(self, signal: str) -> List[MultiDriverResult]:
        """检测指定信号的多驱动问题。
        
        Args:
            signal: 信号名
        
        Returns:
            List[MultiDriverResult]: 检测结果列表
        """
        from trace.driver import DriverTracer
        
        results = []
        tracer = DriverTracer(self.parser)
        drivers = tracer.find_driver(signal)
        
        if len(drivers) > 1:
            driver_sources = []
            for d in drivers:
                drv_type = self._classify_driver(d)
                driver_sources.append(DriverSource(
                    driver_type=drv_type,
                    expression=getattr(d, 'source_expr', str(d))
                ))
            
            has_conflict = self._check_conflict(driver_sources)
            
            results.append(MultiDriverResult(
                signal=signal,
                drivers=driver_sources,
                has_conflict=has_conflict,
                severity="error" if has_conflict else "warning"
            ))
        
        return results
    
    def detect_all(self) -> List[MultiDriverResult]:
        """检测所有信号的多驱动问题。
        
        Returns:
            List[MultiDriverResult]: 所有检测结果
        """
        all_results = []
        
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
                
                signals = self._find_signals(member)
                for sig in signals:
                    results = self.detect(sig)
                    all_results.extend(results)
        
        return all_results
    
    def _classify_driver(self, driver) -> DriverType:
        """分类驱动类型。"""
        drv_str = str(type(driver).__name__).lower()
        
        if 'continuous' in drv_str or 'assign' in drv_str:
            return DriverType.CONTINUOUS
        elif 'always_ff' in drv_str or 'ff' in drv_str:
            return DriverType.ALWAYS_FF
        elif 'always_comb' in drv_str:
            return DriverType.ALWAYS_COMB
        elif 'always_latch' in drv_str or 'latch' in drv_str:
            return DriverType.ALWAYS_LATCH
        else:
            return DriverType.PROCEDURAL
    
    def _check_conflict(self, drivers: List[DriverSource]) -> bool:
        """检查是否有冲突。"""
        if len(drivers) < 2:
            return False
        
        types = set(d.driver_type for d in drivers)
        
        # 不同类型的驱动通常冲突
        if len(types) > 1:
            return True
        
        return False
    
    def _find_signals(self, module) -> List[str]:
        """查找模块中的信号。"""
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
    
    def format_report(self, results: List[MultiDriverResult]) -> str:
        """格式化报告。
        
        Args:
            results: 检测结果
        
        Returns:
            str: 格式化的报告字符串
        """
        lines = []
        lines.append("=" * 60)
        lines.append("MULTI-DRIVER DETECTION REPORT")
        lines.append("=" * 60)
        
        if not results:
            lines.append("\n✅ No multi-driver issues found")
        else:
            lines.append(f"\n⚠️  Found {len(results)} multi-driver signal(s)")
            
            for r in results:
                lines.append(f"\n[{r.severity.upper()}] {r.signal}")
                for d in r.drivers:
                    lines.append(f"  - {d.driver_type.value}: {d.expression[:50]}")
        
        return "\n".join(lines)
