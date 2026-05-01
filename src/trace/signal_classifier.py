"""
SignalClassifier - 信号分类器 (Hybrid)
将信号自动分类为 clock/reset/data/control/port/status

增强版: 添加解析警告，显式打印不支持的语法结构
"""
import sys
import os
import re
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from parse import SVParser
from trace.driver import DriverCollector

# 导入解析警告模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from trace.parse_warn import (
    ParseWarningHandler,
    warn_unsupported,
    warn_error,
    WarningLevel
)


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
    r'.*error.*',
    r'.*_err$',
    r'.*_vld$',
    r'.*_rdy$',
]


@dataclass
class SignalInfo:
    """信号信息"""
    name: str
    category: str
    direction: str
    width: int
    line: int
    module: str
    is_clock: bool = False
    is_reset: bool = False
    patterns_matched: List[str] = field(default_factory=list)


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
    
    def summary(self) -> Dict[str, int]:
        return {
            'total': self.total(),
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
    
    def total(self) -> int:
        return (len(self.clocks) + len(self.resets) + len(self.data_signals) +
                len(self.control_signals) + len(self.status_signals) +
                len(self.port_inputs) + len(self.port_outputs) +
                len(self.port_bidirs) + len(self.unclassified))


class SignalClassifier:
    """信号分类器
    
    增强: 解析过程中显式打印不支持的语法结构
    """
    
    # 不支持的语法类型
    UNSUPPORTED_TYPES = {
        'CovergroupDeclaration': '覆盖率group不影响信号分类',
        'PropertyDeclaration': 'property声明无信号',
        'SequenceDeclaration': 'sequence声明无信号',
        'ClassDeclaration': 'class信号分类可能不完整',
        'InterfaceDeclaration': 'interface信号分类可能不完整',
        'ClockingBlock': 'clocking block信号分类有限',
    }
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        # 创建警告处理器
        self.warn_handler = ParseWarningHandler(
            verbose=verbose,
            component="SignalClassifier"
        )
        self._unsupported_encountered: Set[str] = set()
    
    def classify_signal(self, name: str, direction: str = 'internal',
                       width: int = 1, line: int = 0, module: str = "") -> SignalInfo:
        """分类单个信号"""
        category = 'unknown'
        is_clock = False
        is_reset = False
        patterns_matched = []
        
        # 时钟检测
        for pattern in CLOCK_PATTERNS:
            if re.match(pattern, name, re.IGNORECASE):
                is_clock = True
                category = 'clock'
                patterns_matched.append(f'clock:{pattern}')
                break
        
        # 复位检测
        if not is_clock:
            for pattern in RESET_PATTERNS:
                if re.match(pattern, name, re.IGNORECASE):
                    is_reset = True
                    category = 'reset'
                    patterns_matched.append(f'reset:{pattern}')
                    break
        
        # 控制信号检测
        if not is_clock and not is_reset:
            for pattern in CONTROL_PATTERNS:
                if re.match(pattern, name, re.IGNORECASE):
                    category = 'control'
                    patterns_matched.append(f'control:{pattern}')
                    break
        
        # 数据信号检测
        if not is_clock and not is_reset and category == 'unknown':
            for pattern in DATA_PATTERNS:
                if re.match(pattern, name, re.IGNORECASE):
                    category = 'data'
                    patterns_matched.append(f'data:{pattern}')
                    break
        
        # 状态信号检测
        if not is_clock and not is_reset and category == 'unknown':
            for pattern in STATUS_PATTERNS:
                if re.match(pattern, name, re.IGNORECASE):
                    category = 'status'
                    patterns_matched.append(f'status:{pattern}')
                    break
        
        return SignalInfo(
            name=name,
            category=category,
            direction=direction,
            width=width,
            line=line,
            module=module,
            is_clock=is_clock,
            is_reset=is_reset,
            patterns_matched=patterns_matched
        )
    
    def classify_all(self, parser) -> ClassificationResult:
        """对所有信号分类
        
        增强: 解析过程中显式打印不支持的语法结构
        """
        result = ClassificationResult()
        
        try:
            dc = DriverCollector(parser)
            drivers = dc.get_all_signals()
        except Exception as e:
            self.warn_handler.warn_error(
                "DriverCollection",
                e,
                context="classify_all",
                component="SignalClassifier"
            )
            return result
        
        for sig, driver_list in drivers.items():
            if not driver_list:
                continue
            
            try:
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
                    result.port_bidifs.append(sig_info)
                else:
                    result.unclassified.append(sig_info)
                    
            except Exception as e:
                self.warn_handler.warn_error(
                    "SignalClassification",
                    e,
                    context=f"signal={sig}",
                    component="SignalClassifier"
                )
        
        return result
    
    def check_unsupported_syntax(self, parser):
        """检查不支持的语法类型"""
        if not hasattr(parser, 'trees'):
            return
        
        for path, tree in parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            root = tree.root
            if hasattr(root, 'members') and root.members:
                for member in root.members:
                    kind_name = str(member.kind) if hasattr(member, 'kind') else type(member).__name__
                    
                    if kind_name in self.UNSUPPORTED_TYPES:
                        if kind_name not in self._unsupported_encountered:
                            self.warn_handler.warn_unsupported(
                                kind_name,
                                context=path,
                                suggestion=self.UNSUPPORTED_TYPES[kind_name],
                                component="SignalClassifier"
                            )
                            self._unsupported_encountered.add(kind_name)
    
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
        
        # 添加警告报告
        warning_report = self.warn_handler.get_report()
        if warning_report and "No warnings" not in warning_report:
            lines.append("\n" + "=" * 70)
            lines.append("PARSER WARNINGS:")
            lines.append(warning_report)
        
        lines.append("\n" + "=" * 70)
        return "\n".join(lines)
    
    def get_warning_report(self) -> str:
        """获取警告报告"""
        return self.warn_handler.get_report()
    
    def print_warning_report(self):
        """打印警告报告"""
        self.warn_handler.print_report()
