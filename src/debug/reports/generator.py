"""
ReportGenerator - 调试报告生成器
"""
import sys
import os
from typing import Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ReportSection:
    title: str
    content: str = ""
    items: List[str] = field(default_factory=list)


@dataclass
class DebugReport:
    title: str
    module: str = ""
    created_at: str = ""
    sections: List[ReportSection] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)


class ReportGenerator:
    def __init__(self, parser):
        self.parser = parser
    
    def generate_report(self, module: str = None) -> DebugReport:
        report = DebugReport(
            title="RTL Debug Report",
            module=module or "top",
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        report.sections.append(self._module_overview())
        report.sections.append(self._signal_summary())
        report.sections.append(self._clock_domain())
        report.sections.append(self._issues())
        report.summary = self._summary()
        
        return report
    
    def _module_overview(self) -> ReportSection:
        section = ReportSection(title="Module Overview")
        count = 0
        for tree in self.parser.trees.values():
            if hasattr(tree, 'root') and hasattr(tree.root, 'members'):
                for m in tree.root.members:
                    if 'ModuleDeclaration' in str(type(m)):
                        count += 1
        section.content = "Total modules: " + str(count)
        section.items.append("Modules: " + str(count))
        return section
    
    def _signal_summary(self) -> ReportSection:
        section = ReportSection(title="Signal Summary")
        signals = set()
        for tree in self.parser.trees.values():
            if hasattr(tree, 'root') and hasattr(tree.root, 'members'):
                for i in range(len(tree.root.members)):
                    m = tree.root.members[i]
                    if 'ModuleDeclaration' in str(type(m)):
                        if hasattr(m, 'members'):
                            for j in range(len(m.members)):
                                mm = m.members[j]
                                if 'DataDeclaration' in str(type(mm)):
                                    decls = getattr(mm, 'declarators', None)
                                    if decls:
                                        try:
                                            for decl in decls:
                                                if hasattr(decl, 'name'):
                                                    signals.add(decl.name.value)
                                        except:
                                            pass
        section.content = "Total signals: " + str(len(signals))
        section.items.append("Signals: " + str(len(signals)))
        return section
    
    def _clock_domain(self) -> ReportSection:
        section = ReportSection(title="Clock Domain Analysis")
        try:
            from debug.analyzers.clock_domain import ClockDomainAnalyzer
            ca = ClockDomainAnalyzer(self.parser)
            domains = ca.get_all_domains()
            regs = ca.get_all_registers()
            section.content = "Clock domains: " + str(len(domains))
            section.items.append("Domains: " + str(len(domains)))
            section.items.append("Registers: " + str(len(regs)))
        except Exception as e:
            section.content = "Failed: " + str(e)
        return section
    
    def _issues(self) -> ReportSection:
        section = ReportSection(title="Issues")
        section.content = "No issues found"
        section.items.append("No issues found")
        return section
    
    def _summary(self) -> Dict:
        return {"modules": 0, "signals": 0}
    
    def to_html(self, report: DebugReport) -> str:
        html = "<html><head><style>body{font-family:sans-serif;margin:20px} h1{color:#333}</style></head><body>"
        html += "<h1>" + report.title + "</h1>"
        html += "<p>Module: " + report.module + " | " + report.created_at + "</p>"
        for s in report.sections:
            html += "<h2>" + s.title + "</h2>"
            html += "<p>" + s.content + "</p>"
            html += "<ul>"
            for item in s.items:
                html += "<li>" + item + "</li>"
            html += "</ul>"
        html += "</body></html>"
        return html
    
    def to_markdown(self, report: DebugReport) -> str:
        md = "# " + report.title + "\n\n"
        md += "Module: " + report.module + "\n\n"
        for s in report.sections:
            md += "## " + s.title + "\n\n"
            md += s.content + "\n\n"
            for item in s.items:
                md += "- " + item + "\n"
        return md


class HTMLReport(ReportGenerator):
    pass

class MarkdownReport(ReportGenerator):
    pass
