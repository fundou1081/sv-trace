"""
SpecTracker - Spec变更追踪系统
检测Spec文档变更，分析影响范围
"""
import os
import json
import difflib
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass, field

@dataclass
class SpecChange:
    """Spec变更"""
    id: str
    version: str
    timestamp: str
    author: str
    changes: List[Dict] = field(default_factory=list)
    affected_sections: List[str] = field(default_factory=list)
    impact_modules: List[str] = field(default_factory=list)
    related_rtls: List[str] = field(default_factory=list)

@dataclass
class SpecSection:
    """Spec章节"""
    id: str
    title: str
    content: str
    keywords: List[str] = field(default_factory=list)
    last_modified: str = ""

class SpecTracker:
    """Spec变更追踪器"""
    
    def __init__(self, db_path: str = "./spec_db"):
        self.db_path = db_path
        self._ensure_db()
    
    def _ensure_db(self):
        os.makedirs(self.db_path, exist_ok=True)
    
    def _get_spec_file(self, spec_name: str) -> str:
        return os.path.join(self.db_path, f"{spec_name}.json")
    
    def _get_versions_file(self, spec_name: str) -> str:
        return os.path.join(self.db_path, f"{spec_name}_versions.json")
    
    def parse_spec(self, filepath: str, spec_name: str = "main") -> List[SpecSection]:
        """解析Spec文档，提取章节"""
        sections = []
        
        if not os.path.exists(filepath):
            return sections
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        # 简单按##标题分割
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            if line.startswith('## '):
                # 保存之前的section
                if current_section:
                    sections.append(SpecSection(
                        id=f"{spec_name}_{len(sections)}",
                        title=current_section,
                        content='\n'.join(current_content),
                        keywords=self._extract_keywords(current_content)
                    ))
                
                current_section = line[3:].strip()
                current_content = []
            else:
                if current_section:
                    current_content.append(line)
        
        # 保存最后一个section
        if current_section:
            sections.append(SpecSection(
                id=f"{spec_name}_{len(sections)}",
                title=current_section,
                content='\n'.join(current_content),
                keywords=self._extract_keywords(current_content)
            ))
        
        # 保存解析结果
        spec_data = {
            'spec_name': spec_name,
            'filepath': filepath,
            'sections': [{'id': s.id, 'title': s.title, 'keywords': s.keywords} for s in sections],
            'last_parsed': datetime.now().isoformat()
        }
        
        with open(self._get_spec_file(spec_name), 'w') as f:
            json.dump(spec_data, f, indent=2)
        
        return sections
    
    def _extract_keywords(self, content: List[str]) -> List[str]:
        """提取关键词"""
        text = ' '.join(content).lower()
        
        keywords = []
        important_patterns = [
            '波特率', 'baud', '数据位', 'databit', '校验', 'parity',
            'fifo', '寄存器', 'register', '中断', 'interrupt',
            '时钟', 'clock', '复位', 'reset', 'cdc',
            '功耗', 'power', '时序', 'timing'
        ]
        
        for pattern in important_patterns:
            if pattern.lower() in text:
                keywords.append(pattern)
        
        return keywords
    
    def compare_specs(self, spec_name: str, version1: str, version2: str) -> Dict:
        """对比两个版本的Spec"""
        # 这里简化处理，实际应该从版本存储中读取
        return {
            'spec': spec_name,
            'version1': version1,
            'version2': version2,
            'changes': [],
            'impact': 'unknown'
        }
    
    def track_change(self, spec_name: str, old_content: str, 
                     new_content: str, author: str) -> SpecChange:
        """追踪变更"""
        # 计算diff
        differ = difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            lineterm=''
        )
        
        changes = []
        for line in differ:
            if line.startswith('+') and not line.startswith('+++'):
                changes.append({'type': 'add', 'content': line[1:].strip()})
            elif line.startswith('-') and not line.startswith('---'):
                changes.append({'type': 'remove', 'content': line[1:].strip()})
        
        # 分析影响
        impact_modules = self._analyze_impact(changes)
        
        # 生成版本号
        versions_file = self._get_versions_file(spec_name)
        version_num = "1.0"
        if os.path.exists(versions_file):
            with open(versions_file, 'r') as f:
                versions = json.load(f)
                if versions:
                    last_ver = versions[-1]['version']
                    parts = last_ver.split('.')
                    version_num = f"{parts[0]}.{int(parts[1]) + 1}"
        
        change = SpecChange(
            id=f"{spec_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            version=version_num,
            timestamp=datetime.now().isoformat(),
            author=author,
            changes=changes,
            affected_sections=self._find_affected_sections(changes),
            impact_modules=impact_modules
        )
        
        # 保存版本
        versions = []
        if os.path.exists(versions_file):
            with open(versions_file, 'r') as f:
                versions = json.load(f)
        
        versions.append(change.__dict__)
        
        with open(versions_file, 'w') as f:
            json.dump(versions, f, indent=2)
        
        return change
    
    def _analyze_impact(self, changes: List[Dict]) -> List[str]:
        """分析变更影响"""
        impact_modules = set()
        
        for change in changes:
            content = change.get('content', '').lower()
            
            # 简单关键词匹配
            if any(k in content for k in ['uart', 'tx', 'rx', '串口']):
                impact_modules.add('uart')
            if any(k in content for k in ['fifo', '队列']):
                impact_modules.add('fifo')
            if any(k in content for k in ['clock', 'clk', '时钟']):
                impact_modules.add('clock_domain')
            if any(k in content for k in ['reset', 'rst', '复位']):
                impact_modules.add('reset')
            if any(k in content for k in ['cdc', 'cross']):
                impact_modules.add('cdc')
        
        return list(impact_modules)
    
    def _find_affected_sections(self, changes: List[Dict]) -> List[str]:
        """找出受影响的章节"""
        # 简化处理：返回变更涉及的关键词
        sections = []
        for change in changes:
            content = change.get('content', '')
            # 简单提取章节名
            for word in content.split():
                if len(word) > 3 and word[0].isupper():
                    sections.append(word)
        return list(set(sections))[:10]
    
    def get_change_history(self, spec_name: str) -> List[Dict]:
        """获取变更历史"""
        versions_file = self._get_versions_file(spec_name)
        if not os.path.exists(versions_file):
            return []
        
        with open(versions_file, 'r') as f:
            return json.load(f)
    
    def generate_impact_report(self, change: SpecChange) -> str:
        """生成影响分析报告"""
        lines = []
        lines.append("# Spec变更影响分析报告\n")
        lines.append(f"**Spec**: {change.id}")
        lines.append(f"**版本**: {change.version}")
        lines.append(f"**时间**: {change.timestamp}")
        lines.append(f"**作者**: {change.author}\n")
        
        lines.append("## 变更摘要")
        lines.append(f"- 新增: {sum(1 for c in change.changes if c['type'] == 'add')}")
        lines.append(f"- 删除: {sum(1 for c in change.changes if c['type'] == 'remove')}\n")
        
        lines.append("## 影响模块")
        if change.impact_modules:
            for m in change.impact_modules:
                lines.append(f"- [ ] {m}")
        else:
            lines.append("无明显影响模块")
        
        lines.append("\n## 受影响章节")
        if change.affected_sections:
            for s in change.affected_sections:
                lines.append(f"- {s}")
        else:
            lines.append("无")
        
        lines.append("\n## 建议行动")
        lines.append("1. 通知相关模块负责人")
        lines.append("2. 更新对应的验证计划")
        lines.append("3. 审查RTL实现是否受影响")
        
        return '\n'.join(lines)
