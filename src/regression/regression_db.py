"""
RegressionDatabase - 回归测试结果数据库
记录每次回归测试的结果，支持历史追踪和对比
"""
import os
import json
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass, field

@dataclass
class RegressionResult:
    """单次回归结果"""
    id: str
    run_id: str
    timestamp: str
    total_tests: int
    passed: int
    failed: int
    blocked: int
    skipped: int
    duration_ms: int
    pass_rate: float
    tags: List[str] = field(default_factory=list)
    config: str = ""
    notes: str = ""

@dataclass
class TestRunResult:
    """单个测试运行结果"""
    test_id: str
    test_name: str
    status: str  # pass/fail/blocked
    duration_ms: int = 0
    seed: str = ""
    error_msg: str = ""
    stdout: str = ""
    stderr: str = ""

class RegressionDatabase:
    """回归结果数据库"""
    
    def __init__(self, db_path: str = "./regression_db"):
        self.db_path = db_path
        self._ensure_db()
    
    def _ensure_db(self):
        os.makedirs(self.db_path, exist_ok=True)
        os.makedirs(os.path.join(self.db_path, "runs"), exist_ok=True)
    
    def _get_index_file(self) -> str:
        return os.path.join(self.db_path, "runs.json")
    
    def _get_run_file(self, run_id: str) -> str:
        return os.path.join(self.db_path, "runs", f"{run_id}.json")
    
    def _load_index(self) -> Dict:
        filepath = self._get_index_file()
        if not os.path.exists(filepath):
            return {'runs': [], 'latest': None}
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def _save_index(self, index: Dict):
        filepath = self._get_index_file()
        with open(filepath, 'w') as f:
            json.dump(index, f, indent=2)
    
    def record_run(self, run_id: str, test_results: List[TestRunResult],
                   total_tests: int, passed: int, failed: int,
                   blocked: int = 0, skipped: int = 0,
                   duration_ms: int = 0, tags: List[str] = None,
                   config: str = "", notes: str = "") -> RegressionResult:
        """记录一次回归运行"""
        timestamp = datetime.now().isoformat()
        
        result = RegressionResult(
            id=f"{run_id}_{timestamp}",
            run_id=run_id,
            timestamp=timestamp,
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            blocked=blocked,
            skipped=skipped,
            duration_ms=duration_ms,
            pass_rate=(passed / total_tests * 100) if total_tests > 0 else 0,
            tags=tags or [],
            config=config,
            notes=notes
        )
        
        # 保存运行结果
        run_data = {
            'summary': result.__dict__,
            'tests': [t.__dict__ for t in test_results]
        }
        
        with open(self._get_run_file(run_id), 'w') as f:
            json.dump(run_data, f, indent=2)
        
        # 更新索引
        index = self._load_index()
        index['runs'].append({
            'run_id': run_id,
            'timestamp': timestamp,
            'pass_rate': result.pass_rate,
            'total': total_tests,
            'passed': passed,
            'failed': failed
        })
        index['latest'] = run_id
        self._save_index(index)
        
        return result
    
    def get_run(self, run_id: str) -> Optional[RegressionResult]:
        """获取指定运行结果"""
        filepath = self._get_run_file(run_id)
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r') as f:
            data = json.load(f)
            return data['summary']
    
    def get_test_results(self, run_id: str) -> List[TestRunResult]:
        """获取运行的详细测试结果"""
        filepath = self._get_run_file(run_id)
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r') as f:
            data = json.load(f)
            return [TestRunResult(**t) for t in data['tests']]
    
    def list_runs(self, limit: int = 20) -> List[Dict]:
        """列出最近的运行"""
        index = self._load_index()
        runs = index.get('runs', [])[-limit:]
        return sorted(runs, key=lambda x: x['timestamp'], reverse=True)
    
    def compare_runs(self, run_id1: str, run_id2: str) -> Dict:
        """对比两次运行"""
        run1 = self.get_run(run_id1)
        run2 = self.get_run(run_id2)
        
        if not run1 or not run2:
            return {'error': 'Run not found'}
        
        results1 = {t.test_id: t for t in self.get_test_results(run_id1)}
        results2 = {t.test_id: t for t in self.get_test_results(run_id2)}
        
        # 找出差异
        new_failures = []
        fixed_failures = []
        still_failing = []
        
        all_tests = set(results1.keys()) | set(results2.keys())
        
        for test_id in all_tests:
            r1 = results1.get(test_id)
            r2 = results2.get(test_id)
            
            if r1 and r2:
                if r1.status == 'fail' and r2.status == 'pass':
                    fixed_failures.append(test_id)
                elif r1.status == 'pass' and r2.status == 'fail':
                    new_failures.append(test_id)
                elif r1.status == 'fail' and r2.status == 'fail':
                    still_failing.append(test_id)
            elif r2 and r2.status == 'fail':
                new_failures.append(test_id)
        
        return {
            'run1': run_id1,
            'run2': run_id2,
            'run1_pass_rate': run1['pass_rate'],
            'run2_pass_rate': run2['pass_rate'],
            'new_failures': new_failures,
            'fixed_failures': fixed_failures,
            'still_failing': still_failing,
            'summary': {
                'improved': len(fixed_failures) > 0,
                'regressed': len(new_failures) > 0,
                'delta': run2['pass_rate'] - run1['pass_rate']
            }
        }
    
    def get_trend(self, days: int = 30) -> Dict:
        """获取通过率趋势"""
        index = self._load_index()
        runs = index.get('runs', [])
        
        # 过滤最近的天数
        cutoff = datetime.now().timestamp() - (days * 86400)
        recent_runs = [r for r in runs if datetime.fromisoformat(r['timestamp']).timestamp() > cutoff]
        
        trend = [{
            'date': r['timestamp'][:10],
            'pass_rate': r['pass_rate'],
            'passed': r['passed'],
            'failed': r['failed']
        } for r in sorted(recent_runs, key=lambda x: x['timestamp'])]
        
        # 计算统计
        if trend:
            rates = [r['pass_rate'] for r in trend]
            avg_rate = sum(rates) / len(rates)
            min_rate = min(rates)
            max_rate = max(rates)
        else:
            avg_rate = min_rate = max_rate = 0
        
        return {
            'trend': trend,
            'statistics': {
                'average_pass_rate': avg_rate,
                'min_pass_rate': min_rate,
                'max_pass_rate': max_rate,
                'total_runs': len(trend)
            }
        }
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        index = self._load_index()
        runs = index.get('runs', [])
        
        if not runs:
            return {'total_runs': 0, 'latest': None}
        
        recent = runs[-10:]
        pass_rates = [r['pass_rate'] for r in recent]
        
        return {
            'total_runs': len(runs),
            'latest': index.get('latest'),
            'recent_avg_pass_rate': sum(pass_rates) / len(pass_rates) if pass_rates else 0,
            'recent_runs': len(recent)
        }
