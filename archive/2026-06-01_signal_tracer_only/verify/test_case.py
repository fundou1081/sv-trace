"""
TestCase - 测试用例数据模型
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum
import json

class TestLevel(Enum):
    """测试级别"""
    P0 = "P0"   # 核心功能
    P1 = "P1"   # 重要功能
    P2 = "P2"   # 一般功能

class TestStatus(Enum):
    """测试状态"""
    NOT_RUN = "not_run"
    PASS = "pass"
    FAIL = "fail"
    BLOCKED = "blocked"
    SKIPPED = "skipped"

@dataclass
class TestCase:
    """测试用例"""
    id: str
    name: str
    module: str
    level: TestLevel
    status: TestStatus = TestStatus.NOT_RUN
    
    # 元数据
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # 归属
    owner: str = ""
    tags: List[str] = field(default_factory=list)
    
    # 覆盖
    coverage_items: List[str] = field(default_factory=list)
    
    # 关联
    related_bugs: List[str] = field(default_factory=list)
    related_spec: str = ""
    
    # 运行信息
    seed: Optional[str] = None
    last_run: Optional[datetime] = None
    run_count: int = 0
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'module': self.module,
            'level': self.level.value,
            'status': self.status.value,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'owner': self.owner,
            'tags': self.tags,
            'coverage_items': self.coverage_items,
            'related_bugs': self.related_bugs,
            'related_spec': self.related_spec,
            'seed': self.seed,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'run_count': self.run_count,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TestCase':
        data['level'] = TestLevel(data['level'])
        data['status'] = TestStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        data['last_run'] = datetime.fromisoformat(data['last_run']) if data.get('last_run') else None
        return cls(**data)

@dataclass 
class TestSuite:
    """测试套件"""
    id: str
    name: str
    test_ids: List[str] = field(default_factory=list)
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'test_ids': self.test_ids,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TestSuite':
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)

@dataclass
class TestResult:
    """单次测试结果"""
    test_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    status: TestStatus = TestStatus.NOT_RUN
    duration_ms: int = 0
    seed: Optional[str] = None
    log: str = ""
    error_msg: str = ""
    
    def to_dict(self) -> dict:
        return {
            'test_id': self.test_id,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status.value,
            'duration_ms': self.duration_ms,
            'seed': self.seed,
            'log': self.log,
            'error_msg': self.error_msg,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TestResult':
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['status'] = TestStatus(data['status'])
        return cls(**data)
