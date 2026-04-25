"""
HTML Report Generator - 通用HTML报告生成器
集成所有分析器，生成统一的交互式HTML报告
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
    """报告章节"""
    title: str
    level: int = 2  # h2, h3
    content: str = ""
    table_data: List[Dict] = None
    table_headers: List[str] = None
    badges: Dict[str, Any] = None
    warning: str = None
    success: str = None
    
    def __post_init__(self):
        if self.table_data is None:
            self.table_data = []
        if self.table_headers is None:
            self.table_headers = []
        if self.badges is None:
            self.badges = {}


@dataclass
class HTMLReportConfig:
    """HTML报告配置"""
    title: str = "SV-Trace Analysis Report"
    project_name: str = "SystemVerilog Design"
    author: str = "SV-Trace"
    include_css: bool = True
    include_js: bool = True
    theme: str = "blue"  # blue, green, purple, dark


class HTMLReportGenerator:
    """通用HTML报告生成器"""
    
    THEMES = {
        "blue": {"primary": "#2196F3", "secondary": "#1976D2", "gradient": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"},
        "green": {"primary": "#4CAF50", "secondary": "#388E3C", "gradient": "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)"},
        "purple": {"primary": "#9C27B0", "secondary": "#7B1FA2", "gradient": "linear-gradient(135deg, #8E2DE2 0%, #4A00E0 100%)"},
        "dark": {"primary": "#424242", "secondary": "#212121", "gradient": "linear-gradient(135deg, #232526 0%, #414345 100%)"},
    }
    
    def __init__(self, config: HTMLReportConfig = None):
        self.config = config or HTMLReportConfig()
        self.sections: List[ReportSection] = []
        self.module_name = "Unknown"
        self.file_path = ""
    
    def set_module(self, name: str):
        """设置模块名称"""
        self.module_name = name
    
    def set_file_path(self, path: str):
        """设置文件路径"""
        self.file_path = path
    
    def add_section(self, section: ReportSection):
        """添加章节"""
        self.sections.append(section)
    
    def add_summary(self, stats: Dict[str, Any]):
        """添加汇总统计"""
        section = ReportSection(
            title="📊 Summary",
            level=2,
            badges=stats
        )
        self.sections.insert(0, section)
    
    def add_table(self, title: str, headers: List[str], rows: List[List], 
                  level: int = 2):
        """添加表格"""
        table_data = []
        for row in rows:
            table_data.append(dict(zip(headers, row)))
        
        section = ReportSection(
            title=title,
            level=level,
            table_headers=headers,
            table_data=table_data
        )
        self.sections.append(section)
    
    def add_warning(self, message: str):
        """添加警告"""
        section = ReportSection(
            title="⚠️ Warnings",
            level=2,
            warning=message
        )
        self.sections.append(section)
    
    def add_success(self, message: str):
        """添加成功信息"""
        section = ReportSection(
            title="✅ Success",
            level=2,
            success=message
        )
        self.sections.append(section)
    
    def add_text(self, title: str, content: str, level: int = 2):
        """添加文本内容"""
        section = ReportSection(
            title=title,
            level=level,
            content=content
        )
        self.sections.append(section)
    
    def generate(self, output_path: str = None) -> str:
        """生成HTML报告"""
        theme = self.THEMES.get(self.config.theme, self.THEMES["blue"])
        
        html = self._generate_header(theme)
        html += self._generate_summary_card()
        
        for section in self.sections:
            html += self._generate_section(section, theme)
        
        html += self._generate_footer()
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(html)
        
        return html
    
    def _generate_header(self, theme: Dict) -> str:
        """生成HTML头部"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.config.title} - {self.module_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif; 
            background: #f5f7fa; 
            padding: 20px; 
            line-height: 1.6;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        
        /* Header */
        .header {{
            background: {theme['gradient']};
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }}
        .header h1 {{ font-size: 32px; margin-bottom: 10px; }}
        .header .meta {{ opacity: 0.9; font-size: 14px; }}
        .header .module-name {{ 
            background: rgba(255,255,255,0.2); 
            padding: 5px 15px; 
            border-radius: 20px; 
            display: inline-block;
            margin-top: 10px;
        }}
        
        /* Summary Cards */
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            text-align: center;
            transition: transform 0.2s;
        }}
        .summary-card:hover {{ transform: translateY(-3px); }}
        .summary-card .value {{ 
            font-size: 36px; 
            font-weight: bold; 
            color: {theme['primary']};
        }}
        .summary-card .label {{ 
            color: #666; 
            font-size: 13px; 
            margin-top: 5px;
        }}
        
        /* Section */
        .section {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .section h2 {{ 
            color: {theme['secondary']}; 
            border-bottom: 2px solid #eee; 
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .section h3 {{ 
            color: {theme['primary']}; 
            margin: 20px 0 15px;
        }}
        
        /* Table */
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        .data-table th {{
            background: {theme['primary']};
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 500;
        }}
        .data-table td {{
            padding: 10px 12px;
            border-bottom: 1px solid #eee;
        }}
        .data-table tr:hover {{ background: #f9f9f9; }}
        .data-table .mono {{ 
            font-family: 'SF Mono', 'Monaco', 'Consolas', monospace; 
            font-size: 13px;
        }}
        
        /* Badges */
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin: 2px;
        }}
        .badge-critical {{ background: #ffebee; color: #c62828; }}
        .badge-high {{ background: #fff3e0; color: #ef6c00; }}
        .badge-medium {{ background: #fff8e1; color: #f9a825; }}
        .badge-low {{ background: #e8f5e9; color: #2e7d32; }}
        .badge-info {{ background: #e3f2fd; color: #1565c0; }}
        
        /* Alert */
        .alert {{
            padding: 15px 20px;
            border-radius: 8px;
            margin: 15px 0;
        }}
        .alert-warning {{
            background: #fff3e0;
            border-left: 4px solid #ff9800;
            color: #e65100;
        }}
        .alert-success {{
            background: #e8f5e9;
            border-left: 4px solid #4caf50;
            color: #1b5e20;
        }}
        .alert-error {{
            background: #ffebee;
            border-left: 4px solid #f44336;
            color: #c62828;
        }}
        
        /* Code */
        code {{
            background: #f5f5f5;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'SF Mono', 'Monaco', monospace;
            font-size: 13px;
        }}
        pre {{
            background: #263238;
            color: #aed581;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            font-family: 'SF Mono', 'Monaco', monospace;
            font-size: 13px;
        }}
        
        /* Footer */
        .footer {{
            text-align: center;
            color: #888;
            font-size: 12px;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{self.config.title}</h1>
            <div class="meta">
                Project: {self.config.project_name} | 
                Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
                By: {self.config.author}
            </div>
            <div class="module-name">📁 {self.file_path or self.module_name}</div>
        </div>
"""
    
    def _generate_summary_card(self) -> str:
        """生成汇总卡片"""
        # 找到summary部分
        summary_section = None
        for s in self.sections:
            if s.title == "📊 Summary" or "Summary" in s.title:
                summary_section = s
                break
        
        if not summary_section or not summary_section.badges:
            return ""
        
        html = '<div class="summary-grid">'
        for key, value in summary_section.badges.items():
            label = key.replace('_', ' ').title()
            html += f'''
        <div class="summary-card">
            <div class="value">{value}</div>
            <div class="label">{label}</div>
        </div>
'''
        html += '</div>'
        return html
    
    def _generate_section(self, section: ReportSection, theme: Dict) -> str:
        """生成章节"""
        h = f"<h{section.level}>{section.title}</h{h{section.level}>"
        
        html = f'''
        <div class="section">
            {h}
'''
        
        # 内容
        if section.content:
            html += f'<p>{section.content}</p>'
        
        # 警告
        if section.warning:
            html += f'<div class="alert alert-warning">{section.warning}</div>'
        
        # 成功
        if section.success:
            html += f'<div class="alert alert-success">{section.success}</div>'
        
        # 表格
        if section.table_data and section.table_headers:
            html += self._generate_table(section.table_headers, section.table_data)
        
        html += '</div>'
        return html
    
    def _generate_table(self, headers: List[str], data: List[Dict]) -> str:
        """生成表格"""
        html = '<table class="data-table"><thead><tr>'
        for h in headers:
            html += f'<th>{h}</th>'
        html += '</tr></thead><tbody>'
        
        for row in data:
            html += '<tr>'
            for h in headers:
                val = row.get(h, '')
                # 简单处理badge
                if isinstance(val, str) and val.upper() in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']:
                    badge_class = f"badge-{val.lower()}"
                    html += f'<td><span class="badge {badge_class}">{val}</span></td>'
                else:
                    html += f'<td>{val}</td>'
            html += '</tr>'
        
        html += '</tbody></table>'
        return html
    
    def _generate_footer(self) -> str:
        """生成页脚"""
        return f'''
        <div class="footer">
            Generated by SV-Trace | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
'''
    
    def to_json(self) -> str:
        """导出为JSON (用于API)"""
        data = {
            "config": {
                "title": self.config.title,
                "module": self.module_name,
                "generated": datetime.now().isoformat()
            },
            "sections": [
                {
                    "title": s.title,
                    "content": s.content,
                    "badges": s.badges,
                    "table_headers": s.table_headers,
                    "table_data": s.table_data
                }
                for s in self.sections
            ]
        }
        return json.dumps(data, indent=2)


# 便捷函数
def create_report(title: str = "Analysis Report", **kwargs) -> HTMLReportGenerator:
    """创建报告生成器"""
    config = HTMLReportConfig(title=title, **kwargs)
    return HTMLReportGenerator(config)


__all__ = ['HTMLReportGenerator', 'HTMLReportConfig', 'ReportSection', 'create_report']
