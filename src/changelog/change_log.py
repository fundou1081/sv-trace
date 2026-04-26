"""
ChangeLog - 变更日志系统
记录设计变更、规格变更、代码变更，支持追踪和检索
"""
import os
import json
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass, field

@dataclass
class ChangeEntry:
    """变更条目"""
    id: str
    type: str  # spec/rtl/doc/test/config
    category: str  # feature/bugfix/refactor/docs
    title: str
    description: str
    author: str
    timestamp: str
    files: List[str] = field(default_factory=list)
    commits: List[str] = field(default_factory=list)
    related_issues: List[str] = field(default_factory=list)
    impact: str = ""  # low/medium/high
    status: str = "open"  # open/merged/closed

class ChangeLogManager:
    """变更日志管理器"""
    
    def __init__(self, db_path: str = "./change_db"):
        self.db_path = db_path
        self._ensure_db()
    
    def _ensure_db(self):
        os.makedirs(self.db_path, exist_ok=True)
    
    def _get_file(self) -> str:
        return os.path.join(self.db_path, "changes.json")
    
    def _load(self) -> List[ChangeEntry]:
        filepath = self._get_file()
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r') as f:
            data = json.load(f)
            return [ChangeEntry(**e) for e in data]
    
    def _save(self, entries: List[ChangeEntry]):
        filepath = self._get_file()
        with open(filepath, 'w') as f:
            json.dump([e.__dict__ for e in entries], f, indent=2)
    
    def add_change(self, change_type: str, category: str, title: str,
                   description: str, author: str,
                   files: List[str] = None,
                   commits: List[str] = None,
                   related_issues: List[str] = None,
                   impact: str = "medium") -> ChangeEntry:
        """添加变更条目"""
        entries = self._load()
        
        # 生成ID
        max_id = 0
        for e in entries:
            try:
                num = int(e.id.split('-')[1])
                max_id = max(max_id, num)
            except:
                pass
        
        entry = ChangeEntry(
            id=f"CHG-{max_id + 1:04d}",
            type=change_type,
            category=category,
            title=title,
            description=description,
            author=author,
            timestamp=datetime.now().isoformat(),
            files=files or [],
            commits=commits or [],
            related_issues=related_issues or [],
            impact=impact
        )
        
        entries.append(entry)
        self._save(entries)
        
        return entry
    
    def list_changes(self, change_type: str = None,
                     category: str = None,
                     author: str = None,
                     status: str = None,
                     limit: int = 50) -> List[ChangeEntry]:
        """列出变更"""
        entries = self._load()
        
        results = entries
        if change_type:
            results = [e for e in results if e.type == change_type]
        if category:
            results = [e for e in results if e.category == category]
        if author:
            results = [e for e in results if e.author == author]
        if status:
            results = [e for e in results if e.status == status]
        
        # 按时间倒序
        results.sort(key=lambda x: x.timestamp, reverse=True)
        
        return results[:limit]
    
    def get_change(self, change_id: str) -> Optional[ChangeEntry]:
        """获取变更详情"""
        entries = self._load()
        for e in entries:
            if e.id == change_id:
                return e
        return None
    
    def update_status(self, change_id: str, status: str) -> bool:
        """更新状态"""
        entries = self._load()
        for e in entries:
            if e.id == change_id:
                e.status = status
                self._save(entries)
                return True
        return False
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        entries = self._load()
        
        by_type = {}
        by_category = {}
        by_author = {}
        by_status = {}
        
        for e in entries:
            by_type[e.type] = by_type.get(e.type, 0) + 1
            by_category[e.category] = by_category.get(e.category, 0) + 1
            by_author[e.author] = by_author.get(e.author, 0) + 1
            by_status[e.status] = by_status.get(e.status, 0) + 1
        
        return {
            'total': len(entries),
            'by_type': by_type,
            'by_category': by_category,
            'by_author': by_author,
            'by_status': by_status
        }
    
    def get_changelog(self, since: str = None, until: str = None) -> str:
        """生成变更日志文本"""
        entries = self.list_changes(limit=100)
        
        lines = ["# 变更日志\n"]
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        if since:
            lines.append(f"起始时间: {since}\n")
        if until:
            lines.append(f"截止时间: {until}\n")
        
        lines.append("\n## 变更列表\n")
        
        # 按类型分组
        by_type = {}
        for e in entries:
            if e.type not in by_type:
                by_type[e.type] = []
            by_type[e.type].append(e)
        
        for change_type, changes in by_type.items():
            lines.append(f"\n### {change_type.upper()}\n")
            
            for c in changes:
                lines.append(f"- **[{c.id}]** {c.title}")
                lines.append(f"  - 作者: {c.author}")
                lines.append(f"  - 时间: {c.timestamp[:10]}")
                lines.append(f"  - 分类: {c.category}")
                lines.append(f"  - 影响: {c.impact}")
                if c.files:
                    lines.append(f"  - 文件: {', '.join(c.files[:3])}")
                lines.append("")
        
        return "\n".join(lines)
    
    def link_to_bug(self, change_id: str, bug_id: str) -> bool:
        """关联变更到Bug"""
        entries = self._load()
        for e in entries:
            if e.id == change_id:
                if bug_id not in e.related_issues:
                    e.related_issues.append(bug_id)
                    self._save(entries)
                return True
        return False
    
    def link_to_spec(self, change_id: str, spec_ref: str) -> bool:
        """关联变更到Spec章节"""
        entries = self._load()
        for e in entries:
            if e.id == change_id:
                if spec_ref not in e.related_issues:
                    e.related_issues.append(spec_ref)
                    self._save(entries)
                return True
        return False
