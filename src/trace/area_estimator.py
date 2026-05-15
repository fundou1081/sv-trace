"""
AreaEstimator - 芯片面积估算器 v3
使用DriverCollector获取准确的驱动信息

增强版: 添加解析警告，显式打印不支持的语法结构
"""

import sys
import os
from typing import Dict
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from trace.driver import DriverCollector

# 导入解析警告模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from trace.parse_warn import (
    ParseWarningHandler,
    warn_unsupported,
    warn_error,
    WarningLevel
)


@dataclass
class AreaEstimate:
    """面积估算结果"""
    lut_count: int
    lut_as_logic: int
    lut_as_memory: int
    ff_count: int
    dsp_count: int
    bram_count: float
    io_lut: int
    equivalent_slices: int
    details: Dict


class AreaEstimator:
    """面积估算器 v3
    
    增强: 添加解析警告
    """
    
    # 不支持的语法类型
    UNSUPPORTED_TYPES = {
        'CovergroupDeclaration': 'covergroup不影响面积估算',
        'PropertyDeclaration': 'property声明无面积',
        'SequenceDeclaration': 'sequence声明无面积',
        'ClassDeclaration': 'class内部面积估算可能不完整',
        'InterfaceDeclaration': 'interface内部面积估算可能不完整',
        'PackageDeclaration': 'package无面积',
        'ProgramDeclaration': 'program块面积估算可能不完整',
        'ClockingBlock': 'clocking block面积估算有限',
    }
    
    # 资源模型系数
    LUT_PER_OP = {
        'add': 1,      # 加法每位1 LUT
        'sub': 1,      # 减法每位1 LUT
        'mul': 8,      # 32位乘法约8 LUT6
        'div': 16,     # 除法约16 LUT
        'compare': 1,  # 比较1 LUT
        'logic': 0.1,  # 逻辑运算
        'shift': 1,    # 移位
    }
    
    FF_PER_BIT = 1.0  # 每位1 FF
    DSP_PER_MUL = 1.0 # 每乘法器1 DSP48
    
    def __init__(self, parser, verbose: bool = True):
        self.parser = parser
        self.verbose = verbose
        # 创建警告处理器
        self.warn_handler = ParseWarningHandler(
            verbose=verbose,
            component="AreaEstimator"
        )
        self._dc = DriverCollector(parser, verbose=verbose)
        self._unsupported_encountered = set()
    
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
                                    component="AreaEstimator"
                                )
                                self._unsupported_encountered.add(kind_name)
                except Exception as e:
                    self.warn_handler.warn_error(
                        "UnsupportedSyntaxCheck",
                        e,
                        context=f"file={key}",
                        component="AreaEstimator"
                    )
    
    def analyze(self, module_name: str = None) -> AreaEstimate:
        """分析面积"""
        # 先检查不支持的语法
        self._check_unsupported_syntax()
        
        total_lut = 0
        total_ff = 0
        total_dsp = 0
        total_bram = 0
        always_ff_signals = set()
        always_comb_signals = set()
        
        # 获取所有有驱动的信号
        all_signals = list(self._dc.drivers.keys())
        
        for sig in all_signals:
            try:
                drivers = self._dc.find_driver(sig)
            except Exception as e:
                self.warn_handler.warn_error(
                    "DriverSearch",
                    e,
                    context=f"signal={sig}",
                    component="AreaEstimator"
                )
                continue
            
            if not drivers:
                continue
            
            # 估算位宽(从信号名或声明)
            width = self._estimate_width(sig)
            
            for d in drivers:
                try:
                    # FF统计 - always_ff
                    if d.kind == 'always_ff':
                        total_ff += width
                        always_ff_signals.add(sig)
                    
                    # LUT统计 - always_comb
                    if d.kind == 'always_comb':
                        total_lut += self._estimate_lut(sig, d, width)
                        always_comb_signals.add(sig)
                except Exception as e:
                    self.warn_handler.warn_error(
                        "AreaCalculation",
                        e,
                        context=f"signal={sig}",
                        component="AreaEstimator"
                    )
        
        # 计算结果
        details = {
            'module': module_name or 'top',
            'always_ff_signals': list(always_ff_signals),
            'always_comb_signals': list(always_comb_signals),
        }
        
        return AreaEstimate(
            lut_count=total_lut,
            lut_as_logic=total_lut,
            lut_as_memory=0,
            ff_count=total_ff,
            dsp_count=total_dsp,
            bram_count=total_bram,
            io_lut=0,
            equivalent_slices=total_lut // 8 + total_ff // 8,
            details=details
        )
    
    def _estimate_width(self, sig: str) -> int:
        """估算信号位宽
        
        符合铁律1: 优先从 AST 提取实际位宽信息
        仅在 AST 无法提供时使用启发式推断作为后备
        """
        # 先尝试从 AST 声明中提取实际位宽
        width = self._get_width_from_ast(sig)
        if width > 0:
            return width
        
        # AST 无法提供时的启发式推断（后备方案）
        # 这些是经验规则，作为最后手段
        for suffix, width in [('_d', 1), ('_q', 1), ('_v', 8), ('_data', 32)]:
            if sig.endswith(suffix):
                return width
        
        return 1  # 默认1位
    
    def _get_width_from_ast(self, sig: str) -> int:
        """从 AST 声明中提取信号位宽（铁律1 优先方案）"""
        for key, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            width = self._search_signal_width(tree.root, sig)
            if width > 0:
                return width
        
        return 0
    
    def _search_signal_width(self, node, sig: str) -> int:
        """在 AST 中搜索信号声明的位宽"""
        if not hasattr(node, 'kind') or not node.kind:
            return 0
        
        kind_name = node.kind.name if hasattr(node.kind, 'name') else ''
        
        # 在 DataDeclaration 中查找信号
        if kind_name == 'DataDeclaration':
            # 查找 Declarator（信号名）
            for child in node:
                if child.kind and child.kind.name == 'SeparatedList':
                    for sep in child:
                        if sep.kind and sep.kind.name == 'Declarator':
                            # 检查这个 Declarator 是否是我们要找的信号
                            decl_name = ''
                            for decl_child in sep:
                                
                                if decl_child.kind and decl_child.kind.name == 'TokenKind':
                                    if hasattr(decl_child, 'value'):
                                        decl_name = decl_child.value
                                        break
                                elif decl_child.kind and decl_child.kind.name == 'Identifier':
                                    decl_name = str(decl_child).strip()
                                    break
                            
                            if decl_name == sig:
                                # 找到匹配的信号，回溯查找 LogicType 中的位宽声明
                                return self._extract_width_from_declaration(node)
        
        # 递归搜索子节点
        try:
            for child in node:
                width = self._search_signal_width(child, sig)
                if width > 0:
                    return width
        except:
            pass
        
        return 0
    
    def _extract_width_from_declaration(self, decl_node) -> int:
        """从 DataDeclaration 节点提取位宽"""
        for child in decl_node:
            if hasattr(child, 'kind') and child.kind and child.kind.name == 'LogicType':
                # 在 SyntaxList 中查找 VariableDimension
                for lt_child in child:
                    if lt_child.kind and lt_child.kind.name == 'SyntaxList':
                        for sl_child in lt_child:
                            if sl_child.kind and sl_child.kind.name == 'VariableDimension':
                                return self._parse_width_from_dimension(sl_child)
        return 1  # 默认1位
    
    def _parse_width_from_dimension(self, dim_node) -> int:
        """从 VariableDimension 节点解析位宽"""
        for child in dim_node:
            if hasattr(child, 'kind') and child.kind and child.kind.name == 'RangeDimensionSpecifier':
                range_text = str(child).strip()
                if ':' in range_text:
                    parts = range_text.split(':')
                    try:
                        high = int(parts[0].strip())
                        return high + 1
                    except:
                        pass
        return 1
    
    def _estimate_lut(self, sig: str, driver, width: int) -> int:
        """估算LUT使用"""
        # 从驱动信号推断操作类型
        # driver.driver 是驱动源信号名
        src = getattr(driver, 'driver', '') or ''
        src_str = str(src)
        
        if '+' in src_str or '-' in src_str:
            return int(width * self.LUT_PER_OP['add'])
        elif '*' in src_str:
            return int(width * self.LUT_PER_OP['mul'])
        elif '/' in src_str:
            return int(width * self.LUT_PER_OP['div'])
        elif '>' in src_str or '<' in src_str or '==' in src_str:
            return int(width * self.LUT_PER_OP['compare'])
        elif '&' in src_str or '|' in src_str or '^' in src_str:
            return int(width * self.LUT_PER_OP['logic'])
        
        return width  # 默认1:1
    
    def get_warning_report(self) -> str:
        """获取警告报告"""
        return self.warn_handler.get_report()
    
    def print_warning_report(self):
        """打印警告报告"""
        self.warn_handler.print_report()
