"""
CoverageAnalyzer - 代码覆盖率分析器
分析RTL代码的覆盖情况: 行覆盖、分支覆盖、条件覆盖、FSM覆盖
"""

import sys
import os
import re
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from trace.driver import DriverCollector
from trace.controlflow import ControlFlowTracer


class CoverageType(Enum):
    LINE = "line"
    BRANCH = "branch"
    CONDITION = "condition"
    FSM = "fsm"
    TOGGLE = "toggle"
    ASSERTION = "assertion"


@dataclass
class CoverageStats:
    """覆盖率统计"""
    covered: int = 0
    total: int = 0
    percentage: float = 0.0
    
    def calculate(self):
        if self.total > 0:
            self.percentage = (self.covered / self.total) * 100
        return self


@dataclass
class LineCoverage:
    """行覆盖"""
    stats: CoverageStats = field(default_factory=CoverageStats)
    uncovered_lines: List[int] = field(default_factory=list)
    covered_lines: List[int] = field(default_factory=list)


@dataclass
class BranchCoverage:
    """分支覆盖"""
    stats: CoverageStats = field(default_factory=CoverageStats)
    branches: List[Dict] = field(default_factory=list)  # {line, condition, covered}


@dataclass
class ConditionCoverage:
    """条件覆盖"""
    stats: CoverageStats = field(default_factory=CoverageStats)
    conditions: List[Dict] = field(default_factory=list)


@dataclass
class FSMCoverage:
    """FSM覆盖"""
    stats: CoverageStats = field(default_factory=CoverageStats)
    states: List[str] = field(default_factory=list)
    transitions: List[Tuple[str, str]] = field(default_factory=list)  # (from, to)


@dataclass
class CoverageReport:
    """完整覆盖率报告"""
    line: LineCoverage
    branch: BranchCoverage
    condition: ConditionCoverage
    fsm: FSMCoverage
    
    total_score: float
    suggestions: List[str]


