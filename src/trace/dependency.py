"""
DependencyAnalyzer - 信号依赖分析
分析信号的前向依赖（影响它的）和后向依赖（它影响的）

增强版: 添加解析警告，显式打印不支持的语法结构
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
import re

# 导入解析警告模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from trace.parse_warn import (
    ParseWarningHandler,
    warn_unsupported,
    warn_error,
    WarningLevel
)


@dataclass
class SignalDependency:
    """信号依赖关系"""
    signal: str                  # 信号名
    depends_on: List[str] = field(default_factory=list)  # 前向依赖（影响它的）
    influences: List[str] = field(default_factory=list)   # 后向依赖（它影响的）
    source_signals: List[str] = field(default_factory=list)  # 源头信号（无依赖）
    sink_signals: List[str] = field(default_factory=list)    # 汇信号（无后向）


class DependencyAnalyzer:
    """信号依赖分析器
    
    增强: 添加解析警告
    """
    
    # 不支持的语法类型
    UNSUPPORTED_TYPES = {
        'CovergroupDeclaration': 'covergroup不影响信号依赖分析',
        'PropertyDeclaration': 'property声明无信号依赖',
        'SequenceDeclaration': 'sequence声明无信号依赖',
        'ClassDeclaration': 'class内部信号依赖分析可能不完整',
        'InterfaceDeclaration': 'interface内部信号依赖分析可能不完整',
        'PackageDeclaration': 'package无信号依赖',
        'ProgramDeclaration': 'program块信号依赖分析可能不完整',
        'ClockingBlock': 'clocking block信号依赖分析有限',
    }
    
    def __init__(self, parser, verbose: bool = True):
        self.parser = parser
        self.verbose = verbose
        # 创建警告处理器
        self.warn_handler = ParseWarningHandler(
            verbose=verbose,
            component="DependencyAnalyzer"
        )
        self._driver_cache: Dict[str, List[str]] = {}
        self._load_cache: Dict[str, List[str]] = {}
        self._unsupported_encountered: Set[str] = set()
    
    def analyze(self, signal_name: str, module_name: str = None) -> SignalDependency:
        """分析信号的依赖关系"""
        
        # 1. 找前向依赖（驱动这个信号的信号）
        forward_deps = self._find_forward_dependencies(signal_name, module_name)
        
        # 2. 找后向依赖（这个信号影响的信号）
        backward_deps = self._find_backward_dependencies(signal_name, module_name)
        
        # 3. 找源头信号（没有前向依赖的）
        source_signals = self._find_source_signals(signal_name, module_name, forward_deps)
        
        # 4. 找汇信号（没有后向依赖的）
        sink_signals = backward_deps  # 简化处理
        
        return SignalDependency(
            signal=signal_name,
            depends_on=forward_deps,
            influences=backward_deps,
            source_signals=source_signals,
            sink_signals=sink_signals
        )
    
    def _check_unsupported_syntax(self):
        """检查不支持的语法"""
        for key, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            root = tree.root
            if hasattr(root, 'members') and root.members:
                try:
                    members = list(root.members) if hasattr(root.members, '__iter__') else [root.members]
                    for member in members:
                        if member is None:
                            continue
                        kind_name = str(member.kind) if hasattr(member, 'kind') else type(member).__name__
                        
                        if kind_name in self.UNSUPPORTED_TYPES:
                            if kind_name not in self._unsupported_encountered:
                                self.warn_handler.warn_unsupported(
                                    kind_name,
                                    context=key,
                                    suggestion=self.UNSUPPORTED_TYPES[kind_name],
                                    component="DependencyAnalyzer"
                                )
                                self._unsupported_encountered.add(kind_name)
                        elif 'Declaration' in kind_name or 'Block' in kind_name:
                            if kind_name not in self._unsupported_encountered:
                                self.warn_handler.warn_unsupported(
                                    kind_name,
                                    context=key,
                                    suggestion="可能影响依赖分析完整性",
                                    component="DependencyAnalyzer"
                                )
                                self._unsupported_encountered.add(kind_name)
                except Exception as e:
                    self.warn_handler.warn_error(
                        "UnsupportedSyntaxCheck",
                        e,
                        context=f"file={key}",
                        component="DependencyAnalyzer"
                    )
    
    def _find_forward_dependencies(self, signal_name: str, module_name: str = None) -> List[str]:
        """找前向依赖 - 驱动这个信号的信号"""
        try:
            from .driver import DriverTracer
        except Exception as e:
            self.warn_handler.warn_error(
                "DriverTracerImport",
                e,
                context="DependencyAnalyzer",
                component="DependencyAnalyzer"
            )
            return []
        
        tracer = DriverTracer(self.parser, verbose=self.verbose)
        drivers = tracer.find_driver(signal_name, module_name)
        
        forward_deps = set()
        
        for driver in drivers:
            for src in driver.sources:
                if src and src != signal_name:
                    forward_deps.add(src)
        
        return list(forward_deps)
    
    def _find_backward_dependencies(self, signal_name: str, module_name: str = None) -> List[str]:
        """找后向依赖 - 这个信号影响的信号（负载）"""
        try:
            from .load import LoadTracer
        except Exception as e:
            self.warn_handler.warn_error(
                "LoadTracerImport",
                e,
                context="DependencyAnalyzer",
                component="DependencyAnalyzer"
            )
            return []
        
        tracer = LoadTracer(self.parser, verbose=self.verbose)
        loads = tracer.find_load(signal_name, module_name)
        
        backward_deps = set()
        
        for load in loads:
            # 从 context 提取信号名
            if hasattr(load, 'context') and load.context:
                # 简化处理：从上下文中提取信号
                pass
        
        return list(backward_deps)
    
    def _find_source_signals(self, signal_name: str, module_name: str = None, 
                            forward_deps: List[str] = None) -> List[str]:
        """找源头信号"""
        if not forward_deps:
            return [signal_name]
        
        source_signals = []
        for dep in forward_deps:
            # 递归找源头
            sub_deps = self._find_forward_dependencies(dep, module_name)
            if not sub_deps:
                source_signals.append(dep)
            else:
                source_signals.extend(self._find_source_signals(dep, module_name, sub_deps))
        
        return list(set(source_signals))
    
    def get_warning_report(self) -> str:
        """获取警告报告"""
        return self.warn_handler.get_report()
    
    def print_warning_report(self):
        """打印警告报告"""
        self.warn_handler.print_report()
