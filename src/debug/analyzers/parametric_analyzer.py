"""
ParametricDesignAnalyzer - 参数化设计分析器
分析参数化设计的使用情况: parameter, generate, function, interface, class
"""

import sys
import os
import re
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))


@dataclass
class ParameterInfo:
    """参数信息"""
    name: str
    default_value: str
    line: int
    module_name: str
    is_overridden: bool = False


@dataclass
class GenerateBlock:
    """Generate块信息"""
    kind: str  # for, if, case
    condition: str
    line: int = 0
    iterations: int = 0


@dataclass
class FunctionInfo:
    """Function信息"""
    name: str
    line: int = 0
    parameters: List[str] = field(default_factory=list)
    return_type: str = ""
    usage_count: int = 0


@dataclass
class InterfaceInfo:
    """Interface信息"""
    name: str
    line: int = 0
    signals: List[str] = field(default_factory=list)
    usage_count: int = 0


@dataclass
class ClassInfo:
    """Class信息"""
    name: str
    line: int = 0
    parameters: List[str] = field(default_factory=list)
    properties: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    instantiation_count: int = 0


@dataclass
class ParametricReport:
    """参数化设计报告"""
    # 参数统计
    parameter_count: int = 0
    parameters: List[ParameterInfo] = field(default_factory=list)
    overridden_params: List[str] = field(default_factory=list)
    
    # Generate统计
    generate_count: int = 0
    generate_blocks: List[GenerateBlock] = field(default_factory=list)
    
    # Function统计
    function_count: int = 0
    functions: List[FunctionInfo] = field(default_factory=list)
    
    # Interface统计
    interface_count: int = 0
    interfaces: List[InterfaceInfo] = field(default_factory=list)
    
    # Class统计
    class_count: int = 0
    classes: List[ClassInfo] = field(default_factory=list)
    total_instantiations: int = 0
    
    # 复用性评分
    reusability_score: float = 0.0
    modularity_score: float = 0.0
    
    # 建议
    suggestions: List[str] = field(default_factory=list)


