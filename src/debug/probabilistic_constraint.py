"""Probabilistic Constraint Analysis - 寻找低概率×高影响组合

核心思路: 在依赖图上附加概率信息，找出"高影响×低概率"的危险组合
"""

import re
from typing import Dict, List, Set


class ProbabilisticConstraintAnalyzer:
    """概率约束分析器"""
    
    def __init__(self, constraints: Dict, dependencies: List):
        """
        Args:
            constraints: Dict[constraint_key -> ConstraintDetail]
            dependencies: List[ConstraintDependency]
        """
        self.constraints = constraints
        self.dependencies = dependencies
        self.probs = {}  # 约束激活概率
        self._estimate_all_probabilities()
    
    def _estimate_all_probabilities(self):
        """为每个约束估计激活概率"""
        for key, const in self.constraints.items():
            self.probs[key] = self._estimate_one(const)
    
    def _estimate_one(self, const) -> float:
        """基于约束类型和模式估计先验概率"""
        raw = const.raw_expression
        if not raw:
            return 0.5
        
        # Soft 约束 - 较低
        if const.is_soft:
            return 0.3
        
        # Inside 范围约束 - 范围越小概率越低
        if 'inside' in raw:
            ranges = re.findall(r'\[(\d+):(\d+)\]', raw)
            if ranges:
                total = sum(int(h) - int(l) + 1 for l, h in ranges)
                return min(0.5, total / 256)  # 假设8-bit
            return 0.1
        
        # 单一值比较
        if ' == ' in raw or ' != ' in raw:
            return 0.3
        
        # 数值比较
        if ' > ' in raw or ' < ' in raw or ' >= ' in raw or ' <= ' in raw:
            return 0.4
        
        # Implication - 被触发后才激活
        if const.constraint_type == 'implication':
            return 0.25
        
        return 0.5
    
    def analyze(self) -> Dict:
        """完整分析"""
        return {
            'rare_dependencies': self._find_rare_dependencies(),
            'danger_zones': self._find_danger_zones(),
            'rare_paths': self._find_rare_paths(),
            'critical_rare': self._find_critical_rare(),
        }
    
    def _find_rare_dependencies(self) -> List[Dict]:
        """找低概率依赖边 (P(A) × P(B) < threshold)"""
        rare = []
        for dep in self.dependencies:
            if dep.dependency_type == 'variable':
                p_a = self.probs.get(dep.from_constraint, 0.5)
                p_b = self.probs.get(dep.to_constraint, 0.5)
                joint = p_a * p_b
                
                if joint < 0.1:
                    rare.append({
                        'from': dep.from_constraint,
                        'to': dep.to_constraint,
                        'from_prob': round(p_a, 3),
                        'to_prob': round(p_b, 3),
                        'joint_prob': round(joint, 4),
                    })
        
        return sorted(rare, key=lambda x: x['joint_prob'])[:10]
    
    def _find_danger_zones(self) -> List[Dict]:
        """找危险区域 - 入度高但激活概率低"""
        in_degree = {}
        for dep in self.dependencies:
            in_degree[dep.to_constraint] = in_degree.get(dep.to_constraint, 0) + 1
        
        danger = []
        for const, degree in in_degree.items():
            if degree > 1:
                prob = self.probs.get(const, 0.5)
                risk_score = degree * (1 - prob)  # 高入度 × 低概率 = 高风险
                
                if risk_score > 0.5:
                    danger.append({
                        'constraint': const,
                        'in_degree': degree,
                        'activation_prob': prob,
                        'risk_score': round(risk_score, 3),
                    })
        
        return sorted(danger, key=lambda x: -x['risk_score'])[:10]
    
    def _find_rare_paths(self) -> List[Dict]:
        """找低概率长路径"""
        # 构建邻接表
        adj = {}
        for dep in self.dependencies:
            if dep.dependency_type == 'variable':
                p = self.probs.get(dep.from_constraint, 0.5)
                if dep.from_constraint not in adj:
                    adj[dep.from_constraint] = []
                adj[dep.from_constraint].append((dep.to_constraint, p))
        
        rare_paths = []
        
        def dfs(node, path, prob):
            if len(path) > 3:  # 路径太长
                return
            
            if prob < 0.05 and len(path) > 1:
                rare_paths.append({
                    'path': path.copy(),
                    'joint_prob': round(prob, 4),
                })
            
            for next_node, edge_p in adj.get(node, []):
                if next_node not in path:
                    new_prob = prob * edge_p
                    if new_prob < 0.1:
                        dfs(next_node, path + [next_node], new_prob)
        
        for start in self.probs:
            dfs(start, [start], self.probs[start])
        
        return sorted(rare_paths, key=lambda x: x['joint_prob'])[:10]
    
    def _find_critical_rare(self) -> List[Dict]:
        """找高影响力×低概率的枢纽"""
        # 计算入度作为影响力
        in_degree = {}
        for dep in self.dependencies:
            in_degree[dep.to_constraint] = in_degree.get(dep.to_constraint, 0) + 1
        
        critical = []
        for const, degree in in_degree.items():
            if degree > 2:  # 高影响力
                prob = self.probs.get(const, 0.5)
                if prob < 0.4:  # 低概率
                    critical.append({
                        'constraint': const,
                        'influence': degree,
                        'prob': prob,
                        'risk': round(degree * (1 - prob), 3),
                    })
        
        return sorted(critical, key=lambda x: -x['risk'])[:5]
    
    def get_report(self) -> str:
        """生成分析报告"""
        results = self.analyze()
        
        lines = [
            "=" * 60,
            "PROBABILISTIC CONSTRAINT ANALYSIS",
            "=" * 60,
            "",
            "[1] Rare Dependencies (p < 0.1)",
            "-" * 40,
        ]
        
        for dep in results['rare_dependencies'][:5]:
            lines.append(f"  {dep['from']} -> {dep['to']}: P={dep['joint_prob']}")
        
        lines.extend(["", "[2] Danger Zones", "-" * 40])
        for zone in results['danger_zones'][:5]:
            lines.append(f"  {zone['constraint']}: in_deg={zone['in_degree']}, P={zone['activation_prob']:.2f}")
        
        lines.extend(["", "[3] Critical Rare", "-" * 40])
        for c in results['critical_rare'][:5]:
            lines.append(f"  {c['constraint']}: inf={c['influence']}, P={c['prob']:.2f}")
        
        lines.extend(["", "[4] Rare Paths", "-" * 40])
        for path in results['rare_paths'][:3]:
            p = " -> ".join([x.split('.')[-1] for x in path['path']])
            lines.append(f"  {p}: P={path['joint_prob']}")
        
        return "\n".join(lines)


# ===== 使用示例 =====
if __name__ == "__main__":
    # 测试
    print("Testing ProbabilisticConstraintAnalyzer...")
    print("Module loaded OK")
