"""
Load Tracer - 追踪信号加载点
合并版本: LoadTracer 使用 LoadTracerRegex 内部实现
"""
import pyslang
from pyslang import SyntaxKind
from typing import List, Set, Dict
import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.models import Load


class LoadTracer:
    """
    信号加载点追踪器 (合并版本)
    内部使用 LoadTracerRegex 实现
    """
    
    def __init__(self, parser):
        self.parser = parser
        self.compilation = parser.compilation
        self._loads: List[Load] = []
        self._target_signal = ""
        self._current_module = ""
        
        # 使用正则表达式实现
        self._impl = None
    
    def find_load(self, signal_name: str, module_name: str = None) -> List[Load]:
        """查找信号被加载的位置"""
        # 使用正则表达式实现
        impl = _LoadTracerRegexImpl(self.parser)
        return impl.find_load(signal_name, module_name)
    
    def get_all_signals(self) -> Set[str]:
        """获取所有信号"""
        impl = _LoadTracerRegexImpl(self.parser)
        return impl.get_all_signals()


class _LoadTracerRegexImpl:
    """
    基于正则表达式的信号负载追踪器
    内部使用,不直接暴露
    """
    
    def __init__(self, parser):
        self.parser = parser
        self._code_cache: Dict[str, str] = {}
    
    def _get_code(self, filepath: str) -> str:
        """获取源码"""
        if filepath in self._code_cache:
            return self._code_cache[filepath]
        
        # 使用统一的get_source_safe方法
        from parse import get_source_safe
        code = get_source_safe(self.parser, filepath)
        if code:
            self._code_cache[filepath] = code
            return code
        
        return ""
    
    def _find_in_file(self, filepath: str, signal: str) -> List[Load]:
        """在单个文件中查找信号使用"""
        loads = []
        code = self._get_code(filepath)
        if not code:
            return loads
        
        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # 跳过注释
            if not stripped or stripped.startswith('//') or stripped.startswith('/*'):
                continue
            
            # 1. 时钟/复位事件 @(posedge signal) 或 @(negedge signal)
            if re.search(rf'@\s*\([^)]*\b{signal}\b', stripped):
                loads.append(Load(
                    signal_name=signal,
                    context=stripped[:100],
                    line=line_num,
                    condition="clock_event"
                ))
            
            # 2. 条件判断 if/else if
            if re.search(rf'\b(?:if|else\s+if)\s*\([^)]*\b{signal}\b[^)]*\)', stripped):
                loads.append(Load(
                    signal_name=signal,
                    context=stripped[:100],
                    line=line_num,
                    condition=signal
                ))
            
            # 3. always块内的赋值 (load)
            if re.search(rf'\b{signal}\b\s*[=<]', stripped):
                if not stripped.startswith('assign'):
                    loads.append(Load(
                        signal_name=signal,
                        context=stripped[:100],
                        line=line_num,
                        condition="assignment"
                    ))
            
            # 4. case项
            if re.search(rf'\bcase[zx]?\b.*\b{signal}\b', stripped):
                loads.append(Load(
                    signal_name=signal,
                    context=stripped[:100],
                    line=line_num,
                    condition="case_match"
                ))
            
            # 5. 三元表达式
            if re.search(rf'\?[^:]*\b{signal}\b.*:', stripped):
                loads.append(Load(
                    signal_name=signal,
                    context=stripped[:100],
                    line=line_num,
                    condition="ternary"
                ))
        
        return loads
    
    def find_load(self, signal_name: str, module_name: str = None) -> List[Load]:
        """查找信号被加载的位置"""
        self._loads = []
        self._target_signal = signal_name
        
        for key, tree in self.parser.trees.items():
            if not key:
                continue
            self._loads.extend(self._find_in_file(key, signal_name))
        
        return self._loads
    
    def get_all_signals(self) -> Set[str]:
        """获取所有信号"""
        signals = set()
        
        for key in self.parser.trees.keys():
            code = self._get_code(key)
            if not code:
                continue
            
            # 匹配信号声明
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
        
        return signals


# 保持向后兼容 - LoadTracerRegex 作为别名
class LoadTracerRegex(_LoadTracerRegexImpl):
    """保持向后兼容的别名"""
    
    def __init__(self, parser):
        super().__init__(parser)
