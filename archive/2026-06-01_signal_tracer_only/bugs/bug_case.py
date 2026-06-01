"""
BugCase - Bug追踪数据模型
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum
import json

class BugSeverity(Enum):
    CRITICAL = "critical"  # 导致芯片不工作
    HIGH = "high"          # 功能不正确
    MEDIUM = "medium"      # 性能或体验问题
    LOW = "low"           # 轻微问题

class BugStatus(Enum):
    NEW = "new"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    FIXED = "fixed"
    CLOSED = "closed"
    WONTFIX = "wontfix"

class BugReproducibility(Enum):
    ALWAYS = "always"      # 100%复现
    USUAL = "usual"        # >50%复现
    SOMETIMES = "sometimes" # 10-50%复现
    RARE = "rare"          # <10%复现
    UNKNOWN = "unknown"

@dataclass
class BugCase:
    """Bug用例"""
    id: str
    title: str
    severity: BugSeverity
    status: BugStatus
    module: str
    
    # 详情
    description: str = ""
    reproduce_steps: str = ""
    expected: str = ""
    actual: str = ""
    
    # 关联
    test_case_id: Optional[str] = None
    related_spec: str = ""
    related_bugs: List[str] = field(default_factory=list)
    related_files: List[str] = field(default_factory=list)
    
    # 复现信息
    reproducibility: BugReproducibility = BugReproducibility.UNKNOWN
    reproduce_count: int = 0
    reproduce_rate: float = 0.0
    seed: Optional[str] = None
    
    # 时间
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # 人员
    reporter: str = ""
    assignee: str = ""
    owner: str = ""
    
    # 附件
    waveforms: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    screenshots: List[str] = field(default_factory=list)
    
    # 标签
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'severity': self.severity.value,
            'status': self.status.value,
            'module': self.module,
            'description': self.description,
            'reproduce_steps': self.reproduce_steps,
            'expected': self.expected,
            'actual': self.actual,
            'test_case_id': self.test_case_id,
            'related_spec': self.related_spec,
            'related_bugs': self.related_bugs,
            'related_files': self.related_files,
            'reproducibility': self.reproducibility.value,
            'reproduce_count': self.reproduce_count,
            'reproduce_rate': self.reproduce_rate,
            'seed': self.seed,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'reporter': self.reporter,
            'assignee': self.assignee,
            'owner': self.owner,
            'waveforms': self.waveforms,
            'logs': self.logs,
            'screenshots': self.screenshots,
            'tags': self.tags,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'BugCase':
        data['severity'] = BugSeverity(data['severity'])
        data['status'] = BugStatus(data['status'])
        data['reproducibility'] = BugReproducibility(data.get('reproducibility', 'unknown'))
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if data.get('resolved_at'):
            data['resolved_at'] = datetime.fromisoformat(data['resolved_at'])
        if data.get('closed_at'):
            data['closed_at'] = datetime.fromisoformat(data['closed_at'])
        return cls(**data)

@dataclass
class BugComment:
    """Bug评论/备注"""
    id: str
    bug_id: str
    author: str
    content: str
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'bug_id': self.bug_id,
            'author': self.author,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'BugComment':
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)

@dataclass
class BugReproduceAttempt:
    """Bug复现尝试"""
    bug_id: str
    seed: str
    attempt_count: int
    success_count: int
    duration_ms: int
    notes: str = ""
    attempted_at: datetime = field(default_factory=datetime.now)
    
    @property
    def success_rate(self) -> float:
        if self.attempt_count == 0:
            return 0.0
        return self.success_count / self.attempt_count * 100
    
    def to_dict(self) -> dict:
        return {
            'bug_id': self.bug_id,
            'seed': self.seed,
            'attempt_count': self.attempt_count,
            'success_count': self.success_count,
            'duration_ms': self.duration_ms,
            'notes': self.notes,
            'attempted_at': self.attempted_at.isoformat(),
        }
