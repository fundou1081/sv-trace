"""
ResourceEstimation - 资源利用率估算器
基于静态分析估算硬件资源消耗 (LUT, FF, DSP, BRAM 等)

增强版: 添加解析警告，显式打印不支持的语法结构
"""
import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional
from collections import defaultdict
import pyslang

# 导入解析警告模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from trace.parse_warn import (
    ParseWarningHandler,
    warn_unsupported,
    warn_error,
    WarningLevel
)


# =============================================================================
# 资源估算常量 - 基于经验公式
# =============================================================================

LUT_COST = {
    '+': 1.0, '-': 1.0, '*': 5.0, '/': 12.0, '%': 10.0, '**': 15.0,
    '==': 1.0, '!=': 1.0, '<': 1.0, '>': 1.0, '<=': 1.0, '>=': 1.0,
    '===': 1.5, '!==': 1.5, '&&': 0.25, '||': 0.25, '!': 0.25,
    '&': 0.5, '|': 0.5, '^': 1.0, '~^': 1.0, '~': 0.25,
    '<<': 0.5, '>>': 0.5, '<<<': 0.5, '>>>': 0.5,
}

DSP_COST = {'*': 1}
MUX_LUT_PER_INPUT = 0.25


@dataclass
class OperatorStats:
    operator: str
    count: int = 0
    bit_width: int = 0
    estimated_lut: float = 0.0


@dataclass
class ModuleResource:
    name: str
    lut_count: int = 0
    lut_as_logic: int = 0
    ff_count: int = 0
    reg_bits: int = 0
    dsp_count: int = 0
    operators: List[OperatorStats] = field(default_factory=list)
    muxes: Dict[str, int] = field(default_factory=dict)
    pipeline_depth: int = 0
    pipeline_stages: List[str] = field(default_factory=list)
    
    def visualize(self) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append(f"📊 RESOURCE ESTIMATION: {self.name}")
        lines.append("=" * 60)
        
        lines.append(f"\n🔢 LUTs: {self.lut_count:,}")
        lines.append(f"🔲 FFs: {self.ff_count:,}")
        lines.append(f"⚡ DSPs: {self.dsp_count:,}")
        
        if self.operators:
            lines.append(f"\n🔧 Top Operators:")
            for op in sorted(self.operators, key=lambda x: x.count, reverse=True)[:5]:
                if op.count > 0:
                    lines.append(f"  {op.operator}: {op.count} × {op.bit_width}bit")
        
        lines.append("=" * 60)
        return "\n".join(lines)


