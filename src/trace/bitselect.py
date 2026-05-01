"""
位选信号分析 - Bit Selection Analysis
支持追踪信号的部分选择 (signal[3:0], signal[idx], signal[msb:lsb])

增强版: 添加解析警告，显式打印不支持的语法结构
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
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
class BitSelect:
    """位选信息"""
    signal_name: str
    select_expr: str = ""
    msb: Optional[int] = None
    lsb: Optional[int] = None
    is_single_bit: bool = False
    is_range: bool = False
    is_index: bool = False
    
    def __str__(self):
        if self.is_single_bit:
            return f"{self.signal_name}[{self.msb}]"
        elif self.is_range:
            return f"{self.signal_name}[{self.msb}:{self.lsb}]"
        elif self.is_index:
            return f"{self.signal_name}[{self.select_expr}]"
        return self.signal_name
    
    def get_width(self) -> int:
        if self.is_single_bit:
            return 1
        elif self.is_range and self.msb is not None and self.lsb is not None:
            return self.msb - self.lsb + 1
        return 0


class BitSelectExtractor:
    """位选提取器
    
    增强: 添加解析警告
    """
    
    def __init__(self, parser, verbose: bool = True):
        self.parser = parser
        self.verbose = verbose
        # 创建警告处理器
        self.warn_handler = ParseWarningHandler(
            verbose=verbose,
            component="BitSelectExtractor"
        )
    
    def extract(self, expr: str) -> List[BitSelect]:
        if not expr:
            return []
        
        results = []
        pattern = r'(\w+)\[([^\]]+)\]'
        
        try:
            for match in re.finditer(pattern, expr):
                signal_name = match.group(1)
                select_expr = match.group(2)
                
                bit_select = self._parse_select(signal_name, select_expr)
                if bit_select:
                    results.append(bit_select)
        except Exception as e:
            self.warn_handler.warn_error(
                "BitSelectExtraction",
                e,
                context=f"expr={expr[:50]}",
                component="BitSelectExtractor"
            )
        
        return results
    
    def _parse_select(self, signal_name: str, select_expr: str) -> Optional[BitSelect]:
        result = BitSelect(signal_name=signal_name, select_expr=select_expr)
        select_expr = select_expr.strip()
        
        try:
            # 单bit [3]
            if re.match(r'^\d+$', select_expr):
                result.is_single_bit = True
                result.msb = int(select_expr)
                result.lsb = int(select_expr)
                return result
            
            # 范围 [3:0]
            if ':' in select_expr:
                parts = select_expr.split(':')
                if len(parts) == 2:
                    msb_str = parts[0].strip()
                    lsb_str = parts[1].strip()
                    
                    if msb_str.isdigit() and lsb_str.isdigit():
                        result.is_range = True
                        result.is_single_bit = (msb_str == lsb_str)
                        result.msb = int(msb_str)
                        result.lsb = int(lsb_str)
                        return result
            
            # 变量索引
            result.is_index = True
            return result
        except Exception as e:
            self.warn_handler.warn_error(
                "SelectParsing",
                e,
                context=f"signal={signal_name}, expr={select_expr}",
                component="BitSelectExtractor"
            )
            return result
    
    def match_signal(self, expr: str, target_base: str) -> bool:
        if not expr:
            return False
        
        if target_base in expr:
            return True
        
        bit_selects = self.extract(expr)
        for bs in bit_selects:
            if bs.signal_name == target_base:
                return True
        
        return False
    
    def get_base_signal(self, name_with_select: str) -> Tuple[str, Optional[BitSelect]]:
        match = re.match(r'^(\w+)(?:\[([^\]]+)\])?$', name_with_select)
        if not match:
            return name_with_select, None
        
        base = match.group(1)
        select_expr = match.group(2)
        
        if select_expr:
            bit_select = self._parse_select(base, select_expr)
            return base, bit_select
        
        return base, None


class BitSelectTracer:
    """位选追踪器
    
    增强: 添加解析警告
    """
    
    def __init__(self, parser, verbose: bool = True):
        self.parser = parser
        self.verbose = verbose
        # 创建警告处理器
        self.warn_handler = ParseWarningHandler(
            verbose=verbose,
            component="BitSelectTracer"
        )
        self.driver_tracer = None
        self.load_tracer = None
        self.extractor = BitSelectExtractor(parser, verbose=verbose)
    
    def _get_driver_tracer(self):
        if not self.driver_tracer:
            try:
                from .driver import DriverTracer
                self.driver_tracer = DriverTracer(self.parser, verbose=self.verbose)
            except Exception as e:
                self.warn_handler.warn_error(
                    "DriverTracerInit",
                    e,
                    context="BitSelectTracer",
                    component="BitSelectTracer"
                )
        return self.driver_tracer
    
    def _get_load_tracer(self):
        if not self.load_tracer:
            try:
                from .load import LoadTracer
                self.load_tracer = LoadTracer(self.parser, verbose=self.verbose)
            except Exception as e:
                self.warn_handler.warn_error(
                    "LoadTracerInit",
                    e,
                    context="BitSelectTracer",
                    component="BitSelectTracer"
                )
        return self.load_tracer
    
    def find_bit_drivers(self, signal_name: str) -> List[Tuple[str, BitSelect]]:
        """查找信号的位选驱动"""
        tracer = self._get_driver_tracer()
        if not tracer:
            return []
        
        try:
            drivers = tracer.find_driver(signal_name, include_bit_select=True)
        except Exception as e:
            self.warn_handler.warn_error(
                "BitDriverSearch",
                e,
                context=f"signal={signal_name}",
                component="BitSelectTracer"
            )
            return []
        
        results = []
        for d in drivers:
            # 检查是否是位选形式
            if '[' in d.signal:
                # 从信号名提取位选
                base, bs = self.extractor.get_base_signal(d.signal)
                if bs:
                    results.append((d.source_expr, bs))
        
        return results
    
    def find_bit_loads(self, signal_name: str) -> List[Tuple[str, BitSelect]]:
        """查找信号的位选负载"""
        tracer = self._get_load_tracer()
        if not tracer:
            return []
        
        try:
            loads = tracer.find_load(signal_name)
        except Exception as e:
            self.warn_handler.warn_error(
                "BitLoadSearch",
                e,
                context=f"signal={signal_name}",
                component="BitSelectTracer"
            )
            return []
        
        results = []
        for l in loads:
            bit_selects = self.extractor.extract(l.context)
            for bs in bit_selects:
                results.append((l.context, bs))
        
        return results
    
    def trace_signal_with_bitselect(self, signal_name: str) -> dict:
        """追踪信号及其位选"""
        drivers = self.find_bit_drivers(signal_name)
        loads = self.find_bit_loads(signal_name)
        
        partial_drivers = [(expr, bs) for expr, bs in drivers if bs.is_range or bs.is_index]
        partial_loads = [(expr, bs) for expr, bs in loads if bs.is_range or bs.is_index]
        
        return {
            "signal": signal_name,
            "full_drivers": len(drivers) - len(partial_drivers),
            "partial_drivers": len(partial_drivers),
            "partial_driver_details": partial_drivers,
            "full_loads": len(loads) - len(partial_loads),
            "partial_loads": len(partial_loads),
            "partial_load_details": partial_loads,
            "has_bit_selection": len(partial_drivers) > 0 or len(partial_loads) > 0,
        }
    
    def get_driven_bits(self, signal_name: str) -> List[int]:
        """获取信号被驱动的所有位"""
        drivers = self.find_bit_drivers(signal_name)
        
        driven_bits = set()
        
        for expr, bs in drivers:
            if bs.is_single_bit and bs.msb is not None:
                driven_bits.add(bs.msb)
            elif bs.is_range and bs.msb is not None and bs.lsb is not None:
                for b in range(bs.lsb, bs.msb + 1):
                    driven_bits.add(b)
        
        return sorted(list(driven_bits))
    
    def get_warning_report(self) -> str:
        """获取警告报告"""
        return self.warn_handler.get_report()
    
    def print_warning_report(self):
        """打印警告报告"""
        self.warn_handler.print_report()
