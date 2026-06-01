"""SyntaxCompatibility - SystemVerilog 语法兼容性检查。

检查 SystemVerilog 代码在不同仿真器间的兼容性：
- VCS
- Verilator
- ModelSim
- NCVerilog
- Iverilog

增强版：添加解析警告，显式打印不支持的语法结构。

Example:
    >>> from lint.syntax_check import SyntaxCompatibilityChecker
    >>> checker = SyntaxCompatibilityChecker()
    >>> results = checker.check_project("./design")
    >>> print(checker.generate_report(results))
"""
import re
import os
import sys
from typing import List, Dict, Set
from dataclasses import dataclass
from enum import Enum

# 导入解析警告模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from trace.parse_warn import (
    ParseWarningHandler,
    warn_unsupported,
    warn_error,
    WarningLevel
)


class Simulator(Enum):
    """目标仿真器枚举。
    
    Attributes:
        VCS: Synopsys VCS
        VERILATOR: Verilator
        MODELSIM: Mentor ModelSim
        NCVERILOG: Cadence NCVerilog
        IVERILOG: Icarus Verilog
    """
    VCS = "vcs"
    VERILATOR = "verilator"
    MODELSIM = "modelsim"
    NCVERILOG = "ncverilog"
    IVERILOG = "iverilog"


@dataclass
class CompatibilityIssue:
    """兼容性问题数据类。
    
    Attributes:
        file: 文件路径
        line: 行号
        feature: 不兼容的特性
        severity: 严重级别
        incompatible_simulators: 不兼容的仿真器列表
        suggestion: 修复建议
    """
    file: str
    line: int
    feature: str
    severity: str  # error/warning/info
    incompatible_simulators: List[str]
    suggestion: str


class SyntaxCompatibilityChecker:
    """语法兼容性检查器。
    
    检查代码在不同仿真器间的兼容性问题。

    Attributes:
        verbose: 是否输出详细信息
    
    Example:
        >>> checker = SyntaxCompatibilityChecker()
        >>> checker.check_file("design.sv")
    """
    
    # 各仿真器不支持的特性
    UNSUPPORTED = {
        Simulator.VERILATOR: [
            (r'force\s+.*=', 'force语句', '改用assign'),
            (r'release\s+.*', 'release语句', '改用wire'),
            (r'class\s+.*', 'class定义', '使用package替代'),
            (r'pure\s+virtual', 'pure virtual方法', '移除'),
            (r'interface\s+.*\s+modport', 'modport声明', '简化interface'),
            (r'covergroup.*endgroup', 'covergroup', '使用coverpoint替代'),
        ],
        Simulator.MODELSIM: [
            (r'program\s+.*endprogram', 'program块', '使用module替代'),
            (r'strict_mode', '严格模式', '移除'),
            (r'rand\s+case', 'rand case', '改用普通case'),
        ],
        Simulator.VCS: [
            # VCS基本支持所有特性，但有警告级别差异
        ],
        Simulator.NCVERILOG: [
            (r'yield\s*\(', 'yield语句', '移除或替换'),
            (r'await\s*\(', 'await语句', '使用wait替代'),
        ],
    }
    
    def __init__(self, verbose: bool = True):
        """初始化检查器。
        
        Args:
            verbose: 是否打印详细信息
        """
        self.verbose = verbose
        # 创建警告处理器
        self.warn_handler = ParseWarningHandler(
            verbose=verbose,
            component="SyntaxCompatibilityChecker"
        )
        self.issues = []
        self._unsupported_encountered = set()
    
    def check_file(self, filepath: str) -> List[CompatibilityIssue]:
        """检查单个文件。
        
        Args:
            filepath: 文件路径
        
        Returns:
            List[CompatibilityIssue]: 问题列表
        """
        if not filepath.endswith(('.sv', '.v')):
            return []
        
        issues = []
        
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            self.warn_handler.warn_error(
                "FileRead",
                e,
                context=f"file={filepath}",
                component="SyntaxCompatibilityChecker"
            )
            return []
        
        for sim, patterns in self.UNSUPPORTED.items():
            if sim == Simulator.VCS:
                continue  # VCS最兼容
            
            for i, line in enumerate(lines, 1):
                for pattern, feature, suggestion in patterns:
                    if re.search(pattern, line):
                        issue = CompatibilityIssue(
                            file=filepath,
                            line=i,
                            feature=feature,
                            severity='warning',
                            incompatible_simulators=[sim.value],
                            suggestion=suggestion
                        )
                        issues.append(issue)
                        
                        # 记录警告
                        if feature not in self._unsupported_encountered:
                            self.warn_handler.warn_unsupported(
                                feature,
                                context=f"{filepath}:{i}",
                                suggestion=suggestion,
                                component="SyntaxCompatibilityChecker"
                            )
                            self._unsupported_encountered.add(feature)
        
        self.issues.extend(issues)
        return issues
    
    def check_project(self, project_path: str) -> Dict[str, List]:
        """检查整个项目。
        
        Args:
            project_path: 项目路径
        
        Returns:
            Dict: 文件到问题列表的映射
        """
        import os
        
        results = {}
        
        for root, dirs, files in os.walk(project_path):
            for f in files:
                if f.endswith('.sv') or f.endswith('.v'):
                    filepath = os.path.join(root, f)
                    try:
                        issues = self.check_file(filepath)
                        if issues:
                            results[filepath] = issues
                    except Exception as e:
                        self.warn_handler.warn_error(
                            "ProjectCheck",
                            e,
                            context=f"file={filepath}",
                            component="SyntaxCompatibilityChecker"
                        )
        
        return results
    
    def generate_report(self, results: Dict) -> str:
        """生成报告。
        
        Args:
            results: check_project 返回的结果
        
        Returns:
            str: 格式化报告
        """
        lines = []
        lines.append("=" * 60)
        lines.append("语法兼容性检查报告")
        lines.append("=" * 60)
        
        total_issues = sum(len(issues) for issues in results.values())
        lines.append(f"\n发现问题: {total_issues} 个")
        
        for filepath, issues in results.items():
            lines.append(f"\n## {filepath}")
            for issue in issues:
                lines.append(f"  Line {issue.line}: [{issue.severity}] {issue.feature}")
                lines.append(f"    建议: {issue.suggestion}")
                lines.append(f"    不兼容: {', '.join(issue.incompatible_simulators)}")
        
        if not results:
            lines.append("\n✅ 未发现问题")
        
        # 添加解析警告报告
        warning_report = self.warn_handler.get_report()
        if warning_report and "No warnings" not in warning_report:
            lines.append("\n" + "=" * 60)
            lines.append("PARSER WARNINGS:")
            lines.append(warning_report)
        
        return '\n'.join(lines)
    
    def get_warning_report(self) -> str:
        """获取警告报告。
        
        Returns:
            str: 警告报告
        """
        return self.warn_handler.get_report()
    
    def print_warning_report(self):
        """打印警告报告。"""
        self.warn_handler.print_report()


def check_syntax(source: str, verbose: bool = True):
    """简单的语法检查。
    
    Args:
        source: SystemVerilog 源代码
        verbose: 是否打印详细信息
    
    Returns:
        dict: 检查结果
    """
    import pyslang
    
    warn_handler = ParseWarningHandler(verbose=verbose, component="SyntaxCheck")
    
    try:
        tree = pyslang.SyntaxTree.fromText(source)
        return {"valid": True, "errors": []}
    except Exception as e:
        warn_handler.warn_error(
            "SyntaxParsing",
            e,
            context="check_syntax",
            component="SyntaxCheck"
        )
        return {"valid": False, "errors": [str(e)]}
