"""Load Tracer - 追踪信号加载点.

该模块分析信号在哪里被读取/使用（作为负载）。

功能：
- 查找信号被加载的位置
- 识别时钟事件、条件判断等使用场景

Example:
    >>> from trace.load import LoadTracer
    >>> lt = LoadTracer(parser)
    >>> loads = lt.find_load('data_in')
"""

import pyslang
from pyslang import SyntaxKind
from typing import List, Set, Dict
import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.models import Load

# 导入解析警告模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from trace.parse_warn import (
    ParseWarningHandler,
    warn_unsupported,
    warn_error,
    WarningLevel
)


class LoadTracer:
    """信号加载点追踪器
    
    追踪信号在表达式中被读取的位置，包括：
    - 时钟事件 @(posedge signal)
    - 条件判断 if (signal)
    - 赋值右侧 data_out = signal
    - case 匹配 case (signal)
    
    Attributes:
        warn_handler: 警告处理器
        
    Example:
        >>> lt = LoadTracer(parser, verbose=True)
        >>> loads = lt.find_load('clk')
        >>> for load in loads:
        ...     print(f"Line {load.line}: {load.context}")
    """
    
    # 不支持的语法类型
    UNSUPPORTED_TYPES = {
        'CovergroupDeclaration': 'covergroup不影响信号负载分析',
        'PropertyDeclaration': 'property声明无信号负载',
        'SequenceDeclaration': 'sequence声明无信号负载',
        'ClassDeclaration': 'class内部信号负载分析可能不完整',
        'InterfaceDeclaration': 'interface内部信号负载分析可能不完整',
        'PackageDeclaration': 'package无信号负载',
        'ProgramDeclaration': 'program块信号负载分析可能不完整',
        'ClockingBlock': 'clocking block信号负载分析有限',
    }
    
    def __init__(self, parser, verbose: bool = True):
        """初始化负载追踪器
        
        Args:
            parser: SVParser 实例
            verbose: 是否打印警告信息
        """
        self.parser = parser
        self.verbose = verbose
        self.warn_handler = ParseWarningHandler(
            verbose=verbose,
            component="LoadTracer"
        )
        self.compilation = parser.compilation if hasattr(parser, 'compilation') else None
        self._loads: List[Load] = []
        self._target_signal = ""
        self._current_module = ""
        self._unsupported_encountered: Set[str] = set()
        self._impl = None
    
    @staticmethod
    def extract_from_text(source: str, verbose: bool = True):
        """从源码文本提取负载
        
        Args:
            source: SystemVerilog 源码
            verbose: 是否打印警告
            
        Returns:
            LoadTracer 或 None
        """
        import pyslang
        
        try:
            tree = pyslang.SyntaxTree.fromText(source)
            
            class TextParser:
                def __init__(self, tree):
                    self.trees = {"input.sv": tree}
                    self.compilation = tree
            
            return LoadTracer(TextParser(tree), verbose=verbose)
        except Exception as e:
            print(f"Load extract error: {e}")
            return None

    def find_load(self, signal_name: str, module_name: str = None) -> List[Load]:
        """查找信号被加载的位置
        
        Args:
            signal_name: 信号名
            module_name: 模块名（可选）
            
        Returns:
            List[Load]: 负载列表
        """
        impl = _LoadTracerRegexImpl(self.parser, self.verbose, self.warn_handler)
        return impl.find_load(signal_name, module_name)
    
    def get_all_signals(self) -> Set[str]:
        """获取所有信号
        
        Returns:
            Set[str]: 信号名集合
        """
        impl = _LoadTracerRegexImpl(self.parser, self.verbose, self.warn_handler)
        return impl.get_all_signals()
    
    def get_warning_report(self) -> str:
        """获取警告报告"""
        return self.warn_handler.get_report()
    
    def print_warning_report(self) -> None:
        """打印警告报告"""
        self.warn_handler.print_report()


