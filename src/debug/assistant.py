"""
DebugAssistant - AI 辅助调试入口
"""
import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class QueryIntent(Enum):
    """查询意图枚举"""
    SIGNAL_DRIVERS = "signal_drivers"      # 找驱动
    SIGNAL_LOADS = "signal_loads"          # 找负载
    DATA_FLOW = "data_flow"                # 数据流
    CONTROL_FLOW = "control_flow"          # 控制流
    CROSS_MODULE = "cross_module"          # 跨模块
    DIAGNOSE = "diagnose"                  # 诊断问题
    FULL_CHECK = "full_check"              # 全面检查
    CLOCK_DOMAIN = "clock_domain"          # 时钟域
    UNKNOWN = "unknown"


@dataclass
class QueryResult:
    """查询结果"""
    intent: QueryIntent
    signal: str = ""
    module: str = ""
    content: str = ""
    details: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class DebugAssistant:
    """AI 辅助调试助手"""
    
    def __init__(self, parser):
        self.parser = parser
        
        # 初始化现有工具
        from trace.driver import DriverTracer
        from trace.load import LoadTracer
        from trace.dataflow import DataFlowTracer
        from trace.controlflow import ControlFlowTracer
        from trace.connection import ConnectionTracer
        from trace.datapath import DataPathAnalyzer
        from query.hierarchy import HierarchicalResolver
        
        self.tracers = {
            'driver': DriverTracer(parser),
            'load': LoadTracer(parser),
            'dataflow': DataFlowTracer(parser),
            'controlflow': ControlFlowTracer(parser),
            'connection': ConnectionTracer(parser),
            'datapath': DataPathAnalyzer(parser),
            'hierarchy': HierarchicalResolver(parser),
        }
        
        # 初始化分析器
        from debug.analyzers import XValueDetector, MultiDriverDetector, UninitializedDetector
        self.analyzers = {
            'xvalue': XValueDetector(parser),
            'multi_driver': MultiDriverDetector(parser),
            'uninitialized': UninitializedDetector(parser),
        }
    
    def ask(self, question: str) -> QueryResult:
        """主入口: 处理自然语言查询"""
        # 1. 解析意图
        intent, signal, module = self._parse_question(question)
        
        # 2. 根据意图调用对应工具
        if intent == QueryIntent.SIGNAL_DRIVERS:
            return self._handle_signal_drivers(signal, module)
        elif intent == QueryIntent.SIGNAL_LOADS:
            return self._handle_signal_loads(signal, module)
        elif intent == QueryIntent.DATA_FLOW:
            return self._handle_data_flow(signal, module)
        elif intent == QueryIntent.CONTROL_FLOW:
            return self._handle_control_flow(signal, module)
        elif intent == QueryIntent.CROSS_MODULE:
            return self._handle_cross_module(signal, module)
        elif intent == QueryIntent.DIAGNOSE:
            return self._handle_diagnose(signal, module)
        elif intent == QueryIntent.FULL_CHECK:
            return self._handle_full_check(signal, module)
        elif intent == QueryIntent.CLOCK_DOMAIN:
            return self._handle_clock_domain(signal, module)
        else:
            return QueryResult(
                intent=QueryIntent.UNKNOWN,
                content="Could not understand. Try: 'Find drivers for X', 'Show data flow of Y'"
            )
    
    def _parse_question(self, question: str) -> Tuple[QueryIntent, str, str]:
        """解析问题，提取意图、信号名、模块名"""
        q = question.lower().strip()
        
        # 意图识别 - 优先识别意图
        if any(kw in q for kw in ['driver', 'who drives', 'what drives', 'drive']):
            intent = QueryIntent.SIGNAL_DRIVERS
        elif any(kw in q for kw in ['load', 'who uses', 'what uses', 'used by']):
            intent = QueryIntent.SIGNAL_LOADS
        elif any(kw in q for kw in ['data flow', 'trace', 'flow from', 'flow to']):
            intent = QueryIntent.DATA_FLOW
        elif any(kw in q for kw in ['control', 'condition', 'depends on']):
            intent = QueryIntent.CONTROL_FLOW
        elif any(kw in q for kw in ['cross', 'hierarchy', 'top.', 'module.']):
            intent = QueryIntent.CROSS_MODULE
        elif any(kw in q for kw in ['diagnose', 'why', 'x value', 'unknown', 'problem', 'issue']):
            intent = QueryIntent.DIAGNOSE
        elif any(kw in q for kw in ['check', 'full', 'all', 'common issues']):
            intent = QueryIntent.FULL_CHECK
        elif any(kw in q for kw in ['clock', 'domain', 'timing']):
            intent = QueryIntent.CLOCK_DOMAIN
        else:
            intent = QueryIntent.UNKNOWN
        
        # 提取信号名 - 在整个问题中查找
        # 支持: "for signal X", "of X", "X" (直接信号名)
        signal = ""
        
        # 清理问题文本，去除标点
        q_clean = re.sub(r"[?!.,;:']", "", q)
        
        # 模式1: "for result", "of temp"
        signal_match = re.search(r'(?:for|of|to)\s+(\w+)', q_clean)
        if signal_match:
            signal = signal_match.group(1)
        
        # 模式2: 直接信号名 (最后一个词，如果前面有特定动词)
        if not signal:
            if intent in [QueryIntent.SIGNAL_DRIVERS, QueryIntent.SIGNAL_LOADS]:
                # "Find drivers result" -> 取最后一个词
                words = q.split()
                if len(words) >= 2:
                    signal = words[-1]
        
        # 模式3: "trace from A to B" -> 取 A 或 B
        if not signal:
            from_to = re.search(r'(?:from|to)\s+(\w+)', q)
            if from_to:
                signal = from_to.group(1)
        
        # 模式4: 直接是信号名 (如 "diagnose temp")
        if not signal:
            words = q_clean.split()
            for w in reversed(words):
                # 跳过常见关键词
                if w not in ['diagnose', 'check', 'why', 'is', 'the', 'a', 'an', 'who', 'what', 'find']:
                    signal = w
                    break
        
        # 提取模块名
        module_match = re.search(r'(?:in|module)\s+(\w+)', q)
        module = module_match.group(1) if module_match else ""
        
        # 特殊处理: 去除信号名中的常见后缀
        if signal:
            signal = signal.rstrip('?!')
            # 常见查询词转信号名
            if signal in ['issues', 'problem', 'module', 'this']:
                signal = ""
        
        return intent, signal, module
    
    def _handle_signal_drivers(self, signal: str, module: str) -> QueryResult:
        """处理驱动查询"""
        if not signal:
            return QueryResult(intent=QueryIntent.SIGNAL_DRIVERS, content="Please specify a signal name.")
        
        drivers = self.tracers['driver'].find_driver(signal)
        
        if not drivers:
            return QueryResult(intent=QueryIntent.SIGNAL_DRIVERS, signal=signal, 
                             content=f"No drivers found for '{signal}'")
        
        content = f"Found {len(drivers)} driver(s) for '{signal}':"
        details = []
        
        for i, d in enumerate(drivers, 1):
            kind_name = d.driver_kind.name
            expr = d.source_expr.strip()[:50] if d.source_expr else "N/A"
            details.append(f"  {i}. [{kind_name}] {expr}")
        
        return QueryResult(intent=QueryIntent.SIGNAL_DRIVERS, signal=signal, content=content, details=details)
    
    def _handle_signal_loads(self, signal: str, module: str) -> QueryResult:
        """处理负载查询"""
        if not signal:
            return QueryResult(intent=QueryIntent.SIGNAL_LOADS, content="Please specify a signal name.")
        
        loads = self.tracers['load'].find_load(signal)
        
        if not loads:
            return QueryResult(intent=QueryIntent.SIGNAL_LOADS, signal=signal, content=f"No loads found for '{signal}'")
        
        content = f"Found {len(loads)} load(s) for '{signal}':"
        details = [f"  {i+1}. {l.signal_name}" for i, l in enumerate(loads)]
        
        return QueryResult(intent=QueryIntent.SIGNAL_LOADS, signal=signal, content=content, details=details)
    
    def _handle_data_flow(self, signal: str, module: str) -> QueryResult:
        """处理数据流查询"""
        if not signal:
            return QueryResult(intent=QueryIntent.DATA_FLOW, content="Please specify a signal.")
        
        flow = self.tracers['dataflow'].find_flow(signal)
        
        if not flow.drivers:
            return QueryResult(intent=QueryIntent.DATA_FLOW, signal=signal, content=f"No data flow for '{signal}'")
        
        content = f"[Data Flow] {signal} - {len(flow.drivers)} drivers"
        details = []
        for d in flow.drivers:
            expr = d.source_expr.strip()[:40] if d.source_expr else "N/A"
            details.append(f"  - {d.driver_kind.name}: {expr}")
        
        return QueryResult(intent=QueryIntent.DATA_FLOW, signal=signal, content=content, details=details)
    
    def _handle_control_flow(self, signal: str, module: str) -> QueryResult:
        """处理控制流查询"""
        if not signal:
            return QueryResult(intent=QueryIntent.CONTROL_FLOW, content="Please specify a signal.")
        
        cf_tracer = self.tracers['controlflow']
        cf_deps = cf_tracer.find_control_dependencies(signal)
        
        content = f"[Control Dependencies] {signal}"
        
        if hasattr(cf_deps, 'dependencies') and cf_deps.dependencies:
            details = [f"  Depends on: {d}" for d in cf_deps.dependencies[:5]]
        else:
            details = ["  No explicit control dependencies found"]
        
        return QueryResult(intent=QueryIntent.CONTROL_FLOW, signal=signal, content=content, details=details)
    
    def _handle_cross_module(self, signal: str, module: str) -> QueryResult:
        """处理跨模块追踪"""
        if not signal:
            return QueryResult(intent=QueryIntent.CROSS_MODULE, content="Please specify a signal with hierarchy.")
        
        hierarchy = self.tracers['hierarchy']
        resolved = hierarchy.resolve_signal(signal)
        
        if not resolved:
            return QueryResult(intent=QueryIntent.CROSS_MODULE, signal=signal, content=f"Could not resolve '{signal}'")
        
        content = f"[Hierarchy] {signal} -> Module: {resolved.get('module', 'unknown')}"
        
        return QueryResult(intent=QueryIntent.CROSS_MODULE, signal=signal, content=content)
    
    def _handle_diagnose(self, signal: str, module: str) -> QueryResult:
        """处理诊断查询 - 使用增强的分析器"""
        # 如果没有信号，转到全面检查
        if not signal or signal in ['issues', 'module', 'problem']:
            return self._handle_full_check(signal, module)
        
        issues = []
        
        # 1. XValue 检测
        xvalue_issues = self.analyzers['xvalue'].detect(signal)
        for i in xvalue_issues:
            issues.append(f"[XValue] {i.cause.value}: {i.description}")
        
        # 2. 多驱动检测
        multi_issues = self.analyzers['multi_driver'].detect(signal)
        for i in multi_issues:
            issues.append(f"[Multi-Driver] {i.driver_type.value}: {len(i.drivers)} sources")
        
        # 3. 未初始化检测
        uninit_issues = self.analyzers['uninitialized'].detect(signal)
        for i in uninit_issues:
            issues.append(f"[Uninit] {i.issue_type}: {i.description}")
        
        # 4. 检查负载
        loads = self.tracers['load'].find_load(signal)
        if not loads:
            drivers = self.tracers['driver'].find_driver(signal)
            if drivers:
                issues.append("[Warning] Signal driven but never used")
        
        if not issues:
            content = f"✅ No obvious issues found for '{signal}'"
            suggestions = ["Signal appears properly driven and used"]
        else:
            content = f"[Diagnosis] {signal} - {len(issues)} issue(s) found"
            suggestions = [
                "Review each issue above",
                "Run 'Check module for issues' for full analysis"
            ]
        
        return QueryResult(intent=QueryIntent.DIAGNOSE, signal=signal, content=content, 
                          details=issues, suggestions=suggestions)
    
    def _handle_full_check(self, module: str, module_name: str = None) -> QueryResult:
        """处理全面检查"""
        from lint.linter import SVLinter, IssueSeverity
        
        linter = SVLinter(self.parser)
        report = linter.run_all()
        
        errors = [i for i in report.issues if i.severity == IssueSeverity.ERROR]
        warnings = [i for i in report.issues if i.severity == IssueSeverity.WARNING]
        
        content = f"[Full Check] Errors: {len(errors)}, Warnings: {len(warnings)}"
        
        details = []
        for e in errors[:5]:
            details.append(f"  ERROR: {e.message}")
        for w in warnings[:5]:
            details.append(f"  WARNING: {w.message}")
        
        suggestions = ["Run: lint --check unused", "Run: lint --check multi"]
        
        return QueryResult(intent=QueryIntent.FULL_CHECK, content=content, details=details, suggestions=suggestions)
    
    def _handle_clock_domain(self, signal: str, module: str) -> QueryResult:
        """处理时钟域查询"""
        if not signal:
            return QueryResult(intent=QueryIntent.CLOCK_DOMAIN, content="Please specify a signal.")
        
        drivers = self.tracers['driver'].find_driver(signal)
        ff_drivers = [d for d in drivers if d.driver_kind.name == 'ALWAYS_FF']
        
        if not ff_drivers:
            return QueryResult(intent=QueryIntent.CLOCK_DOMAIN, signal=signal, 
                             content=f"Signal '{signal}' is not a register (not driven by always_ff)")
        
        content = f"[Clock Domain] {signal} - {len(ff_drivers)} always_ff driver(s)"
        details = ["Check always_ff @(posedge clk) for clock info"]
        
        return QueryResult(intent=QueryIntent.CLOCK_DOMAIN, signal=signal, content=content, details=details)

    # 便捷方法
    def find_drivers(self, signal: str):
        return self.tracers['driver'].find_driver(signal)
    
    def find_loads(self, signal: str):
        return self.tracers['load'].find_load(signal)
    
    def trace_data_flow(self, signal: str):
        return self.tracers['dataflow'].find_flow(signal)
    
    def full_check(self):
        from lint.linter import SVLinter
        return SVLinter(self.parser).run_all()
