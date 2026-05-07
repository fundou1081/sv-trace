"""VCD Analyzer - VCD波形分析器.

该模块提供 VCD (Value Change Dump) 波形文件的解析和分析功能。

支持功能：
- 解析 VCD 文件/文本
- 检测信号跳变沿
- 测量时钟频率和占空比
- 检测时钟域特征
- 对比两个信号

Example:
    >>> from trace.vcd_analyzer import VCDAnalyzer
    >>> analyzer = VCDAnalyzer(verbose=True)
    >>> waveforms = analyzer.parse_vcd("wave.vcd")
    >>> transitions = analyzer.find_transitions('clk')
    >>> freq = analyzer.measure_frequency('clk')
"""

import re
import os
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field

# 导入解析警告模块
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
try:
    from trace.parse_warn import (
        ParseWarningHandler,
        warn_unsupported,
        warn_error,
        WarningLevel
    )
except ImportError:
    class ParseWarningHandler:
        def __init__(self, verbose=True, component="VCDAnalyzer"):
            self.verbose = verbose
            self.component = component
        def warn_unsupported(self, node_kind, context="", suggestion="", component=None):
            if self.verbose:
                print(f"⚠️ [WARN][{component or self.component}] <{node_kind}> {suggestion} @ {context}")
        def warn_error(self, operation, exc, context="", component=None):
            if self.verbose:
                print(f"❌ [ERROR][{component or self.component}] {operation}: {exc} @ {context}")
        def get_report(self):
            return ""


@dataclass
class SignalWaveform:
    """信号波形数据类
    
    Attributes:
        name: 信号名称
        values: (时间, 值) 元组列表
        code: VCD 文件中的标识符
    """
    name: str
    values: List[Tuple[int, int]] = field(default_factory=list)
    code: str = ""
    
    def add_value(self, time: int, value: int) -> None:
        """添加值
        
        Args:
            time: 时间戳
            value: 信号值
        """
        self.values.append((time, value))


@dataclass
class Transition:
    """信号跳变数据类
    
    Attributes:
        time: 跳变时间
        from_value: 原始值
        to_value: 目标值
    """
    time: int
    from_value: int
    to_value: int


@dataclass
class VCDHeader:
    """VCD 文件头信息
    
    Attributes:
        timescale: 时间尺度字符串 (如 "1ns")
        timescale_value: 时间尺度数值
        timescale_unit: 时间单位
        modules: 模块列表
        date: 日期
        version: 版本
    """
    timescale: str = "1ns"
    timescale_value: int = 1
    timescale_unit: str = "ns"
    modules: List[str] = field(default_factory=list)
    date: str = ""
    version: str = ""