class _LoadTracerRegexImpl:
    """基于正则表达式的信号负载追踪器（内部实现）"""
    
    def __init__(self, parser, verbose: bool = True, 
                 warn_handler: ParseWarningHandler = None):
        """初始化
        
        Args:
            parser: SVParser 实例
            verbose: 是否打印警告
            warn_handler: 警告处理器
        """
        self.parser = parser
        self.verbose = verbose
        self.warn_handler = warn_handler or ParseWarningHandler(
            verbose=verbose, 
            component="LoadTracer"
        )
        self._code_cache: Dict[str, str] = {}
    
    def _get_code(self, filepath: str) -> str:
        """获取源码"""
        if filepath in self._code_cache:
            return self._code_cache[filepath]
        
        from parse import get_source_safe
        code = get_source_safe(self.parser, filepath)
        if code:
            self._code_cache[filepath] = code
            return code
        
        return ""
    
    def _check_unsupported_syntax(self, tree, source: str = "") -> None:
        """检查不支持的语法"""
        if not tree or not hasattr(tree, 'root'):
            return
        
        root = tree.root
        if hasattr(root, 'members') and root.members:
            try:
                members = list(root.members) if hasattr(root.members, '__iter__') else [root.members]
                for member in members:
                    if member is None:
                        continue
                    kind_name = str(member.kind) if hasattr(member, 'kind') else type(member).__name__
                    
                    if kind_name in LoadTracer.UNSUPPORTED_TYPES:
                        if kind_name not in self.warn_handler._seen_kinds:
                            self.warn_handler.warn_unsupported(
                                kind_name,
                                context=source,
                                suggestion=LoadTracer.UNSUPPORTED_TYPES[kind_name],
                                component="LoadTracer"
                            )
                            self.warn_handler._seen_kinds.add(kind_name)
            except Exception as e:
                self.warn_handler.warn_error(
                    "UnsupportedSyntaxCheck", e,
                    context=f"file={source}",
                    component="LoadTracer"
                )
    
    def _find_in_file(self, filepath: str, signal: str) -> List[Load]:
        """在单个文件中查找信号使用"""
        loads = []
        code = self._get_code(filepath)
        if not code:
            return loads
        
        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            try:
                stripped = line.strip()
                
                # 跳过注释
                if not stripped or stripped.startswith('//') or stripped.startswith('/*'):
                    continue
                
                # 时钟/复位事件
                if re.search(rf'@\s*\([^)]*\b{signal}\b', stripped):
                    loads.append(Load(
                        signal_name=signal,
                        context=stripped[:100],
                        line=line_num,
                        condition="clock_event"
                    ))
                
                # 条件判断
                if re.search(rf'\b(?:if|else\s+if)\s*\([^)]*\b{signal}\b[^)]*\)', stripped):
                    loads.append(Load(
                        signal_name=signal,
                        context=stripped[:100],
                        line=line_num,
                        condition=signal
                    ))
                
                # always块内的赋值 (load)
                if re.search(rf'\b{signal}\b\s*[=<]', stripped):
                    if not stripped.startswith('assign'):
                        loads.append(Load(
                            signal_name=signal,
                            context=stripped[:100],
                            line=line_num,
                            condition="assignment"
                        ))
                
                # case项
                if re.search(rf'\bcase[zx]?\b.*\b{signal}\b', stripped):
                    loads.append(Load(
                        signal_name=signal,
                        context=stripped[:100],
                        line=line_num,
                        condition="case_match"
                    ))
                
                # 三元表达式
                if re.search(rf'\?[^:]*\b{signal}\b.*:', stripped):
                    loads.append(Load(
                        signal_name=signal,
                        context=stripped[:100],
                        line=line_num,
                        condition="ternary"
                    ))
                        
            except Exception as e:
                self.warn_handler.warn_error(
                    "SignalLoadSearch", e,
                    context=f"file={filepath}, line={line_num}",
                    component="LoadTracer"
                )
        
        return loads
    
    def find_load(self, signal_name: str, module_name: str = None) -> List[Load]:
        """查找信号被加载的位置
        
        Args:
            signal_name: 信号名
            module_name: 模块名（可选）
            
        Returns:
            List[Load]: 负载列表
        """
        self._loads = []
        self._target_signal = signal_name
        
        for key, tree in self.parser.trees.items():
            if not key:
                continue
            
            self._check_unsupported_syntax(tree, key)
            self._loads.extend(self._find_in_file(key, signal_name))
        
        return self._loads
    
    def get_all_signals(self) -> Set[str]:
        """获取所有信号
        
        Returns:
            Set[str]: 信号名集合
        """
        signals = set()
        
        for key in self.parser.trees.keys():
            code = self._get_code(key)
            if not code:
                continue
            
            try:
                patterns = [
                    r'\b(logic|reg|wire|bit)\b[^\n;]*\b([a-zA-Z_][a-zA-Z0-9_]*)\b',
                    r'\binput\b[^\n;]*\b([a-zA-Z_][a-zA-Z0-9_]*)\b',
                    r'\boutput\b[^\n;]*\b([a-zA-Z_][a-zA-Z0-9_]*)\b',
                ]
                
                for pattern in patterns:
                    for match in re.finditer(pattern, code, re.IGNORECASE):
                        sig = match.group(1)
                        if sig and not sig.startswith('_'):
                            signals.add(sig)
            except Exception as e:
                self.warn_handler.warn_error(
                    "SignalExtraction", e,
                    context=f"file={key}",
                    component="LoadTracer"
                )
        
        return signals


# 向后兼容别名
class LoadTracerRegex(_LoadTracerRegexImpl):
    """向后兼容的别名"""
    
    def __init__(self, parser, verbose: bool = True):
        super().__init__(parser, verbose)
