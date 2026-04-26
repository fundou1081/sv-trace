"""
SignalClassifier - 信号分类器 (Hybrid)
将信号自动分类为 clock/reset/data/control/port/status
"""
import sys
import os
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from parse import SVParser
from trace.driver import DriverCollector

# ========== 分类规则 (Skill) ==========

@dataclass
class SignalCategory:
    """信号分类定义"""
    name: str
    patterns: List[str]
    description: str

# Clock信号模式
CLOCK_PATTERNS = [
    r'.*clk$',
    r'.*clock$',
    r'.*_clk$',
    r'.*_clock$',
    r'i_.*_clk',
    r'.*_clk_i$',
    r'clk_.*',
    r'.*_clkin$',
    r'.*_clk_out$',
]

# Reset信号模式
RESET_PATTERNS = [
    r'.*rst$',
    r'.*reset$',
    r'.*_rst$',
    r'.*_reset$',
    r'.*_rst_n$',
    r'.*_reset_n$',
    r'.*_n$',           # active low suffix
    r'.*async.*',
    r'preset.*',
    r'presetn.*',
]

# Data信号模式
DATA_PATTERNS = [
    r'.*data.*',
    r'.*din$',
    r'.*dout$',
    r'.*_data$',
    r'.*_din$',
    r'.*_dout$',
    r'.*_q$',           # register output
    r'.*_d$',           # register input
    r'.*wr_data.*',
    r'.*rd_data.*',
    r'.*tx_data.*',
    r'.*rx_data.*',
    r'.*wdata.*',
    r'.*rdata.*',
]

# Control信号模式
CONTROL_PATTERNS = [
    r'.*en$',
    r'.*enable$',
    r'.*_en$',
    r'.*_enable$',
    r'.*valid$',
    r'.*_valid$',
    r'.*ready$',
    r'.*_ready$',
    r'.*load$',
    r'.*_load$',
    r'.*wr$',
    r'.*_wr$',
    r'.*rd$',
    r'.*_rd$',
    r'.*req$',
    r'.*_req$',
    r'.*ack$',
    r'.*_ack$',
    r'.*start$',
    r'.*stop$',
]

# Status信号模式
STATUS_PATTERNS = [
    r'.*flag$',
    r'.*_flag$',
    r'.*status$',
    r'.*_status$',
    r'.*busy$',
    r'.*_busy$',
    r'.*done$',
    r'.*_done$',
    r'.*empty$',
    r'.*_empty$',
    r'.*full$',
    r'.*_full$',
    r'.*error$',
    r'.*_error$',
    r'.*irq$',
    r'.*_irq$',
    r'.*int$',
    r'.*_int$',
    r'.*overflow$',
    r'.*underflow$',
]

# ========== 信号分类结果 ==========

@dataclass
class SignalInfo:
    """信号信息"""
    name: str
    direction: str  # input/output/inout/internal
    width: int = 1
    category: str = "unknown"
    is_clock: bool = False
    is_reset: bool = False
    matched_pattern: str = ""
    line_number: int = 0
    module: str = ""

@dataclass
class ClassificationResult:
    """分类结果"""
    clocks: List[SignalInfo] = field(default_factory=list)
    resets: List[SignalInfo] = field(default_factory=list)
    data_signals: List[SignalInfo] = field(default_factory=list)
    control_signals: List[SignalInfo] = field(default_factory=list)
    status_signals: List[SignalInfo] = field(default_factory=list)
    port_inputs: List[SignalInfo] = field(default_factory=list)
    port_outputs: List[SignalInfo] = field(default_factory=list)
    port_bidirs: List[SignalInfo] = field(default_factory=list)
    unclassified: List[SignalInfo] = field(default_factory=list)
    
    @property
    def all_signals(self) -> List[SignalInfo]:
        return (self.clocks + self.resets + self.data_signals + 
                self.control_signals + self.status_signals +
                self.port_inputs + self.port_outputs + 
                self.port_bidirs + self.unclassified)
    
    def summary(self) -> dict:
        return {
            'total': len(self.all_signals),
            'clocks': len(self.clocks),
            'resets': len(self.resets),
            'data': len(self.data_signals),
            'control': len(self.control_signals),
            'status': len(self.status_signals),
            'inputs': len(self.port_inputs),
            'outputs': len(self.port_outputs),
            'bidirs': len(self.port_bidirs),
            'unclassified': len(self.unclassified),
        }

# ========== 信号分类器 ==========

