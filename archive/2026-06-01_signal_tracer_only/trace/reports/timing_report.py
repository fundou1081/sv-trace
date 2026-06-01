"""
Timing Report Generator - 时序报告生成器
支持 HTML 和 JSON 格式
"""
import os
import sys
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from trace.timing_depth import TimingDepthAnalyzer


@dataclass
class ReportConfig:
    """报告配置"""
    title: str = "Timing Report"
    output_format: str = "html"  # html, json
    include_details: bool = True
    max_paths: int = 50
    show_all_paths: bool = False


class TimingReportGenerator:
    """时序报告生成器"""
    
    def __init__(self, parser, config: ReportConfig = None):
        self.parser = parser
        self.config = config or ReportConfig()
        self.analyzer = TimingDepthAnalyzer(parser)
        self.module_name = self._get_module_name()
    
    def _get_module_name(self) -> str:
        """获取模块名称"""
        for fname, tree in self.parser.trees.items():
            if tree and tree.root:
                header = getattr(tree.root, 'header', None)
                if header:
                    name = getattr(header, 'name', None)
                    if name:
                        return getattr(name, 'value', 'unknown')
        return 'unknown'
    
    def generate(self, output_path: str = None) -> str:
        """生成报告"""
        if self.config.output_format == 'json':
            return self._generate_json(output_path)
        else:
            return self._generate_html(output_path)
    
    def _generate_html(self, output_path: str = None) -> str:
        """生成 HTML 报告"""
        paths = self.analyzer.analyze()
        critical = self.analyzer.find_critical_path()
        worst_logic = self.analyzer.find_worst_logic_path()
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.config.title} - {self.module_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #333; margin-bottom: 10px; }}
        h2 {{ color: #555; margin: 30px 0 15px; border-bottom: 2px solid #ddd; padding-bottom: 5px; }}
        .meta {{ color: #888; font-size: 14px; margin-bottom: 20px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .stat-value {{ font-size: 32px; font-weight: bold; color: #2196F3; }}
        .stat-label {{ color: #666; font-size: 14px; margin-top: 5px; }}
        .critical-path {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .critical-path h3 {{ margin-bottom: 10px; font-size: 18px; }}
        .path-display {{ font-family: 'Courier New', monospace; background: rgba(255,255,255,0.2); padding: 15px; border-radius: 5px; word-break: break-all; }}
        .metrics {{ display: flex; gap: 30px; margin-top: 15px; }}
        .metric {{ background: rgba(255,255,255,0.2); padding: 10px 15px; border-radius: 5px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; }}
        .metric-label {{ font-size: 12px; opacity: 0.8; }}
        table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        th {{ background: #2196F3; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #eee; }}
        tr:hover {{ background: #f9f9f9; }}
        .path-cell {{ font-family: 'Courier New', monospace; font-size: 13px; }}
        .tag {{ display: inline-block; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold; }}
        .tag-critical {{ background: #f44336; color: white; }}
        .tag-warning {{ background: #ff9800; color: white; }}
        .tag-ok {{ background: #4CAF50; color: white; }}
        .domain-tag {{ background: #9c27b0; color: white; }}
        .footer {{ text-align: center; color: #888; font-size: 12px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{self.config.title}</h1>
        <div class="meta">Module: {self.module_name} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        
        <div class="summary">
            <div class="stat">
                <div class="stat-value">{len(self.analyzer.registers)}</div>
                <div class="stat-label">Registers</div>
            </div>
            <div class="stat">
                <div class="stat-value">{len(paths)}</div>
                <div class="stat-label">Timing Paths</div>
            </div>
            <div class="stat">
                <div class="stat-value">{len(self.analyzer.domains)}</div>
                <div class="stat-label">Clock Domains</div>
            </div>
            <div class="stat">
                <div class="stat-value">{critical.timing_depth if critical else 0}</div>
                <div class="stat-label">Max Timing Depth</div>
            </div>
        </div>
"""
        
        # Critical Path Section
        if critical:
            html += f"""
        <div class="critical-path">
            <h3>🔴 Critical Path (Most Timing Depth)</h3>
            <div class="path-display">{' → '.join(critical.signals)}</div>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value">{critical.timing_depth}</div>
                    <div class="metric-label">Timing Depth</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{critical.logic_depth}</div>
                    <div class="metric-label">Logic Depth</div>
                </div>
            </div>
        </div>
"""
        
        # Clock Domains Section
        if self.analyzer.domains:
            html += f"""
        <h2>⏱ Clock Domains ({len(self.analyzer.domains)})</h2>
        <table>
            <tr><th>Domain</th><th>Clock Signal</th><th>Registers</th></tr>
"""
            for name, domain in self.analyzer.domains.items():
                html += f"""            <tr><td>{name}</td><td class="path-cell">{domain.clock}</td><td>{len(domain.registers)}</td></tr>
"""
            html += "        </table>\n"
        
        # All Paths Section
        if paths:
            sorted_paths = sorted(paths, key=lambda x: (-x.timing_depth, -x.logic_depth))[:self.config.max_paths]
            
            html += f"""
        <h2>📊 All Timing Paths ({len(paths)} total, showing {len(sorted_paths)})</h2>
        <table>
            <tr>
                <th>Start</th>
                <th>End</th>
                <th>Timing Depth</th>
                <th>Logic Depth</th>
                <th>Path</th>
            </tr>
"""
            for p in sorted_paths:
                depth_tag = 'tag-critical' if p.timing_depth >= 3 else 'tag-warning' if p.timing_depth >= 2 else 'tag-ok'
                html += f"""            <tr>
                <td class="path-cell">{p.start_reg}</td>
                <td class="path-cell">{p.end_reg}</td>
                <td><span class="tag {depth_tag}">{p.timing_depth}</span></td>
                <td>{p.logic_depth}</td>
                <td class="path-cell">{' → '.join(p.signals)}</td>
            </tr>
"""
            html += "        </table>\n"
        
        # Worst Logic Path Section
        if worst_logic and worst_logic.logic_depth > 0:
            html += f"""
        <h2>⚡ Worst Logic Path (Most Operators)</h2>
        <div class="critical-path" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <h3>Logic Depth: {worst_logic.logic_depth}</h3>
            <div class="path-display">{' → '.join(worst_logic.signals)}</div>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value">{worst_logic.timing_depth}</div>
                    <div class="metric-label">Timing Depth</div>
                </div>
            </div>
        </div>
"""
        
        # CDC Analysis Section
        if len(self.analyzer.domains) > 1:
            html += self._generate_cdc_section()
        
        html += f"""
        <div class="footer">
            Generated by SV-Trace Timing Analyzer | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(html)
        
        return html
    
    def _generate_cdc_section(self) -> str:
        """生成 CDC 分析部分"""
        cdc_paths = self._analyze_cdc()
        
        html = """
        <h2>🔄 Clock Domain Crossing (CDC) Analysis</h2>
"""
        if cdc_paths:
            html += f"""        <p style="color: #f44336; margin-bottom: 15px;">⚠️ Found {len(cdc_paths)} cross-clock domain paths!</p>
        <table>
            <tr>
                <th>Source Domain</th>
                <th>Dest Domain</th>
                <th>Path</th>
                <th>Depth</th>
            </tr>
"""
            for path in cdc_paths:
                html += f"""            <tr>
                <td>{path['source_domain']}</td>
                <td>{path['dest_domain']}</td>
                <td class="path-cell">{' → '.join(path['signals'])}</td>
                <td>{path['timing_depth']}</td>
            </tr>
"""
            html += "        </table>\n"
        else:
            html += """        <p style="color: #4CAF50;">✅ No cross-clock domain paths detected</p>
"""
        
        return html
    
    def _analyze_cdc(self) -> List[Dict]:
        """分析跨时钟域路径"""
        cdc_paths = []
        regs = self.analyzer.registers
        
        # 检查寄存器对的时钟域
        for reg_name, reg in regs.items():
            if not reg.clock:
                continue
            
            # 追溯路径
            result = self.analyzer._trace_upstream(reg_name, set())
            if not result:
                continue
            
            path_signals = result[0][::-1]  # 反转，从源头到终点
            
            # 检查路径上的所有寄存器
            prev_domain = None
            for sig in path_signals:
                if sig in regs and regs[sig].clock:
                    curr_domain = regs[sig].clock
                    if prev_domain and curr_domain != prev_domain:
                        cdc_paths.append({
                            'source_domain': prev_domain,
                            'dest_domain': curr_domain,
                            'signals': path_signals,
                            'timing_depth': len([s for s in path_signals if s in regs]) - 1
                        })
                        break
                    prev_domain = curr_domain
        
        return cdc_paths
    
    def _generate_json(self, output_path: str = None) -> str:
        """生成 JSON 报告"""
        paths = self.analyzer.analyze()
        critical = self.analyzer.find_critical_path()
        worst_logic = self.analyzer.find_worst_logic_path()
        
        report = {
            'metadata': {
                'title': self.config.title,
                'module': self.module_name,
                'generated': datetime.now().isoformat(),
            },
            'summary': {
                'registers': len(self.analyzer.registers),
                'timing_paths': len(paths),
                'clock_domains': len(self.analyzer.domains),
                'max_timing_depth': critical.timing_depth if critical else 0,
                'max_logic_depth': worst_logic.logic_depth if worst_logic else 0,
            },
            'domains': {
                name: {
                    'clock': domain.clock,
                    'registers': domain.registers
                }
                for name, domain in self.analyzer.domains.items()
            },
            'registers': {
                name: asdict(reg)
                for name, reg in self.analyzer.registers.items()
            },
            'paths': [
                {
                    'start': p.start_reg,
                    'end': p.end_reg,
                    'timing_depth': p.timing_depth,
                    'logic_depth': p.logic_depth,
                    'signals': p.signals,
                    'domains': p.domains
                }
                for p in sorted(paths, key=lambda x: (-x.timing_depth, -x.logic_depth))[:self.config.max_paths]
            ],
            'critical_path': {
                'start': critical.start_reg,
                'end': critical.end_reg,
                'timing_depth': critical.timing_depth,
                'logic_depth': critical.logic_depth,
                'signals': critical.signals
            } if critical else None,
            'worst_logic_path': {
                'start': worst_logic.start_reg,
                'end': worst_logic.end_reg,
                'timing_depth': worst_logic.timing_depth,
                'logic_depth': worst_logic.logic_depth,
                'signals': worst_logic.signals
            } if worst_logic else None,
            'cdc_analysis': self._analyze_cdc()
        }
        
        json_str = json.dumps(report, indent=2)
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(json_str)
        
        return json_str


def generate_report(parser, output_path: str = None, format: str = 'html', title: str = None) -> str:
    """生成时序报告的便捷函数"""
    config = ReportConfig(
        title=title or "Timing Report",
        output_format=format
    )
    generator = TimingReportGenerator(parser, config)
    return generator.generate(output_path)
