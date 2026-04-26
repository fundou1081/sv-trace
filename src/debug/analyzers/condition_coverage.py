"""
ConditionCoverage - 条件覆盖分析器
分析if嵌套条件，生成条件覆盖率和cross覆盖
"""
import os
import sys
import re
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


@dataclass
class Condition:
    """单个条件"""
    id: str
    original_expr: str  # 原始表达式
    expanded_signals: List[str] = field(default_factory=list)  # 展开后的信号
    is_simple: bool = True  # 是否简单条件
    conditions: List[str] = field(default_factory=list)  # 子条件(for cross)


@dataclass  
class ConditionBranch:
    """条件分支"""
    condition_id: str
    branch_type: str  # "if", "else_if", "else"
    line_number: int = 0
    condition_expr: str = ""
    expanded_conditions: List[Condition] = field(default_factory=list)


@dataclass
class ConditionCoverage:
    """条件覆盖信息"""
    if_id: str
    line: int
    depth: int  # 嵌套深度
    branches: List[ConditionBranch] = field(default_factory=list)
    
    # 覆盖统计
    total_conditions: int = 0
    covered_conditions: int = 0
    coverage_rate: float = 0.0
    
    # Cross覆盖
    cross_pairs: List[Tuple[str, str]] = field(default_factory=list)
    covered_cross: int = 0


@dataclass
class CoverageReport:
    """覆盖报告"""
    conditions: List[ConditionCoverage] = field(default_factory=list)
    total_if_count: int = 0
    total_conditions: int = 0
    total_branches: int = 0
    average_coverage: float = 0.0
    
    # 建议
    suggestions: List[str] = field(default_factory=list)