class SignalClassifier:
    """信号分类器"""
    
    def __init__(self, parser: SVParser = None):
        self.parser = parser
        self._imported_patterns = {}
    
    def add_pattern(self, category: str, pattern: str):
        """添加自定义分类规则"""
        if category not in self._imported_patterns:
            self._imported_patterns[category] = []
        self._imported_patterns[category].append(pattern)
    
    def _match_patterns(self, signal_name: str, patterns: List[str]) -> Tuple[bool, str]:
        """匹配信号名模式"""
        import re
        for pattern in patterns:
            if re.match(pattern, signal_name, re.IGNORECASE):
                return True, pattern
        return False, ""
    
    def classify_signal(self, name: str, direction: str = "internal",
                       width: int = 1, line: int = 0, module: str = "") -> SignalInfo:
        """分类单个信号"""
        signal = SignalInfo(
            name=name,
            direction=direction,
            width=width,
            line_number=line,
            module=module
        )
        
        # 组合所有patterns
        all_patterns = {
            'clock': CLOCK_PATTERNS + self._imported_patterns.get('clock', []),
            'reset': RESET_PATTERNS + self._imported_patterns.get('reset', []),
            'data': DATA_PATTERNS + self._imported_patterns.get('data', []),
            'control': CONTROL_PATTERNS + self._imported_patterns.get('control', []),
            'status': STATUS_PATTERNS + self._imported_patterns.get('status', []),
        }
        
        # 按优先级检查
        if direction == 'input':
            matched, pattern = self._match_patterns(name, all_patterns['clock'])
            if matched:
                signal.category = 'clock'
                signal.is_clock = True
                signal.matched_pattern = pattern
                return signal
            
            matched, pattern = self._match_patterns(name, all_patterns['reset'])
            if matched:
                signal.category = 'reset'
                signal.is_reset = True
                signal.matched_pattern = pattern
                return signal
        
        # 检查data
        matched, pattern = self._match_patterns(name, all_patterns['data'])
        if matched:
            signal.category = 'data'
            signal.matched_pattern = pattern
            return signal
        
        # 检查control
        matched, pattern = self._match_patterns(name, all_patterns['control'])
        if matched:
            signal.category = 'control'
            signal.matched_pattern = pattern
            return signal
        
        # 检查status
        matched, pattern = self._match_patterns(name, all_patterns['status'])
        if matched:
            signal.category = 'status'
            signal.matched_pattern = pattern
            return signal
        
        signal.category = 'unclassified'
        return signal
    
    def classify_from_parser(self, parser: SVParser = None) -> ClassificationResult:
        """从解析器分类所有信号"""
        if parser is None:
            parser = self.parser
        
        if parser is None:
            return ClassificationResult()
        
        result = ClassificationResult()
        dc = DriverCollector(parser)
        drivers = dc.get_all_signals()
        
        for sig, driver_list in drivers.items():
            if not driver_list:
                continue
            
            driver = driver_list[0]
            direction = 'internal'
            if hasattr(driver, 'port_direction'):
                direction = str(driver.port_direction).lower()
            elif hasattr(driver, 'is_input'):
                direction = 'input' if driver.is_input else 'output'
            
            width = 1
            if hasattr(driver, 'width') and driver.width:
                width = driver.width
            
            line = 0
            if hasattr(driver, 'line'):
                line = driver.line
            
            module = ''
            if hasattr(driver, 'module'):
                module = driver.module
            
            sig_info = self.classify_signal(
                name=sig,
                direction=direction,
                width=width,
                line=line,
                module=module
            )
            
            # 按类别分组
            if sig_info.is_clock:
                result.clocks.append(sig_info)
            elif sig_info.is_reset:
                result.resets.append(sig_info)
            elif sig_info.category == 'data':
                result.data_signals.append(sig_info)
            elif sig_info.category == 'control':
                result.control_signals.append(sig_info)
            elif sig_info.category == 'status':
                result.status_signals.append(sig_info)
            elif direction == 'input':
                result.port_inputs.append(sig_info)
            elif direction == 'output':
                result.port_outputs.append(sig_info)
            elif direction == 'inout':
                result.port_bidirs.append(sig_info)
            else:
                result.unclassified.append(sig_info)
        
        return result
    
    def generate_report(self, result: ClassificationResult, module_name: str = "") -> str:
        """生成分类报告"""
        lines = []
        lines.append("=" * 70)
        lines.append(f"信号分类报告: {module_name or 'All Modules'}")
        lines.append("=" * 70)
        
        summary = result.summary()
        lines.append(f"\n总计: {summary['total']} 个信号")
        lines.append(f"  时钟: {summary['clocks']}  | 复位: {summary['resets']}  | 数据: {summary['data']}")
        lines.append(f"  控制: {summary['control']} | 状态: {summary['status']}")
        lines.append(f"  输入: {summary['inputs']}  | 输出: {summary['outputs']} | 双向: {summary['bidirs']}")
        
        if result.clocks:
            lines.append(f"\n时钟信号 ({len(result.clocks)}):")
            for s in result.clocks:
                lines.append(f"  {s.name} ({s.direction})")
        
        if result.resets:
            lines.append(f"\n复位信号 ({len(result.resets)}):")
            for s in result.resets:
                lines.append(f"  {s.name} ({s.direction})")
        
        if result.data_signals:
            lines.append(f"\n数据信号 ({len(result.data_signals)}):")
            for s in result.data_signals[:15]:
                lines.append(f"  {s.name} [{s.width-1}:0]")
            if len(result.data_signals) > 15:
                lines.append(f"  ... 还有 {len(result.data_signals) - 15} 个")
        
        if result.control_signals:
            lines.append(f"\n控制信号 ({len(result.control_signals)}):")
            for s in result.control_signals:
                lines.append(f"  {s.name}")
        
        if result.status_signals:
            lines.append(f"\n状态信号 ({len(result.status_signals)}):")
            for s in result.status_signals:
                lines.append(f"  {s.name}")
        
        lines.append("\n" + "=" * 70)
        return "\n".join(lines)
