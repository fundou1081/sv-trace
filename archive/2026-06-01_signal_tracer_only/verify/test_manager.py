"""
TestManager - 测试用例管理核心
提供测试用例的增删改查能力
"""
import os
import json
from typing import List, Dict, Optional
from datetime import datetime
from .test_case import TestCase, TestSuite, TestResult, TestLevel, TestStatus

class TestManager:
    """测试用例管理器"""
    
    def __init__(self, db_path: str = "./test_db"):
        self.db_path = db_path
        self._ensure_db()
    
    def _ensure_db(self):
        """确保数据库目录存在"""
        os.makedirs(self.db_path, exist_ok=True)
        os.makedirs(os.path.join(self.db_path, "results"), exist_ok=True)
    
    def _get_tests_file(self) -> str:
        return os.path.join(self.db_path, "tests.json")
    
    def _get_suites_file(self) -> str:
        return os.path.join(self.db_path, "suites.json")
    
    def _load_tests(self) -> Dict[str, TestCase]:
        """加载测试用例"""
        filepath = self._get_tests_file()
        if not os.path.exists(filepath):
            return {}
        
        with open(filepath, 'r') as f:
            data = json.load(f)
            return {k: TestCase.from_dict(v) for k, v in data.items()}
    
    def _save_tests(self, tests: Dict[str, TestCase]):
        """保存测试用例"""
        filepath = self._get_tests_file()
        with open(filepath, 'w') as f:
            json.dump({k: v.to_dict() for k, v in tests.items()}, f, indent=2)
    
    def _load_suites(self) -> Dict[str, TestSuite]:
        """加载测试套件"""
        filepath = self._get_suites_file()
        if not os.path.exists(filepath):
            return {}
        
        with open(filepath, 'r') as f:
            data = json.load(f)
            return {k: TestSuite.from_dict(v) for k, v in data.items()}
    
    def _save_suites(self, suites: Dict[str, TestSuite]):
        """保存测试套件"""
        filepath = self._get_suites_file()
        with open(filepath, 'w') as f:
            json.dump({k: v.to_dict() for k, v in suites.items()}, f, indent=2)
    
    # ========== Test CRUD ==========
    
    def add_test(self, name: str, module: str, level: str = "P1", 
                 description: str = "", owner: str = "", 
                 tags: List[str] = None) -> TestCase:
        """添加测试用例"""
        tests = self._load_tests()
        
        # 生成ID
        existing_ids = [int(k) for k in tests.keys() if k.isdigit()]
        new_id = str(max(existing_ids) + 1) if existing_ids else "1"
        
        # 创建测试用例
        test = TestCase(
            id=new_id,
            name=name,
            module=module,
            level=TestLevel(level),
            description=description,
            owner=owner,
            tags=tags or []
        )
        
        tests[new_id] = test
        self._save_tests(tests)
        
        return test
    
    def get_test(self, test_id: str) -> Optional[TestCase]:
        """获取测试用例"""
        tests = self._load_tests()
        return tests.get(test_id)
    
    def list_tests(self, module: str = None, level: str = None,
                   status: str = None, owner: str = None,
                   tags: List[str] = None) -> List[TestCase]:
        """列出测试用例 (支持过滤)"""
        tests = self._load_tests()
        results = list(tests.values())
        
        if module:
            results = [t for t in results if t.module == module]
        if level:
            results = [t for t in results if t.level.value == level]
        if status:
            results = [t for t in results if t.status.value == status]
        if owner:
            results = [t for t in results if t.owner == owner]
        if tags:
            results = [t for t in results if any(tag in t.tags for tag in tags)]
        
        return results
    
    def update_test(self, test_id: str, **kwargs) -> Optional[TestCase]:
        """更新测试用例"""
        tests = self._load_tests()
        if test_id not in tests:
            return None
        
        test = tests[test_id]
        
        # 更新字段
        for key, value in kwargs.items():
            if hasattr(test, key):
                if key == 'level' and isinstance(value, str):
                    value = TestLevel(value)
                elif key == 'status' and isinstance(value, str):
                    value = TestStatus(value)
                setattr(test, key, value)
        
        test.updated_at = datetime.now()
        tests[test_id] = test
        self._save_tests(tests)
        
        return test
    
    def remove_test(self, test_id: str) -> bool:
        """删除测试用例"""
        tests = self._load_tests()
        if test_id in tests:
            del tests[test_id]
            self._save_tests(tests)
            return True
        return False
    
    # ========== TestSuite CRUD ==========
    
    def create_suite(self, name: str, test_ids: List[str] = None,
                     description: str = "") -> TestSuite:
        """创建测试套件"""
        suites = self._load_suites()
        
        # 生成ID
        existing_ids = [int(k[1:]) for k in suites.keys() if k.startswith('s')]
        new_id = f"s{max(existing_ids) + 1}" if existing_ids else "s1"
        
        suite = TestSuite(
            id=new_id,
            name=name,
            test_ids=test_ids or [],
            description=description
        )
        
        suites[new_id] = suite
        self._save_suites(suites)
        
        return suite
    
    def get_suite(self, suite_id: str) -> Optional[TestSuite]:
        """获取测试套件"""
        suites = self._load_suites()
        return suites.get(suite_id)
    
    def list_suites(self) -> List[TestSuite]:
        """列出所有测试套件"""
        suites = self._load_suites()
        return list(suites.values())
    
    def add_test_to_suite(self, suite_id: str, test_id: str) -> bool:
        """添加测试到套件"""
        suites = self._load_suites()
        if suite_id not in suites:
            return False
        
        suite = suites[suite_id]
        if test_id not in suite.test_ids:
            suite.test_ids.append(test_id)
            suite.updated_at = datetime.now()
            self._save_suites(suites)
        
        return True
    
    def remove_test_from_suite(self, suite_id: str, test_id: str) -> bool:
        """从套件移除测试"""
        suites = self._load_suites()
        if suite_id not in suites:
            return False
        
        suite = suites[suite_id]
        if test_id in suite.test_ids:
            suite.test_ids.remove(test_id)
            suite.updated_at = datetime.now()
            self._save_suites(suites)
        
        return True
    
    def remove_suite(self, suite_id: str) -> bool:
        """删除测试套件"""
        suites = self._load_suites()
        if suite_id in suites:
            del suites[suite_id]
            self._save_suites(suites)
            return True
        return False
    
    # ========== Results ==========
    
    def record_result(self, test_id: str, status: str, 
                     duration_ms: int = 0, seed: str = None,
                     log: str = "", error_msg: str = "") -> TestResult:
        """记录测试结果"""
        result = TestResult(
            test_id=test_id,
            status=TestStatus(status),
            duration_ms=duration_ms,
            seed=seed,
            log=log,
            error_msg=error_msg
        )
        
        # 保存结果
        results_dir = os.path.join(self.db_path, "results")
        filepath = os.path.join(results_dir, f"{test_id}.json")
        
        # 追加到历史
        history = []
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                history = json.load(f)
        
        history.append(result.to_dict())
        
        with open(filepath, 'w') as f:
            json.dump(history, f, indent=2)
        
        # 更新测试状态
        self.update_test(test_id, status=status, last_run=datetime.now(),
                        run_count=(self.get_test(test_id).run_count or 0) + 1)
        
        return result
    
    def get_test_results(self, test_id: str) -> List[TestResult]:
        """获取测试历史结果"""
        results_dir = os.path.join(self.db_path, "results")
        filepath = os.path.join(results_dir, f"{test_id}.json")
        
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r') as f:
            data = json.load(f)
            return [TestResult.from_dict(r) for r in data]
    
    # ========== Statistics ==========
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        tests = self._load_tests()
        suites = self._load_suites()
        
        status_counts = {}
        level_counts = {}
        module_counts = {}
        
        for test in tests.values():
            status_counts[test.status.value] = status_counts.get(test.status.value, 0) + 1
            level_counts[test.level.value] = level_counts.get(test.level.value, 0) + 1
            module_counts[test.module] = module_counts.get(test.module, 0) + 1
        
        return {
            'total_tests': len(tests),
            'total_suites': len(suites),
            'status_counts': status_counts,
            'level_counts': level_counts,
            'module_counts': module_counts,
        }