class ParametricDesignAnalyzer:
    """参数化设计分析器"""
    
    def __init__(self, parser):
        self.parser = parser
    
    def analyze(self) -> ParametricReport:
        """执行分析"""
        report = ParametricReport()
        
        for path, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            try:
                with open(path, 'r') as f:
                    content = f.read()
            except:
                continue
            
            # 提取所有类型的设计元素
            self._extract_parameters(content, report, path)
            self._extract_generate_blocks(content, report)
            self._extract_functions(content, report)
            self._extract_interfaces(content, report)
            self._extract_classes(content, report)
        
        # 计算复用性评分
        self._calculate_scores(report)
        
        # 生成建议
        self._generate_suggestions(report)
        
        return report
    
    def _extract_parameters(self, content: str, report: ParametricReport, path: str):
        """提取参数"""
        # 1. 模块参数
        param_pattern = r'parameter\s+(\w+)\s*=\s*([^,;]+)'
        params = re.finditer(param_pattern, content)
        
        for match in params:
            param = ParameterInfo(
                name=match.group(1),
                default_value=match.group(2).strip(),
                line=content[:match.start()].count('\n') + 1,
                module_name=os.path.basename(path)
            )
            report.parameters.append(param)
            report.parameter_count += 1
        
        # 2. 检查参数是否被覆盖
        override_pattern = r'\.(\w+)\s*='
        overrides = re.findall(override_pattern, content)
        for ov in overrides:
            if ov not in report.overridden_params:
                report.overridden_params.append(ov)
        
        # 3. localparam
        localparam_pattern = r'localparam\s+(\w+)\s*=\s*([^,;]+)'
        localparams = re.finditer(localparam_pattern, content)
        for match in localparams:
            param = ParameterInfo(
                name=match.group(1),
                default_value=match.group(2).strip(),
                line=content[:match.start()].count('\n') + 1,
                module_name=os.path.basename(path)
            )
            report.parameters.append(param)
            report.parameter_count += 1
    
    def _extract_generate_blocks(self, content: str, report: ParametricReport):
        """提取Generate块"""
        # for循环generate
        for_pattern = r'generate\s+for\s*\((.*?)\)\s*begin(?::\s*(\w+))?'
        for_matches = re.finditer(for_pattern, content, re.DOTALL)
        
        for match in for_matches:
            init, cond, inc = self._parse_for_condition(match.group(1))
            gen = GenerateBlock(
                kind='for',
                condition=f"{init}; {cond}; {inc}",
                iterations=self._estimate_iterations(init, cond, inc),
                line=content[:match.start()].count('\n') + 1
            )
            report.generate_blocks.append(gen)
            report.generate_count += 1
        
        # if generate
        if_pattern = r'generate\s+if\s*\(([^)]+)\)'
        if_matches = re.finditer(if_pattern, content)
        
        for match in if_matches:
            gen = GenerateBlock(
                kind='if',
                condition=match.group(1),
                line=content[:match.start()].count('\n') + 1
            )
            report.generate_blocks.append(gen)
            report.generate_count += 1
        
        # case generate
        case_pattern = r'generate\s+case'
        case_matches = re.finditer(case_pattern, content)
        
        for match in case_matches:
            gen = GenerateBlock(
                kind='case',
                condition='case',
                line=content[:match.start()].count('\n') + 1
            )
            report.generate_blocks.append(gen)
            report.generate_count += 1
    
    def _parse_for_condition(self, cond: str) -> Tuple[str, str, str]:
        """解析for条件"""
        parts = cond.split(';')
        init = parts[0].strip() if len(parts) > 0 else ""
        condition = parts[1].strip() if len(parts) > 1 else ""
        inc = parts[2].strip() if len(parts) > 2 else ""
        return init, condition, inc
    
    def _estimate_iterations(self, init: str, cond: str, inc: str) -> int:
        """估算迭代次数"""
        try:
            # 简单估算: 提取起始值和结束值
            start_match = re.search(r'=\s*(\d+)', init)
            end_match = re.search(r'[<>=]+\s*(\d+)', cond)
            
            if start_match and end_match:
                start = int(start_match.group(1))
                end = int(end_match.group(1))
                return max(1, end - start + 1)
        except:
            pass
        return 1
    
    def _extract_functions(self, content: str, report: ParametricReport):
        """提取函数"""
        # function声明
        func_pattern = r'function\s+(?:\w+\s+)?(\w+)\s*\('
        funcs = re.finditer(func_pattern, content)
        
        for match in funcs:
            name = match.group(1)
            
            # 查找参数
            func_start = match.start()
            func_end = content.find('endfunction', func_start)
            if func_end < 0:
                continue
            
            func_content = content[func_start:func_end]
            
            # 提取参数列表
            param_match = re.search(r'function\s+\w+\s*\(([^)]*)\)', func_content)
            params = []
            if param_match:
                params = [p.strip() for p in param_match.group(1).split(',') if p.strip()]
            
            func_info = FunctionInfo(
                name=name,
                parameters=params,
                line=content[:func_start].count('\n') + 1
            )
            
            # 统计使用次数
            func_info.usage_count = len(re.findall(rf'\b{name}\s*\(', content))
            
            report.functions.append(func_info)
            report.function_count += 1
    
    def _extract_interfaces(self, content: str, report: ParametricReport):
        """提取接口"""
        # interface声明
        iface_pattern = r'interface\s+(\w+)'
        ifaces = re.finditer(iface_pattern, content)
        
        for match in ifaces:
            name = match.group(1)
            
            # 查找信号
            iface_start = match.start()
            iface_end = content.find('endinterface', iface_start)
            if iface_end < 0:
                continue
            
            iface_content = content[iface_start:iface_end]
            signals = re.findall(r'\b(logic|wire|reg)\s+(?:\[[^\]]+\]\s+)?(\w+)', iface_content)
            signal_names = [s[1] for s in signals]
            
            info = InterfaceInfo(
                name=name,
                signals=signal_names,
                line=content[:iface_start].count('\n') + 1
            )
            
            # 统计实例化次数
            info.usage_count = len(re.findall(rf'\b{name}\s+(?!_def)', content))
            
            report.interfaces.append(info)
            report.interface_count += 1
    
    def _extract_classes(self, content: str, report: ParametricReport):
        """提取类"""
        # class声明
        class_pattern = r'class\s+(\w+)'
        classes = re.finditer(class_pattern, content)
        
        for match in classes:
            name = match.group(1)
            
            # 查找参数化
            class_start = match.start()
            class_end = content.find('endclass', class_start)
            if class_end < 0:
                continue
            
            class_content = content[class_start:class_end]
            
            # 提取参数
            param_match = re.search(r'class\s+\w+\s*#\(([^)]+)\)', class_content)
            params = []
            if param_match:
                params = [p.strip().split()[-1] for p in param_match.group(1).split(',')]
            
            # 提取属性
            properties = re.findall(r'(?:rand\s+)?(?:\w+\s+)+(\w+)\s*;', class_content)
            
            # 提取方法
            methods = re.findall(r'(?:virtual\s+)?function|task\s+(\w+)', class_content)
            methods = [m for m in methods if m]
            
            info = ClassInfo(
                name=name,
                parameters=params,
                properties=properties,
                methods=methods,
                line=content[:class_start].count('\n') + 1
            )
            
            # 统计实例化次数
            info.instantiation_count = len(re.findall(rf'\b{name}\s+(?:_t\s+)?[a-z]\w*\s*=', content))
            
            report.classes.append(info)
            report.class_count += 1
            report.total_instantiations += info.instantiation_count
    
    def _calculate_scores(self, report: ParametricReport):
        """计算评分"""
        # 复用性评分: 基于参数数量、generate使用、function数量
        reuse_factors = (
            report.parameter_count * 2 +
            report.generate_count * 3 +
            report.function_count * 2 +
            report.interface_count * 5 +
            report.class_count * 5 +
            report.total_instantiations * 2
        )
        report.reusability_score = min(100, reuse_factors)
        
        # 模块化评分: 基于generate块、interface、class
        modularity_factors = (
            report.generate_count * 3 +
            report.interface_count * 5 +
            report.class_count * 5
        )
        report.modularity_score = min(100, modularity_factors)
    
    def _generate_suggestions(self, report: ParametricReport):
        """生成建议"""
        suggestions = []
        
        if report.parameter_count == 0:
            suggestions.append("未发现参数,考虑使用parameter提高设计灵活性")
        
        if report.generate_count == 0:
            suggestions.append("未发现generate块,可能存在重复代码")
        
        if report.function_count == 0:
            suggestions.append("未发现function,考虑提取公共逻辑")
        
        if report.interface_count == 0:
            suggestions.append("未使用interface,可以使用interface简化信号连接")
        
        if report.class_count == 0:
            suggestions.append("未使用class,考虑使用OOP提高代码复用")
        
        if report.classes:
            total_params = sum(len(c.parameters) for c in report.classes)
            if total_params == 0:
                suggestions.append("Class未使用参数化,考虑添加参数提高通用性")
        
        if not suggestions:
            suggestions.append("参数化设计表现良好")
        
        report.suggestions = suggestions
    
    def print_report(self, report: ParametricReport):
        """打印报告"""
        print("="*60)
        print("Parametric Design Analysis Report")
        print("="*60)
        
        print(f"\nParameters: {report.parameter_count}")
        print(f"  Overridden: {len(report.overridden_params)}")
        if report.parameters[:5]:
            print(f"  Examples: {[p.name for p in report.parameters[:5]]}")
        
        print(f"\nGenerate Blocks: {report.generate_count}")
        if report.generate_blocks:
            kinds = Counter(g.kind for g in report.generate_blocks)
            print(f"  Types: {dict(kinds)}")
        
        print(f"\nFunctions: {report.function_count}")
        if report.functions[:5]:
            print(f"  Examples: {[f.name for f in report.functions[:5]]}")
        
        print(f"\nInterfaces: {report.interface_count}")
        if report.interfaces:
            print(f"  {[i.name for i in report.interfaces]}")
        
        print(f"\nClasses: {report.class_count}")
        print(f"  Total instantiations: {report.total_instantiations}")
        if report.classes:
            for c in report.classes[:3]:
                print(f"    {c.name}: {len(c.parameters)} params, {len(c.methods)} methods")
        
        print(f"\nScores:")
        print(f"  Reusability: {report.reusability_score:.1f}")
        print(f"  Modularity: {report.modularity_score:.1f}")
        
        print("="*60)
        
        if report.suggestions:
            print(f"\nSuggestions:")
            for s in report.suggestions:
                print(f"  - {s}")


__all__ = ['ParametricDesignAnalyzer', 'ParametricReport']
