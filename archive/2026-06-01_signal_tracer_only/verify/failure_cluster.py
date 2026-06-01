"""
FailureCluster - 失败用例聚类
将相似的失败用例自动归类
"""
from typing import List, Dict
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class FailureCase:
    """失败用例"""
    test_id: str
    test_name: str
    error_type: str
    error_message: str
    file: str
    line: int = 0

@dataclass
class FailureCluster:
    """失败聚类"""
    cluster_id: str
    error_type: str
    cases: List[FailureCase]
    root_cause: str = ""

class FailureClusterer:
    """失败用例聚类器"""
    
    def __init__(self):
        self.clusters = []
    
    def cluster(self, failures: List[FailureCase]) -> List[FailureCluster]:
        """对失败用例聚类"""
        # 按错误类型分组
        by_type = defaultdict(list)
        for f in failures:
            by_type[f.error_type].append(f)
        
        # 生成聚类
        clusters = []
        for i, (error_type, cases) in enumerate(by_type.items()):
            cluster = FailureCluster(
                cluster_id=f"cluster_{i+1}",
                error_type=error_type,
                cases=cases,
                root_cause=self._infer_root_cause(error_type)
            )
            clusters.append(cluster)
        
        self.clusters = clusters
        return clusters
    
    def _infer_root_cause(self, error_type: str) -> str:
        """推断根本原因"""
        root_causes = {
            'timeout': '可能是死锁或无限等待',
            'assertion': '可能是设计逻辑错误',
            'data_mismatch': '可能是数据处理错误',
            'cdc': '可能是跨时钟域问题',
            'x_propagation': '可能是信号未初始化',
        }
        
        for key, cause in root_causes.items():
            if key in error_type.lower():
                return cause
        
        return '需要进一步分析'
    
    def generate_report(self) -> str:
        """生成聚类报告"""
        lines = []
        lines.append("# 失败用例聚类报告")
        lines.append("")
        lines.append(f"总聚类数: {len(self.clusters)}")
        lines.append("")
        
        for cluster in self.clusters:
            lines.append(f"## {cluster.cluster_id}: {cluster.error_type}")
            lines.append(f"- 失败数: {len(cluster.cases)}")
            lines.append(f"- 可能原因: {cluster.root_cause}")
            lines.append("- 受影响测试:")
            for c in cluster.cases[:5]:
                lines.append(f"  - {c.test_name} ({c.file}:{c.line})")
            lines.append("")
        
        return '\n'.join(lines)
