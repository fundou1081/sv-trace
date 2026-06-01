"""
SeedManager - 随机种子管理系统
记录和管理随机种子，便于问题复现
"""
import os
import json
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class SeedRecord:
    """种子记录"""
    seed: str
    timestamp: str
    test_name: str
    result: str  # pass/fail
    notes: str = ""

class SeedManager:
    """种子管理器"""
    
    def __init__(self, db_path: str = "./seed_db"):
        self.db_path = db_path
        os.makedirs(db_path, exist_ok=True)
        self._db_file = os.path.join(db_path, "seeds.json")
    
    def _load(self) -> Dict:
        if not os.path.exists(self._db_file):
            return {}
        with open(self._db_file, 'r') as f:
            return json.load(f)
    
    def _save(self, data: Dict):
        with open(self._db_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def record(self, seed: str, test_name: str, result: str, notes: str = "") -> SeedRecord:
        """记录种子"""
        record = SeedRecord(
            seed=seed,
            timestamp=datetime.now().isoformat(),
            test_name=test_name,
            result=result,
            notes=notes
        )
        
        data = self._load()
        if test_name not in data:
            data[test_name] = []
        data[test_name].append(record.__dict__)
        self._save(data)
        
        return record
    
    def get_seeds(self, test_name: str, result: str = None) -> List[SeedRecord]:
        """获取测试的种子"""
        data = self._load()
        records = data.get(test_name, [])
        
        if result:
            records = [r for r in records if r['result'] == result]
        
        return [SeedRecord(**r) for r in records]
    
    def find_failed_seeds(self) -> List[SeedRecord]:
        """找出失败的种子"""
        all_records = []
        data = self._load()
        
        for test_name, records in data.items():
            for r in records:
                if r['result'] == 'fail':
                    all_records.append(SeedRecord(**r))
        
        return all_records
    
    def reproduce_with_seed(self, test_name: str, seed: str) -> bool:
        """使用指定种子复现测试"""
        # TODO: 调用仿真器执行
        return True