class ResourceEstimation:
    """资源估算器
    
    增强: 添加解析警告
    """
    
    # 不支持的语法类型
    UNSUPPORTED_TYPES = {
        'CovergroupDeclaration': 'covergroup不影响资源估算',
        'PropertyDeclaration': 'property声明无资源',
        'SequenceDeclaration': 'sequence声明无资源',
        'ClassDeclaration': 'class内部资源估算可能不完整',
        'InterfaceDeclaration': 'interface内部资源估算可能不完整',
        'PackageDeclaration': 'package无资源',
        'ProgramDeclaration': 'program块资源估算可能不完整',
        'ClockingBlock': 'clocking block资源估算有限',
    }
    
    def __init__(self, parser, verbose: bool = True):
        self.parser = parser
        self.verbose = verbose
        # 创建警告处理器
        self.warn_handler = ParseWarningHandler(
            verbose=verbose,
            component="ResourceEstimation"
        )
        self._unsupported_encountered = set()
    
    def _check_unsupported_syntax(self, tree, source: str = ""):
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
                    
                    if kind_name in self.UNSUPPORTED_TYPES:
                        if kind_name not in self._unsupported_encountered:
                            self.warn_handler.warn_unsupported(
                                kind_name,
                                context=source,
                                suggestion=self.UNSUPPORTED_TYPES[kind_name],
                                component="ResourceEstimation"
                            )
                            self._unsupported_encountered.add(kind_name)
            except Exception as e:
                self.warn_handler.warn_error(
                    "UnsupportedSyntaxCheck",
                    e,
                    context=f"file={source}",
                    component="ResourceEstimation"
                )
    
    def analyze_module(self, module_name: str = None) -> ModuleResource:
        modules = self._get_all_modules()
        
        if module_name:
            target = module_name
        else:
            target = modules[0] if modules else "unknown"
        
        result = ModuleResource(name=target)
        
        # 解析代码统计运算符
        try:
            stats = self._analyze_code(target)
        except Exception as e:
            self.warn_handler.warn_error(
                "CodeAnalysis",
                e,
                context=f"module={target}",
                component="ResourceEstimation"
            )
            stats = {
                'operators': defaultdict(lambda: {'count': 0, 'bit_width': 8}),
                'muxes': {'if_else': 0, 'case': 0, 'ternary': 0},
                'ff_count': 0,
                'reg_bits': 0,
                'dsp_count': 0,
                'pipeline_depth': 0,
            }
        
        # 计算资源
        result.lut_as_logic = self._calculate_lut(stats)
        result.lut_count = result.lut_as_logic
        result.ff_count = stats.get('ff_count', 0)
        result.reg_bits = stats.get('reg_bits', 0)
        result.dsp_count = stats.get('dsp_count', 0)
        result.pipeline_depth = stats.get('pipeline_depth', 0)
        
        # 运算符详情
        for op, data in stats.get('operators', {}).items():
            if data['count'] > 0:
                est_lut = data['count'] * data['bit_width'] * LUT_COST.get(op, 1.0)
                result.operators.append(OperatorStats(
                    operator=op,
                    count=data['count'],
                    bit_width=data['bit_width'],
                    estimated_lut=est_lut
                ))
        
        # MUX 结构
        result.muxes = {k: v for k, v in stats.get('muxes', {}).items() if v > 0}
        
        return result
    
    def _get_all_modules(self) -> List[str]:
        modules = []
        for fname, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            # 检查不支持的语法
            self._check_unsupported_syntax(tree, fname)
            
            members = list(tree.root.members) if hasattr(tree.root, 'members') else []
            for m in members:
                if m.kind == pyslang.SyntaxKind.ModuleDeclaration:
                    if hasattr(m, 'header') and hasattr(m.header, 'name'):
                        modules.append(str(m.header.name))
        return modules
    
    def _analyze_code(self, module_name: str) -> Dict:
        stats = {
            'operators': defaultdict(lambda: {'count': 0, 'bit_width': 8}),
            'muxes': {'if_else': 0, 'case': 0, 'ternary': 0},
            'ff_count': 0,
            'reg_bits': 0,
            'dsp_count': 0,
            'pipeline_depth': 0,
        }
        
        # 解析所有文件找对应模块
        for fname, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            # 获取源码
            try:
                source = tree.source if hasattr(tree, 'source') else ""
            except:
                source = ""
            
            if not source:
                try:
                    with open(fname) as f:
                        source = f.read()
                except:
                    continue
            
            try:
                # 1. 统计模块中的 always_ff 块数量 (FF 估算)
                lines = source.split('\n')
                in_always_ff = False
                in_module = False
                
                for line in lines:
                    stripped = line.strip()
                    
                    # 检查模块边界
                    if stripped.startswith('module '):
                        in_module = module_name in stripped
                        continue
                    elif stripped.startswith('endmodule'):
                        in_module = False
                        continue
                    
                    if not in_module:
                        continue
                    
                    # always_ff 块 -> FF
                    if 'always_ff' in stripped:
                        in_always_ff = True
                        stats['ff_count'] += 1
                    
                    # 运算符统计
                    for op in ['*', '/', '+', '-']:
                        if op in stripped:
                            stats['operators'][op]['count'] += stripped.count(op)
                    
                    # 比较运算符
                    for op in ['==', '!=', '<', '>', '<=', '>=']:
                        if op in stripped:
                            stats['operators'][op]['count'] += stripped.count(op)
                    
                    # MUX 结构
                    if stripped.startswith('if') or 'if (' in stripped:
                        stats['muxes']['if_else'] += 1
                    if stripped.startswith('case'):
                        stats['muxes']['case'] += 1
                    if '?' in stripped and ':' in stripped:
                        stats['muxes']['ternary'] += 1
                    
                    # 估算位宽
                    width = self._extract_width(stripped)
                    if width > 0:
                        for op in stats['operators']:
                            stats['operators'][op]['bit_width'] = max(stats['operators'][op]['bit_width'], width)
                            
            except Exception as e:
                self.warn_handler.warn_error(
                    "LineAnalysis",
                    e,
                    context=f"file={fname}",
                    component="ResourceEstimation"
                )
        
        return stats
    
    def _extract_width(self, line: str) -> int:
        """提取位宽"""
        # 匹配 [7:0] 或 [7:0] 格式
        match = re.search(r'\[(\d+):0\]', line)
        if match:
            return int(match.group(1)) + 1
        
        # 匹配 logic [7:0]
        match = re.search(r'logic\s*\[(\d+):0\]', line)
        if match:
            return int(match.group(1)) + 1
        
        return 0
    
    def _calculate_lut(self, stats: Dict) -> int:
        total = 0.0
        
        for op, data in stats['operators'].items():
            count = data['count']
            width = data['bit_width']
            cost = LUT_COST.get(op, 1.0)
            total += count * width * cost
        
        # MUX LUT
        muxes = stats.get('muxes', {})
        if muxes.get('if_else', 0) > 0:
            total += muxes['if_else'] * MUX_LUT_PER_INPUT * 2
        if muxes.get('case', 0) > 0:
            total += muxes['case'] * MUX_LUT_PER_INPUT * 4
        
        return max(1, int(total))
    
    def get_warning_report(self) -> str:
        """获取警告报告"""
        return self.warn_handler.get_report()
    
    def print_warning_report(self):
        """打印警告报告"""
        self.warn_handler.print_report()


def estimate_resource(parser, module_name: str = None, verbose: bool = True) -> ModuleResource:
    est = ResourceEstimation(parser, verbose=verbose)
    return est.analyze_module(module_name)