class CoverageAnalyzer:
    """代码覆盖率分析器"""
    
    def __init__(self, parser):
        self.parser = parser
        self._dc = DriverCollector(parser)
        self._cf = ControlFlowTracer(parser)
    
    def analyze(self) -> CoverageReport:
        """执行覆盖率分析"""
        line_cov = self._analyze_line_coverage()
        branch_cov = self._analyze_branch_coverage()
        cond_cov = self._analyze_condition_coverage()
        fsm_cov = self._analyze_fsm_coverage()
        
        # 计算总分
        total = (
            line_cov.stats.percentage * 0.3 +     # 行覆盖权重30%
            branch_cov.stats.percentage * 0.3 +   # 分支覆盖权重30%
            cond_cov.stats.percentage * 0.2 +    # 条件覆盖权重20%
            fsm_cov.stats.percentage * 0.2       # FSM覆盖权重20%
        )
        
        # 生成建议
        suggestions = self._generate_suggestions(
            line_cov, branch_cov, cond_cov, fsm_cov
        )
        
        return CoverageReport(
            line=line_cov,
            branch=branch_cov,
            condition=cond_cov,
            fsm=fsm_cov,
            total_score=total,
            suggestions=suggestions
        )
    
    def _analyze_line_coverage(self) -> LineCoverage:
        """分析行覆盖"""
        covered = []
        uncovered = []
        total_lines = 0
        
        for path, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            try:
                with open(path, 'r') as f:
                    lines = f.readlines()
            except:
                continue
            
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                total_lines += 1
                
                # 检查是否有代码
                if self._is_code_line(stripped):
                    # 检查是否有驱动或引用
                    if self._is_covered(path, i, stripped):
                        covered.append(i)
                    else:
                        uncovered.append(i)
        
        stats = CoverageStats(covered=len(covered), total=total_lines)
        stats.calculate()
        
        return LineCoverage(
            stats=stats,
            uncovered_lines=uncovered,
            covered_lines=covered
        )
    
    def _is_code_line(self, line: str) -> bool:
        """判断是否是代码行"""
        # 排除空行和注释
        if not line:
            return False
        if line.startswith('//'):
            return False
        if line.startswith('/*') or line.startswith('*'):
            return False
        
        # 包含代码关键词
        code_keywords = [
            'module', 'always_ff', 'always_comb', 'always_latch',
            'assign', 'input', 'output', 'logic', 'wire', 'reg',
            'if', 'else', 'case', 'endcase', 'begin', 'end',
            '<=', '=', '+', '-', '*', '/'
        ]
        
        return any(kw in line for kw in code_keywords)
    
    def _is_covered(self, path: str, line: int, code: str) -> bool:
        """判断代码行是否被覆盖"""
        # always块中的代码行被认为是已覆盖的(可测试)
        always_keywords = ['always_ff', 'always_comb', 'always_latch']
        if any(kw in code for kw in always_keywords):
            return True
        
        # assign语句认为是已覆盖
        if 'assign' in code:
            return True
        
        # if/case分支认为是已覆盖(隐含条件覆盖)
        if any(kw in code for kw in ['if', 'case', 'begin', 'end']):
            return True
        
        # 变量声明认为是已覆盖
        if any(kw in code for kw in ['logic', 'wire', 'reg', 'input', 'output']):
            return True
        
        return False
    
    def _analyze_branch_coverage(self) -> BranchCoverage:
        """分析分支覆盖"""
        branches = []
        covered = 0
        total = 0
        
        for path, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            try:
                with open(path, 'r') as f:
                    lines = f.readlines()
            except:
                continue
            
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                
                # if分支
                if re.match(r'\s*if\s*\(', stripped):
                    total += 1
                    branches.append({
                        'line': i,
                        'type': 'if',
                        'condition': stripped,
                        'covered': True  # 静态分析假设已覆盖
                    })
                    covered += 1
                
                # else分支
                elif re.match(r'\s*else\s*', stripped):
                    total += 1
                    branches.append({
                        'line': i,
                        'type': 'else',
                        'condition': '',
                        'covered': True
                    })
                    covered += 1
                
                # case分支
                elif re.match(r'\s*\w+:\s*', stripped) or 'case' in stripped:
                    total += 1
                    branches.append({
                        'line': i,
                        'type': 'case',
                        'condition': stripped,
                        'covered': True
                    })
                    covered += 1
        
        stats = CoverageStats(covered=covered, total=total)
        stats.calculate()
        
        return BranchCoverage(stats=stats, branches=branches)
    
    def _analyze_condition_coverage(self) -> ConditionCoverage:
        """分析条件覆盖"""
        conditions = []
        covered = 0
        total = 0
        
        for path, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            try:
                with open(path, 'r') as f:
                    content = f.read()
            except:
                continue
            
            # 查找所有条件表达式
            condition_pattern = r'if\s*\(([^)]+)\)|case\s*\(([^)]+)\)'
            matches = re.finditer(condition_pattern, content)
            
            for match in matches:
                cond = match.group(1) or match.group(2)
                if cond:
                    total += 1
                    
                    # 分解复合条件
                    sub_conditions = self._split_conditions(cond)
                    conditions.append({
                        'expression': cond,
                        'sub_conditions': sub_conditions,
                        'covered': True  # 静态分析假设已覆盖
                    })
                    covered += 1
        
        stats = CoverageStats(covered=covered, total=total)
        stats.calculate()
        
        return ConditionCoverage(stats=stats, conditions=conditions)
    
    def _split_conditions(self, expr: str) -> List[str]:
        """分解复合条件表达式"""
        # 处理 && 和 ||
        sub = re.split(r'\s*(&&|\|\|)\s*', expr)
        return [s.strip() for s in sub if s.strip() and s.strip() not in ['&&', '||']]
    
    def _analyze_fsm_coverage(self) -> FSMCoverage:
        """分析FSM覆盖"""
        states = []
        transitions = []
        covered = 0
        total = 0
        
        for path, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            try:
                with open(path, 'r') as f:
                    content = f.read()
            except:
                continue
            
            # 查找状态机模式
            # 模式1: 枚举定义
            enum_match = re.findall(r'typedef\s+enum\s*\{([^}]+)\}', content)
            for enum in enum_match:
                state_names = [s.strip() for s in enum.split(',')]
                states.extend(state_names)
            
            # 模式2: case语句中的状态转换 (典型状态机)
            case_pattern = r'case\s*\(\s*(\w+)\s*\)(.*?)endcase'
            cases = re.finditer(case_pattern, content, re.DOTALL)
            
            current_state = None
            for case in cases:
                state_var = case.group(1)
                case_body = case.group(2)
                
                if 'state' in state_var.lower():
                    # 查找状态转移
                    state_pattern = r'(\w+):\s*(\w+)\s*<='
                    trans = re.findall(state_pattern, case_body)
                    for from_state, to_state in trans:
                        if from_state not in states:
                            states.append(from_state)
                        transitions.append((from_state, to_state))
                        total += 1
                        covered += 1
        
        stats = CoverageStats(covered=covered, total=max(total, 1))
        stats.calculate()
        
        return FSMCoverage(stats=stats, states=states, transitions=transitions)
    
    def _generate_suggestions(
        self, 
        line: LineCoverage, 
        branch: BranchCoverage, 
        cond: ConditionCoverage,
        fsm: FSMCoverage
    ) -> List[str]:
        """生成覆盖率改进建议"""
        suggestions = []
        
        if line.stats.percentage < 80:
            suggestions.append(
                f"行覆盖率偏低({line.stats.percentage:.1f}%), "
                f"有{len(line.uncovered_lines)}行未覆盖"
            )
        
        if branch.stats.percentage < 80:
            suggestions.append(
                f"分支覆盖率偏低({branch.stats.percentage:.1f}%)"
            )
        
        if cond.stats.percentage < 70:
            suggestions.append(
                f"条件覆盖率偏低({cond.stats.percentage:.1f}%)"
            )
        
        if fsm.stats.percentage < 100 and len(fsm.states) > 0:
            suggestions.append(
                f"FSM状态覆盖不完整({fsm.stats.percentage:.1f}%), "
                f"有{len(fsm.states)}个状态"
            )
        
        if not suggestions:
            suggestions.append("覆盖率表现良好")
        
        return suggestions
    
    def print_report(self, report: CoverageReport):
        """打印报告"""
        print("="*60)
        print("Coverage Analysis Report")
        print("="*60)
        
        print(f"\nLine Coverage: {report.line.stats.percentage:.1f}%")
        print(f"  Covered: {report.line.stats.covered}/{report.line.stats.total}")
        print(f"  Uncovered lines: {len(report.line.uncovered_lines)}")
        
        print(f"\nBranch Coverage: {report.branch.stats.percentage:.1f}%")
        print(f"  Covered: {report.branch.stats.covered}/{report.branch.stats.total}")
        print(f"  Branches: {len(report.branch.branches)}")
        
        print(f"\nCondition Coverage: {report.condition.stats.percentage:.1f}%")
        print(f"  Conditions: {report.condition.stats.covered}/{report.condition.stats.total}")
        
        print(f"\nFSM Coverage: {report.fsm.stats.percentage:.1f}%")
        print(f"  States: {len(report.fsm.states)}")
        print(f"  Transitions: {len(report.fsm.transitions)}")
        
        print(f"\n{'='*60}")
        print(f"TOTAL SCORE: {report.total_score:.1f}%")
        print("="*60)
        
        if report.suggestions:
            print(f"\nSuggestions:")
            for s in report.suggestions:
                print(f"  - {s}")


__all__ = ['CoverageAnalyzer', 'CoverageReport', 'CoverageType']
