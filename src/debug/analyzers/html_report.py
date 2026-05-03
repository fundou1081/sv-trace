"""HTMLReportGenerator - 通用 HTML 报告生成器。

集成所有分析器，生成统一的交互式 HTML 报告。

Example:
    >>> from debug.analyzers.html_report import HTMLReportGenerator
    >>> generator = HTMLReportGenerator("design.sv")
    >>> generator.add_section("Coverage", "80%")
    >>> generator.add_section("Complexity", "Grade A")
    >>> html = generator.generate()
    >>> print(html)
"""
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


@dataclass
class ReportSection:
    """报告章节数据类。
    
    Attributes:
        title: 标题
        level: 级别 (h2, h3, etc.)
        content: 内容 (HTML)
    """
    title: str
    level: int = 2
    content: str = ""


@dataclass
class ReportBadge:
    """报告徽章数据类。
    
    Attributes:
        text: 徽章文本
        color: 颜色 (green/yellow/red/blue)
    """
    text: str
    color: str = "blue"


class HTMLReportGenerator:
    """通用 HTML 报告生成器。
    
    生成格式化的 HTML 报告，支持章节、徽章、表格等。

    Attributes:
        title: 报告标题
        sections: 章节列表
        badges: 全局徽章列表
    
    Example:
        >>> generator = HTMLReportGenerator("Design Report")
        >>> generator.add_section("Overview", "Design statistics")
        >>> print(generator.generate())
    """
    
    def __init__(self, title: str = "SystemVerilog Design Report"):
        """初始化生成器。
        
        Args:
            title: 报告标题
        """
        self.title = title
        self.sections: List[ReportSection] = []
        self.badges: List[ReportBadge] = []
        self.metadata: Dict[str, Any] = {}
    
    def add_section(self, title: str, content: str, level: int = 2):
        """添加章节。
        
        Args:
            title: 标题
            content: HTML 内容
            level: 标题级别
        """
        self.sections.append(ReportSection(title=title, level=level, content=content))
    
    def add_badge(self, text: str, color: str = "blue"):
        """添加徽章。
        
        Args:
            text: 徽章文本
            color: 颜色
        """
        self.badges.append(ReportBadge(text=text, color=color))
    
    def add_table(self, headers: List[str], rows: List[List[str]]) -> str:
        """生成 HTML 表格。
        
        Args:
            headers: 表头列表
            rows: 行列表
        
        Returns:
            str: HTML 表格字符串
        """
        lines = ['<table class="data-table">']
        lines.append('<thead><tr>')
        for h in headers:
            lines.append(f'<th>{h}</th>')
        lines.append('</tr></thead>')
        lines.append('<tbody>')
        for row in rows:
            lines.append('<tr>')
            for cell in row:
                lines.append(f'<td>{cell}</td>')
            lines.append('</tr>')
        lines.append('</tbody>')
        lines.append('</table>')
        return '\n'.join(lines)
    
    def generate(self) -> str:
        """生成完整 HTML 报告。
        
        Returns:
            str: 完整 HTML 字符串
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{self.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .badge {{ 
            display: inline-block; 
            padding: 4px 12px; 
            border-radius: 12px;
            font-size: 12px;
            margin: 2px;
        }}
        .badge-green {{ background: #d4edda; color: #155724; }}
        .badge-yellow {{ background: #fff3cd; color: #856404; }}
        .badge-red {{ background: #f8d7da; color: #721c24; }}
        .badge-blue {{ background: #d1ecf1; color: #0c5460; }}
        table.data-table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        table.data-table th, table.data-table td {{ 
            border: 1px solid #ddd; 
            padding: 8px; 
            text-align: left; 
        }}
        table.data-table th {{ background: #f4f4f4; }}
        h1 {{ color: #333; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .section {{ margin: 20px 0; }}
        .meta {{ color: #888; font-size: 12px; }}
    </style>
</head>
<body>
    <h1>{self.title}</h1>
    <p class="meta">Generated: {timestamp}</p>
"""
        
        # Add badges
        if self.badges:
            html += '<div class="badges">\n'
            for badge in self.badges:
                html += f'<span class="badge badge-{badge.color}">{badge.text}</span>\n'
            html += '</div>\n'
        
        # Add sections
        for section in self.sections:
            html += f'<div class="section">\n'
            html += f'<h{section.level}>{section.title}</h{section.level}>\n'
            html += f'{section.content}\n'
            html += '</div>\n'
        
        html += """
</body>
</html>"""
        return html
    
    def save(self, filename: str):
        """保存报告到文件。
        
        Args:
            filename: 文件名
        """
        with open(filename, 'w') as f:
            f.write(self.generate())