class ConditionCoverageAnalyzer:
    """条件覆盖分析器"""
    
    def __init__(self, parser):
        self.parser = parser
        self._conditions: List[ConditionCoverage] = []
        self._signal_map: Dict[str, List[str]] = {}  # 中间变量 -> 底层信号
    
    def analyze(self) -> CoverageReport:
        """执行条件覆盖分析"""
        self._conditions = []
        self._signal_map = {}
        
        # 1. 收集所有中间变量到信号的映射
        self._build_signal_dependency_map()
        
        # 2. 分析每个文件的if嵌套
        for fname, tree in self.parser.trees.items():
            code = self._get_code(fname)
            if code:
                self._analyze_if_conditions(code, fname)
        
        # 3. 生成统计和建议
        report = self._generate_report()
        
        return report
    
    def _get_code(self, fname: str) -> str:
        """获取源码"""
        if fname in self.parser.trees:
            tree = self.parser.trees[fname]
            if hasattr(tree, 'source') and tree.source:
                return tree.source
        
        try:
            with open(fname) as f:
                return f.read()
        except:
            return ""
    
    def _build_signal_dependency_map(self):
        """构建中间变量到信号的映射"""
        from trace.dependency import DependencyAnalyzer
        
        dep_analyzer = DependencyAnalyzer(self.parser)
        
        # 获取所有信号
        from trace.driver import DriverCollector
        collector = DriverCollector(self.parser)
        signals = collector.get_all_signals()
        
        for sig in signals:
            dep = dep_analyzer.analyze(sig)
            if dep.depends_on:
                # 有依赖的信号可能是中间变量
                # 只保留组合逻辑路径上的
                if len(dep.depends_on) <= 5:  # 合理范围内的依赖
                    self._signal_map[sig] = dep.depends_on[:10]
    
    def _analyze_if_conditions(self, code: str, fname: str):
        """分析if条件"""
        lines = code.split('\n')
        
        # 跟踪嵌套深度
        depth_stack = []
        current_if_id = 0
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # 跳过注释和空行
            if not stripped or stripped.startswith('//') or stripped.startswith('*'):
                i += 1
                continue
            
            # 检测if语句
            if_match = re.match(r'if\s*\((.+)\)\s*', stripped)
            if if_match:
                expr = if_match.group(1)
                depth = len(depth_stack)
                
                # 创建覆盖信息
                cov = self._create_condition_coverage(
                    if_id=f"if_{fname}_{current_if_id}",
                    expr=expr,
                    line=i + 1,
                    depth=depth
                )
                
                self._conditions.append(cov)
                depth_stack.append(current_if_id)
                current_if_id += 1
                
                # 跳过到匹配的}或end
                i = self._skip_to_end(lines, i)
                continue
            
            # 检测else if
            elif_match = re.match(r'end\s+|\s+else\s+if\s*\((.+)\)\s*', stripped)
            if elif_match and len(depth_stack) > 0:
                expr = elif_match.group(1) if elif_match.group(1) else ""
                
                parent_id = depth_stack[-1]
                if parent_id < len(self._conditions):
                    cov = self._conditions[parent_id]
                    
                    branch = ConditionBranch(
                        condition_id=cov.if_id,
                        branch_type="else_if",
                        line_number=i + 1,
                        condition_expr=expr,
                        expanded_conditions=self._expand_conditions(expr)
                    )
                    cov.branches.append(branch)
                    cov.total_conditions += len(branch.expanded_conditions)
                
                i = self._skip_to_end(lines, i)
                continue
            
            # 检测else
            if re.match(r'\s*else\s*', stripped):
                if len(depth_stack) > 0:
                    parent_id = depth_stack[-1]
                    if parent_id < len(self._conditions):
                        cov = self._conditions[parent_id]
                        
                        branch = ConditionBranch(
                            condition_id=cov.if_id,
                            branch_type="else",
                            line_number=i + 1,
                            condition_expr="else"
                        )
                        cov.branches.append(branch)
                
                i = self._skip_to_end(lines, i)
                continue
            
            # 检测end
            if stripped.startswith('end') or stripped == 'endmodule':
                if depth_stack:
                    depth_stack.pop()
            
            i += 1
    
    def _create_condition_coverage(self, if_id: str, expr: str, line: int, depth: int) -> ConditionCoverage:
        """创建条件覆盖对象"""
        cov = ConditionCoverage(
            if_id=if_id,
            line=line,
            depth=depth
        )
        
        # 解析if条件
        branch = ConditionBranch(
            condition_id=if_id,
            branch_type="if",
            line_number=line,
            condition_expr=expr,
            expanded_conditions=self._expand_conditions(expr)
        )
        
        cov.branches.append(branch)
        cov.total_conditions = len(branch.expanded_conditions)
        
        # 生成cross对
        cov.cross_pairs = self._generate_cross_pairs(branch.expanded_conditions)
        
        return cov
    
    def _expand_conditions(self, expr: str) -> List[Condition]:
        """展开条件到原始信号"""
        conditions = []
        
        # 清理表达式
        expr = expr.strip()
        
        # 处理逻辑运算符连接的多个条件
        # a && b || c -> [a, b, c] 或者分组
        
        # 找到所有独立的基本条件
        # 支持: a == b, a < b, a[0], !a, a && b, a || b
        
        tokens = self._split_logical_expr(expr)
        
        for i, token in enumerate(tokens):
            token = token.strip()
            if not token:
                continue
            
            # 展开中间变量
            expanded = self._resolve_signal(token)
            
            cond = Condition(
                id=f"cond_{i}",
                original_expr=token,
                expanded_signals=expanded,
                is_simple=len(expanded) == 1,
                conditions=[token]  # 原始条件
            )
            conditions.append(cond)
        
        return conditions
    
    def _split_logical_expr(self, expr: str) -> List[str]:
        """分割逻辑表达式"""
        result = []
        current = ""
        paren_depth = 0
        bracket_depth = 0
        
        i = 0
        while i < len(expr):
            ch = expr[i]
            
            if ch == '(':
                paren_depth += 1
                current += ch
            elif ch == ')':
                paren_depth -= 1
                current += ch
            elif ch == '[':
                bracket_depth += 1
                current += ch
            elif ch == ']':
                bracket_depth -= 1
                current += ch
            elif ch == '&' and paren_depth == 0 and bracket_depth == 0:
                if i + 1 < len(expr) and expr[i+1] == '&':
                    if current.strip():
                        result.append(current.strip())
                    current = ""
                    i += 2
                    continue
                else:
                    current += ch
            elif ch == '|' and paren_depth == 0 and bracket_depth == 0:
                if i + 1 < len(expr) and expr[i+1] == '|':
                    if current.strip():
                        result.append(current.strip())
                    current = ""
                    i += 2
                    continue
                else:
                    current += ch
            else:
                current += ch
            
            i += 1
        
        if current.strip():
            result.append(current.strip())
        
        return result
    
    def _resolve_signal(self, expr: str) -> List[str]:
        """解析表达式中的信号"""
        signals = []
        
        # 提取所有标识符
        tokens = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', expr)
        
        # 过滤关键字
        keywords = {'if', 'else', 'for', 'while', 'case', 'switch', 
                   'posedge', 'negedge', 'and', 'or', 'not', 'true', 'false'}
        tokens = [t for t in tokens if t not in keywords]
        
        for token in tokens:
            # 检查是否是中间变量
            if token in self._signal_map:
                # 展开到底层
                signals.extend(self._signal_map[token][:5])  # 限制数量
            else:
                # 可能是原始信号
                signals.append(token)
        
        # 去重
        return list(set(signals))[:10]
    
    def _generate_cross_pairs(self, conditions: List[Condition]) -> List[Tuple[str, str]]:
        """生成cross对"""
        pairs = []
        signals = []
        
        for cond in conditions:
            signals.extend(cond.expanded_signals)
        
        # 生成所有两两组合
        for i in range(len(signals)):
            for j in range(i + 1, len(signals)):
                pairs.append((signals[i], signals[j]))
        
        return pairs[:20]  # 限制数量
    
    def _skip_to_end(self, lines: List[str], start: int) -> int:
        """跳到if块的结束"""
        i = start + 1
        brace_count = 1 if '{' in lines[start] else 0
        
        while i < len(lines) and brace_count > 0:
            line = lines[i].strip()
            brace_count += line.count('{') - line.count('}')
            
            if brace_count == 0:
                return i
            
            # 简单的缩进判断
            if brace_count > 0 and (line.startswith('end') or line.startswith('endelse')):
                brace_count = 0
                return i
            
            i += 1
        
        return i
    
    def _generate_report(self) -> CoverageReport:
        """生成报告"""
        total_if = len(self._conditions)
        total_cond = sum(c.total_conditions for c in self._conditions)
        total_branch = sum(len(c.branches) for c in self._conditions)
        
        # 计算平均覆盖率
        if total_if > 0:
            avg_cov = sum(c.coverage_rate for c in self._conditions) / total_if
        else:
            avg_cov = 0.0
        
        report = CoverageReport(
            conditions=self._conditions,
            total_if_count=total_if,
            total_conditions=total_cond,
            total_branches=total_branch,
            average_coverage=avg_cov
        )
        
        # 生成建议
        self._generate_suggestions(report)
        
        return report
    
    def _generate_suggestions(self, report: CoverageReport):
        """生成建议"""
        # 低覆盖率
        low_cov = [c for c in report.conditions if c.coverage_rate < 0.8]
        if low_cov:
            report.suggestions.append(
                f"有{len(low_cov)}个if条件的覆盖率低于80%"
            )
        
        # 深层嵌套
        deep = [c for c in report.conditions if c.depth > 3]
        if deep:
            report.suggestions.append(
                f"有{len(deep)}个if嵌套深度超过3层，建议简化"
            )
        
        # 复杂条件
        complex = [c for c in report.conditions if c.total_conditions > 5]
        if complex:
            report.suggestions.append(
                f"有{len(complex)}个if条件包含超过5个子条件，考虑拆分"
            )
    
    def export_to_coverage_model(self, filename: str, report: CoverageReport):
        """导出为coverage model (SystemVerilog)"""
        content = f"""// Condition Coverage Model - Auto-generated by SV-Trace
// Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""

        for cov in report.conditions:
            content += f"""
