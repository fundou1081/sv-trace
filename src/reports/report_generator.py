"""
ReportGenerator - 验证报告自动生成
生成标准格式的验证报告
"""
import os
import json
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class VerificationReport:
    """验证报告"""
    module_name: str
    version: str
    generated_at: str
    spec_version: str
    coverage: Dict
    test_results: Dict
    bugs: Dict
    issues: List[str]

class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, project_name: str = "sv_project"):
        self.project_name = project_name
    
    def generate_markdown(self, report: VerificationReport) -> str:
        """生成Markdown格式报告"""
        lines = []
        lines.append("# " + self.project_name + " 验证报告")
        lines.append("")
        lines.append(f"**模块**: {report.module_name}")
        lines.append(f"**版本**: {report.version}")
        lines.append(f"**生成时间**: {report.generated_at}")
        lines.append(f"**Spec版本**: {report.spec_version}")
        lines.append("")
        
        lines.append("## 1. 执行摘要")
        lines.append("")
        coverage = report.coverage
        lines.append(f"- 代码覆盖率: {coverage.get('code', 0):.1f}%")
        lines.append(f"- 功能覆盖率: {coverage.get('functional', 0):.1f}%")
        lines.append(f"- 断言覆盖率: {coverage.get('assertion', 0):.1f}%")
        lines.append("")
        
        lines.append("## 2. 测试结果")
        lines.append("")
        test_results = report.test_results
        lines.append(f"- 总测试数: {test_results.get('total', 0)}")
        lines.append(f"- 通过: {test_results.get('passed', 0)}")
        lines.append(f"- 失败: {test_results.get('failed', 0)}")
        lines.append(f"- 阻塞: {test_results.get('blocked', 0)}")
        pass_rate = test_results.get('pass_rate', 0)
        lines.append(f"- 通过率: {pass_rate:.1f}%")
        lines.append("")
        
        lines.append("## 3. Bug状态")
        lines.append("")
        bugs = report.bugs
        lines.append(f"- 总Bug数: {bugs.get('total', 0)}")
        lines.append(f"- Open: {bugs.get('open', 0)}")
        lines.append(f"- Closed: {bugs.get('closed', 0)}")
        lines.append(f"- Critical: {bugs.get('critical', 0)}")
        lines.append("")
        
        lines.append("## 4. 遗留问题")
        lines.append("")
        if report.issues:
            for issue in report.issues:
                lines.append(f"- {issue}")
        else:
            lines.append("无遗留问题")
        lines.append("")
        
        lines.append("## 5. 结论")
        lines.append("")
        if pass_rate >= 95 and bugs.get('critical', 0) == 0:
            lines.append("✅ **通过验证**")
        elif pass_rate >= 90:
            lines.append("⚠️ **有条件通过**")
        else:
            lines.append("❌ **未通过验证**")
        lines.append("")
        
        lines.append("---")
        lines.append(f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        return '\n'.join(lines)
    
    def generate_html(self, report: VerificationReport) -> str:
        """生成HTML格式报告"""
        md = self.generate_markdown(report)
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{self.project_name} 验证报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .pass {{ color: green; }}
        .fail {{ color: red; }}
    </style>
</head>
<body>
    <h1>{self.project_name} 验证报告</h1>
    <p><strong>模块:</strong> {report.module_name}</p>
    <p><strong>版本:</strong> {report.version}</p>
    <p><strong>生成时间:</strong> {report.generated_at}</p>
    
    <h2>执行摘要</h2>
    <table>
        <tr><th>覆盖率类型</th><th>数值</th></tr>
        <tr><td>代码覆盖率</td><td>{report.coverage.get('code', 0):.1f}%</td></tr>
        <tr><td>功能覆盖率</td><td>{report.coverage.get('functional', 0):.1f}%</td></tr>
        <tr><td>断言覆盖率</td><td>{report.coverage.get('assertion', 0):.1f}%</td></tr>
    </table>
    
    <h2>测试结果</h2>
    <p>通过率: <span class="{'pass' if report.test_results.get('pass_rate', 0) >= 90 else 'fail'}">{report.test_results.get('pass_rate', 0):.1f}%</span></p>
    
    <h2>Bug状态</h2>
    <p>总Bug: {report.bugs.get('total', 0)}, Critical: {report.bugs.get('critical', 0)}</p>
    
    <footer>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </footer>
</body>
</html>"""
        
        return html
