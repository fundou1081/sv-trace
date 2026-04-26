"""
SyntaxCompatibility - 语法兼容性检查
检查SystemVerilog代码在不同仿真器间的兼容性
"""
import re
from typing import List, Dict, Set
from dataclasses import dataclass
from enum import Enum

class Simulator(Enum):
    VCS = "vcs"
    VERILATOR = "verilator"
    MODELSIM = "modelsim"
    NCVERILOG = "ncverilog"
    IVERILOG = "iverilog"

@dataclass
class CompatibilityIssue:
    """兼容性问题"""
    file: str
    line: int
    feature: str
    severity: str  # error/warning/info
    incompatible_simulators: List[str]
    suggestion: str

class SyntaxCompatibilityChecker:
    """语法兼容性检查器"""
    
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
    
    def __init__(self):
        self.issues = []
    
    def check_file(self, filepath: str) -> List[CompatibilityIssue]:
        """检查文件"""
        if not filepath.endswith(('.sv', '.v')):
            return []
        
        issues = []
        
        with open(filepath, 'r') as f:
            content = f.read()
            lines = content.split('\n')
        
        for sim, patterns in self.UNSUPPORTED.items():
            if sim == Simulator.VCS:
                continue  # VCS最兼容
            
            for i, line in enumerate(lines, 1):
                for pattern, feature, suggestion in patterns:
                    if re.search(pattern, line):
                        issues.append(CompatibilityIssue(
                            file=filepath,
                            line=i,
                            feature=feature,
                            severity='warning',
                            incompatible_simulators=[sim.value],
                            suggestion=suggestion
                        ))
        
        return issues
    
    def check_project(self, project_path: str) -> Dict[str, List]:
        """检查整个项目"""
        import os
        
        results = {}
        
        for root, dirs, files in os.walk(project_path):
            for f in files:
                if f.endswith('.sv') or f.endswith('.v'):
                    filepath = os.path.join(root, f)
                    issues = self.check_file(filepath)
                    if issues:
                        results[filepath] = issues
        
        return results
    
    def generate_report(self, results: Dict) -> str:
        """生成报告"""
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
        
        return '\n'.join(lines)
