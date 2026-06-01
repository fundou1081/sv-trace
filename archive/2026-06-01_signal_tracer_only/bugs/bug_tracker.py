"""
BugTracker - Bug追踪核心
提供Bug的全生命周期管理
"""
import os
import json
from typing import List, Dict, Optional
from datetime import datetime
from .bug_case import BugCase, BugComment, BugReproduceAttempt, BugSeverity, BugStatus, BugReproducibility

class BugTracker:
    """Bug追踪器"""
    
    def __init__(self, db_path: str = "./bug_db"):
        self.db_path = db_path
        self._ensure_db()
    
    def _ensure_db(self):
        """确保数据库目录存在"""
        os.makedirs(self.db_path, exist_ok=True)
        os.makedirs(os.path.join(self.db_path, "comments"), exist_ok=True)
        os.makedirs(os.path.join(self.db_path, "reproduce"), exist_ok=True)
        os.makedirs(os.path.join(self.db_path, "attachments"), exist_ok=True)
    
    def _get_bugs_file(self) -> str:
        return os.path.join(self.db_path, "bugs.json")
    
    def _get_comments_file(self, bug_id: str) -> str:
        return os.path.join(self.db_path, "comments", f"{bug_id}.json")
    
    def _get_reproduce_file(self, bug_id: str) -> str:
        return os.path.join(self.db_path, "reproduce", f"{bug_id}.json")
    
    def _load_bugs(self) -> Dict[str, BugCase]:
        filepath = self._get_bugs_file()
        if not os.path.exists(filepath):
            return {}
        with open(filepath, 'r') as f:
            data = json.load(f)
            return {k: BugCase.from_dict(v) for k, v in data.items()}
    
    def _save_bugs(self, bugs: Dict[str, BugCase]):
        filepath = self._get_bugs_file()
        with open(filepath, 'w') as f:
            json.dump({k: v.to_dict() for k, v in bugs.items()}, f, indent=2)
    
    # ========== Bug CRUD ==========
    
    def create_bug(self, title: str, module: str, severity: str = "medium",
                   description: str = "", reporter: str = "",
                   test_case_id: str = None, tags: List[str] = None) -> BugCase:
        """创建Bug"""
        bugs = self._load_bugs()
        
        # 生成ID
        existing_ids = [int(k[1:]) for k in bugs.keys() if k.startswith('B')]
        new_id = f"B{max(existing_ids) + 1}" if existing_ids else "B1"
        
        bug = BugCase(
            id=new_id,
            title=title,
            severity=BugSeverity(severity),
            status=BugStatus.NEW,
            module=module,
            description=description,
            reporter=reporter,
            test_case_id=test_case_id,
            tags=tags or []
        )
        
        bugs[new_id] = bug
        self._save_bugs(bugs)
        
        return bug
    
    def get_bug(self, bug_id: str) -> Optional[BugCase]:
        """获取Bug"""
        bugs = self._load_bugs()
        return bugs.get(bug_id)
    
    def list_bugs(self, module: str = None, severity: str = None,
                  status: str = None, assignee: str = None,
                  tags: List[str] = None) -> List[BugCase]:
        """列出Bug (支持过滤)"""
        bugs = self._load_bugs()
        results = list(bugs.values())
        
        if module:
            results = [b for b in results if b.module == module]
        if severity:
            results = [b for b in results if b.severity.value == severity]
        if status:
            results = [b for b in results if b.status.value == status]
        if assignee:
            results = [b for b in results if b.assignee == assignee]
        if tags:
            results = [b for b in results if any(tag in b.tags for tag in tags)]
        
        # 按严重性排序
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        results.sort(key=lambda b: severity_order.get(b.severity.value, 4))
        
        return results
    
    def update_bug(self, bug_id: str, **kwargs) -> Optional[BugCase]:
        """更新Bug"""
        bugs = self._load_bugs()
        if bug_id not in bugs:
            return None
        
        bug = bugs[bug_id]
        
        for key, value in kwargs.items():
            if hasattr(bug, key):
                if key == 'severity' and isinstance(value, str):
                    value = BugSeverity(value)
                elif key == 'status' and isinstance(value, str):
                    value = BugStatus(value)
                elif key == 'reproducibility' and isinstance(value, str):
                    value = BugReproducibility(value)
                setattr(bug, key, value)
        
        bug.updated_at = datetime.now()
        
        # 更新状态时间
        if bug.status == BugStatus.FIXED and not bug.resolved_at:
            bug.resolved_at = datetime.now()
        elif bug.status == BugStatus.CLOSED and not bug.closed_at:
            bug.closed_at = datetime.now()
        
        bugs[bug_id] = bug
        self._save_bugs(bugs)
        
        return bug
    
    def close_bug(self, bug_id: str, reason: str = "wontfix") -> Optional[BugCase]:
        """关闭Bug"""
        return self.update_bug(bug_id, status=reason)
    
    def delete_bug(self, bug_id: str) -> bool:
        """删除Bug"""
        bugs = self._load_bugs()
        if bug_id in bugs:
            del bugs[bug_id]
            self._save_bugs(bugs)
            
            # 删除关联文件
            for subdir in ['comments', 'reproduce']:
                filepath = os.path.join(self.db_path, subdir, f"{bug_id}.json")
                if os.path.exists(filepath):
                    os.remove(filepath)
            
            return True
        return False
    
    # ========== Comments ==========
    
    def add_comment(self, bug_id: str, author: str, content: str) -> BugComment:
        """添加评论"""
        filepath = self._get_comments_file(bug_id)
        
        comments = []
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                comments = [BugComment.from_dict(c) for c in json.load(f)]
        
        # 生成ID
        new_id = f"{bug_id}_c{len(comments) + 1}"
        
        comment = BugComment(
            id=new_id,
            bug_id=bug_id,
            author=author,
            content=content
        )
        
        comments.append(comment)
        
        with open(filepath, 'w') as f:
            json.dump([c.to_dict() for c in comments], f, indent=2)
        
        # 更新bug的updated_at
        self.update_bug(bug_id, updated_at=datetime.now())
        
        return comment
    
    def get_comments(self, bug_id: str) -> List[BugComment]:
        """获取Bug的所有评论"""
        filepath = self._get_comments_file(bug_id)
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r') as f:
            data = json.load(f)
            return [BugComment.from_dict(c) for c in data]
    
    # ========== Reproduce ==========
    
    def record_reproduce(self, bug_id: str, seed: str, attempt_count: int,
                        success_count: int, duration_ms: int,
                        notes: str = "") -> BugReproduceAttempt:
        """记录复现尝试"""
        attempt = BugReproduceAttempt(
            bug_id=bug_id,
            seed=seed,
            attempt_count=attempt_count,
            success_count=success_count,
            duration_ms=duration_ms,
            notes=notes
        )
        
        filepath = self._get_reproduce_file(bug_id)
        
        attempts = []
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                attempts = json.load(f)
        
        attempts.append(attempt.to_dict())
        
        with open(filepath, 'w') as f:
            json.dump(attempts, f, indent=2)
        
        # 更新Bug的复现统计
        bug = self.get_bug(bug_id)
        if bug:
            bug.reproduce_count += attempt_count
            if attempt_count > 0:
                bug.reproduce_rate = sum(a['success_count'] for a in attempts) / sum(a['attempt_count'] for a in attempts) * 100
            if bug.reproduce_rate > 0:
                if bug.reproduce_rate >= 90:
                    bug.reproducibility = BugReproducibility.ALWAYS
                elif bug.reproduce_rate >= 50:
                    bug.reproducibility = BugReproducibility.USUAL
                elif bug.reproduce_rate >= 10:
                    bug.reproducibility = BugReproducibility.SOMETIMES
                else:
                    bug.reproducibility = BugReproducibility.RARE
            self.update_bug(bug_id, reproduce_count=bug.reproduce_count,
                          reproduce_rate=bug.reproduce_rate,
                          reproducibility=bug.reproducibility.value,
                          seed=seed)
        
        return attempt
    
    def get_reproduce_history(self, bug_id: str) -> List[BugReproduceAttempt]:
        """获取复现历史"""
        filepath = self._get_reproduce_file(bug_id)
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r') as f:
            data = json.load(f)
            return [BugReproduceAttempt(**a) for a in data]
    
    # ========== Statistics ==========
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        bugs = self._load_bugs()
        
        severity_counts = {}
        status_counts = {}
        module_counts = {}
        assignee_counts = {'unassigned': 0}
        
        for bug in bugs.values():
            severity_counts[bug.severity.value] = severity_counts.get(bug.severity.value, 0) + 1
            status_counts[bug.status.value] = status_counts.get(bug.status.value, 0) + 1
            module_counts[bug.module] = module_counts.get(bug.module, 0) + 1
            
            if bug.assignee:
                assignee_counts[bug.assignee] = assignee_counts.get(bug.assignee, 0) + 1
            else:
                assignee_counts['unassigned'] += 1
        
        # 计算平均解决时间
        resolved_bugs = [b for b in bugs.values() if b.resolved_at]
        avg_resolve_days = 0
        if resolved_bugs:
            total_days = sum((b.resolved_at - b.created_at).days for b in resolved_bugs)
            avg_resolve_days = total_days / len(resolved_bugs)
        
        return {
            'total_bugs': len(bugs),
            'severity_counts': severity_counts,
            'status_counts': status_counts,
            'module_counts': module_counts,
            'assignee_counts': assignee_counts,
            'avg_resolve_days': round(avg_resolve_days, 1),
            'open_bugs': sum(1 for b in bugs.values() if b.status not in [BugStatus.CLOSED, BugStatus.WONTFIX]),
            'critical_bugs': severity_counts.get('critical', 0),
        }