// ============================================================================
// If at line {cov.line}, depth={cov.depth}
// ============================================================================
"""
            
            for i, branch in enumerate(cov.branches):
                branch_name = branch.branch_type.replace(' ', '_')
                
                if branch.condition_expr:
                    content += f"// Branch {i}: {branch.condition_expr}\n"
                
                # 生成covergroup
                content += f"""
covergroup cg_{cov.if_id}_{branch_name} @(posedge clk);
    option.per_instance = 1;
    option.comment = "Line {cov.line}, {branch.branch_type}";
    
"""
                    
                    for j, cond in enumerate(branch.expanded_conditions):
                        for sig in cond.expanded_signals[:3]:
                            content += f"    {sig}: coverpoint {sig} {{}}\n"
                        
                        # Cross覆盖
                        if len(cond.expanded_signals) >= 2:
                            sigs = ', '.join(cond.expanded_signals[:2])
                            content += f"    cross_{j}: cross {{ {sigs} }};\n"
                    
                    content += "endgroup\n\n"
                    
                    # 实例化
                    content += f"    cg_{cov.if_id}_{branch_name} {cov.if_id}_{branch_name}_inst;\n"
        
        with open(filename, 'w') as f:
            f.write(content)
        
        return filename
    
    def export_to_constraint(self, filename: str, report: CoverageReport):
        """导出为约束文件"""
        content = f"""// Coverage Constraints - Auto-generated by SV-Trace
// Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
        
        for cov in report.conditions:
            content += f"// Line {cov.line}, depth={cov.depth}\n"
            
            # 生成随机约束确保所有条件被覆盖
            for i, branch in enumerate(cov.branches):
                if branch.expanded_conditions:
                    sigs = [s for c in branch.expanded_conditions for s in c.expanded_signals[:2]]
                    if sigs:
                        sig_list = ' && '.join(f"{s}==1'b{0 if i%2 else 1}" for i, s in enumerate(sigs[:4]))
                        content += f"// constraint cv_{cov.if_id}_{i} {{ {sig_list}; }}\n"
        
        with open(filename, 'w') as f:
            f.write(content)
        
        return filename
    
    def print_report(self, report: CoverageReport):
        """打印报告"""
        print("\n" + "="*60)
        print("Condition Coverage Analysis Report")
        print("="*60)
        
        print(f"\n[Summary]")
        print(f"  Total If Statements: {report.total_if_count}")
        print(f"  Total Conditions: {report.total_conditions}")
        print(f"  Total Branches: {report.total_branches}")
        print(f"  Average Coverage: {report.average_coverage*100:.1f}%")
        
        if report.conditions:
            print(f"\n[Condition Details]")
            for cov in report.conditions[:10]:
                print(f"  Line {cov.line}: depth={cov.depth}, conditions={cov.total_conditions}")
                for branch in cov.branches[:3]:
                    if branch.condition_expr:
                        print(f"    - {branch.branch_type}: {branch.condition_expr[:40]}")
        
        if report.suggestions:
            print(f"\n[Suggestions]")
            for s in report.suggestions:
                print(f"  - {s}")
        
        print("\n" + "="*60)


def analyze_condition_coverage(parser) -> CoverageReport:
    """便捷函数"""
    analyzer = ConditionCoverageAnalyzer(parser)
    return analyzer.analyze()


__all__ = [
    'ConditionCoverageAnalyzer',
    'CoverageReport',
    'ConditionCoverage',
    'Condition',
    'ConditionBranch',
    'analyze_condition_coverage',
]