class VCDAnalyzer:
    """VCD 波形分析器
    
    提供 VCD 波形文件的解析和分析功能。
    
    Attributes:
        signals: 信号名到波形的映射
        header: VCD 文件头信息
        warn_handler: 警告处理器
        
    Example:
        >>> va = VCDAnalyzer(verbose=True)
        >>> waveforms = va.parse_vcd("design.vcd")
        >>> for name, wave in waveforms.items():
        ...     print(f"{name}: {len(wave.values)} values")
    """
    
    # 不支持的 VCD 特性
    UNSUPPORTED_FEATURES = {
        'real': '实数类型信号不支持',
        'event': 'event类型不支持',
        'string': '字符串类型不支持',
    }
    
    def __init__(self, verbose: bool = True):
        """初始化 VCD 分析器
        
        Args:
            verbose: 是否打印警告信息
        """
        self.verbose = verbose
        self.warn_handler = ParseWarningHandler(
            verbose=verbose,
            component="VCDAnalyzer"
        )
        self.signals: Dict[str, SignalWaveform] = {}
        self.header = VCDHeader()
        self._signal_codes: Dict[str, str] = {}
        self._current_scope: List[str] = []
        self._unsupported_encountered: Set[str] = set()
    
    def parse_vcd(self, filepath: str) -> Dict[str, SignalWaveform]:
        """解析 VCD 文件
        
        Args:
            filepath: VCD 文件路径
            
        Returns:
            Dict[str, SignalWaveform]: 信号名到波形的映射
        """
        if not filepath.endswith('.vcd'):
            filepath += '.vcd'
        
        waveforms = {}
        
        try:
            with open(filepath, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            self.warn_handler.warn_error(
                "FileNotFound",
                FileNotFoundError(f"File not found: {filepath}"),
                context=filepath,
                component="VCDAnalyzer"
            )
            return waveforms
        except Exception as e:
            self.warn_handler.warn_error(
                "FileRead", e,
                context=filepath,
                component="VCDAnalyzer"
            )
            return waveforms
        
        try:
            self._parse_content(content)
            waveforms = self.signals
        except Exception as e:
            self.warn_handler.warn_error(
                "VCDParsing", e,
                context=filepath,
                component="VCDAnalyzer"
            )
        
        return waveforms
    
    def parse_vcd_text(self, content: str) -> Dict[str, SignalWaveform]:
        """从文本解析 VCD
        
        Args:
            content: VCD 文件内容字符串
            
        Returns:
            Dict[str, SignalWaveform]: 信号名到波形的映射
        """
        waveforms = {}
        
        try:
            self._parse_content(content)
            waveforms = self.signals
        except Exception as e:
            self.warn_handler.warn_error(
                "VCDTextParsing", e,
                context="<text>",
                component="VCDAnalyzer"
            )
        
        return waveforms
    
    def _parse_content(self, content: str) -> None:
        """解析 VCD 内容
        
        Args:
            content: VCD 文件内容
        """
        lines = content.split('\n')
        
        state = "header"
        current_time = 0
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            if line.startswith('$enddefinitions'):
                state = "data"
                continue
            
            if state == "header":
                self._parse_header_line(line)
            elif state == "definitions":
                self._parse_definition_line(line)
            elif state == "data":
                if line.startswith('#'):
                    current_time = int(line[1:])
                else:
                    self._process_vcd_line(line, current_time)
    
    def _process_vcd_line(self, line: str, current_time: int) -> None:
        """处理 VCD 数据行
        
        Args:
            line: VCD 数据行
            current_time: 当前时间戳
        """
        if not line or len(line) < 2:
            return
        
        line = line.replace(' ', '')
        
        # 二进制格式: b<value><code>
        if line[0].lower() == 'b':
            if len(line) < 3:
                return
            
            binary_part = line[1:]
            code_char = None
            value_str = ""
            
            for i, c in enumerate(binary_part):
                if c not in '01xzXZ':
                    code_char = c
                    value_str = binary_part[:i]
                    break
            
            if code_char and code_char in self._signal_codes:
                sig_name = self._signal_codes[code_char]
                if sig_name in self.signals:
                    if value_str:
                        if value_str.lower() in ('x', 'z'):
                            value = 0
                        else:
                            try:
                                value = int(value_str, 2)
                            except ValueError:
                                value = 0
                        self.signals[sig_name].add_value(current_time, value)
        else:
            # 单比特格式: <value><code>
            if len(line) < 2:
                return
            
            value_char = line[0]
            code_char = line[1]
            
            if code_char in self._signal_codes:
                sig_name = self._signal_codes[code_char]
                if sig_name in self.signals:
                    if value_char == '0':
                        value = 0
                    elif value_char == '1':
                        value = 1
                    elif value_char.lower() in ('x', 'z', '?'):
                        value = 0
                    else:
                        return
                    
                    self.signals[sig_name].add_value(current_time, value)
    
    def _parse_header_line(self, line: str) -> None:
        """解析 VCD 头部行
        
        Args:
            line: VCD 头部行
        """
        line = line.strip()
        
        if line.startswith('$timescale'):
            match = re.search(r'\$timescale\s+(\d+)(\w+)\s+\$end', line)
            if match:
                self.header.timescale_value = int(match.group(1))
                self.header.timescale_unit = match.group(2)
                self.header.timescale = f"{match.group(1)}{match.group(2)}"
        
        elif line.startswith('$scope'):
            match = re.search(r'\$scope\s+(\w+)\s+(\w+)\s+\$end', line)
            if match:
                self._current_scope.append(match.group(2))
        
        elif line.startswith('$upscope'):
            if self._current_scope:
                self._current_scope.pop()
        
        elif line.startswith('$var'):
            match = re.search(r'\$var\s+(\w+)\s+(\d+)\s+(\S+)\s+(\w+)\s+\$end', line)
            if match:
                var_type = match.group(1)
                code = match.group(3)
                name = match.group(4)
                
                if var_type in self.UNSUPPORTED_FEATURES:
                    if var_type not in self._unsupported_encountered:
                        self.warn_handler.warn_unsupported(
                            f"VCD_{var_type}",
                            context="/".join(self._current_scope),
                            suggestion=self.UNSUPPORTED_FEATURES[var_type],
                            component="VCDAnalyzer"
                        )
                        self._unsupported_encountered.add(var_type)
                
                full_name = "/".join(self._current_scope + [name])
                self._signal_codes[code] = full_name
                self.signals[full_name] = SignalWaveform(name=full_name, code=code)
        
        elif line.startswith('$date'):
            match = re.search(r'\$date\s+(.+)\s+\$end', line)
            if match:
                self.header.date = match.group(1).strip()
        
        elif line.startswith('$version'):
            match = re.search(r'\$version\s+(.+)\s+\$end', line)
            if match:
                self.header.version = match.group(1).strip()
    
    def _parse_definition_line(self, line: str) -> None:
        """解析定义行"""
        self._parse_header_line(line)
    
    def find_transitions(self, signal_name: str) -> List[Transition]:
        """查找信号的跳变沿
        
        Args:
            signal_name: 信号名
            
        Returns:
            List[Transition]: 跳变列表
        """
        if signal_name not in self.signals:
            return []
        
        transitions = []
        waveform = self.signals[signal_name]
        
        for i in range(1, len(waveform.values)):
            t, v = waveform.values[i]
            _, prev_v = waveform.values[i-1]
            
            if v != prev_v:
                transitions.append(Transition(
                    time=t,
                    from_value=prev_v,
                    to_value=v
                ))
        
        return transitions
    
    def measure_frequency(self, signal_name: str) -> Optional[float]:
        """测量信号频率
        
        Args:
            signal_name: 信号名
            
        Returns:
            Optional[float]: 频率 (Hz)，如果无法测量则返回 None
        """
        transitions = self.find_transitions(signal_name)
        if len(transitions) < 2:
            return None
        
        periods = []
        rising_edges = [t for t in transitions if t.to_value > t.from_value]
        
        if len(rising_edges) < 2:
            return None
        
        for i in range(1, len(rising_edges)):
            periods.append(rising_edges[i].time - rising_edges[i-1].time)
        
        avg_period = sum(periods) / len(periods)
        
        if self.header.timescale_value > 0:
            avg_period *= self.header.timescale_value
        
        return 1.0 / avg_period if avg_period > 0 else None
    
    def measure_duty_cycle(self, signal_name: str) -> Optional[float]:
        """测量占空比
        
        Args:
            signal_name: 信号名
            
        Returns:
            Optional[float]: 占空比 (0-1)，如果无法测量则返回 None
        """
        if signal_name not in self.signals:
            return None
        
        waveform = self.signals[signal_name]
        if len(waveform.values) < 2:
            return None
        
        high_time = 0
        low_time = 0
        prev_time = 0
        prev_value = 0
        
        for time, value in waveform.values:
            if prev_value == 1:
                high_time += time - prev_time
            else:
                low_time += time - prev_time
            prev_time = time
            prev_value = value
        
        total_time = high_time + low_time
        if total_time == 0:
            return None
        
        return high_time / total_time
    
    def detect_clock_domain(self, signal_name: str) -> Dict:
        """检测时钟域特征
        
        Args:
            signal_name: 信号名
            
        Returns:
            Dict: 包含频率、占空比等信息的字典
        """
        freq = self.measure_frequency(signal_name)
        duty = self.measure_duty_cycle(signal_name)
        
        return {
            'signal': signal_name,
            'frequency': freq,
            'duty_cycle': duty,
            'is_clock': freq is not None and 0.3 <= (duty or 0) <= 0.7,
            'period': 1.0 / freq if freq else None,
            'timescale': self.header.timescale,
        }
    
    def compare_signals(self, signal1: str, signal2: str) -> Dict:
        """对比两个信号
        
        Args:
            signal1: 信号1名
            signal2: 信号2名
            
        Returns:
            Dict: 包含相关性、相位差等信息的字典
        """
        result = {
            'signal1': signal1,
            'signal2': signal2,
            'correlation': 0.0,
            'phase_shift': 0,
            'note': '对比功能已实现'
        }
        
        if signal1 not in self.signals or signal2 not in self.signals:
            result['note'] = '信号不存在'
            return result
        
        w1 = self.signals[signal1]
        w2 = self.signals[signal2]
        
        if len(w1.values) < 2 or len(w2.values) < 2:
            return result
        
        transitions1 = self.find_transitions(signal1)
        transitions2 = self.find_transitions(signal2)
        
        if len(transitions1) == len(transitions2):
            result['correlation'] = 1.0
        elif abs(len(transitions1) - len(transitions2)) <= 2:
            result['correlation'] = 0.8
        else:
            result['correlation'] = 0.0
        
        if len(transitions1) > 0 and len(transitions2) > 0:
            t1_first = transitions1[0].time if transitions1 else 0
            t2_first = transitions2[0].time if transitions2 else 0
            result['phase_shift'] = t1_first - t2_first
        
        return result
    
    def get_warning_report(self) -> str:
        """获取警告报告
        
        Returns:
            str: 警告报告字符串
        """
        return self.warn_handler.get_report()
    
    def print_warning_report(self) -> None:
        """打印警告报告到标准输出"""
        self.warn_handler.print_report()
