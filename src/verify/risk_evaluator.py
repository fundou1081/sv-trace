"""
RiskEvaluator - 风险评估报告
评估变更风险，生成风险报告
"""
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class RiskItem:
    """风险项"""
    item: str
    risk_level: str  # high/medium/low
    impact: str
    probability: str  # high/medium/low
    mitigation: str

class RiskEvaluator:
    """风险评估器"""
    
    def __init__(self):
        self.risk_rules = {
            'cdc_change': 'high',
            'reset_change': 'high',
            'interface_change': 'medium',
            'fsm_change': 'medium',
            'logic_optimization': 'low',
        }
    
    def evaluate_changes(self, changes: List[str]) -> List[RiskItem]:
        """评估变更风险"""
        risks = []
        
        for change in changes:
            change_lower = change.lower()
            
            for pattern, level in self.risk_rules.items():
                if pattern in change_lower:
                    risks.append(RiskItem(
                        item=change,
                        risk_level=level,
                        impact=self._get_impact_description(pattern),
                        probability='medium',
                        mitigation=self._get_mitigation(pattern)
                    ))
                    break
        
        return risks
    
    def _get_impact_description(self, pattern: str) -> str:
        impacts = {
            'cdc_change': '可能导致亚稳态或数据错误',
            'reset_change': '可能导致复位失败或状态异常',
            'interface_change': '可能导致接口时序问题',
            'fsm_change': '可能导致状态机死锁或错误转移',
            'logic_optimization': '可能影响时序或功能',
        }
        return impacts.get(pattern, '未知影响')
    
    def _get_mitigation(self, pattern: str) -> str:
        mitigations = {
            'cdc_change': '1. 审查CDC路径 2. 添加SVA断言 3. 增加CDC覆盖',
            'reset_change': '1. 审查复位时序 2. 检查所有复位条件 3. 仿真验证',
            'interface_change': '1. 审查接口时序 2. 检查约束 3. 端到端测试',
            'fsm_change': '1. 审查状态转移 2. 覆盖所有状态和转移 3. 边界测试',
            'logic_optimization': '1. 时序分析 2. 回归测试',
        }
        return mitigations.get(pattern, '建议审查')
    
    def generate_report(self, risks: List[RiskItem]) -> str:
        """生成风险报告"""
        lines = []
        lines.append("# 变更风险评估报告")
        lines.append("")
        
        high = [r for r in risks if r.risk_level == 'high']
        medium = [r for r in risks if r.risk_level == 'medium']
        low = [r for r in risks if r.risk_level == 'low']
        
        lines.append(f"## 风险摘要")
        lines.append(f"- 高风险: {len(high)} 项")
        lines.append(f"- 中风险: {len(medium)} 项")
        lines.append(f"- 低风险: {len(low)} 项")
        lines.append("")
        
        if high:
            lines.append("## 🔴 高风险项")
            for r in high:
                lines.append(f"- **{r.item}**")
                lines.append(f"  - 影响: {r.impact}")
                lines.append(f"  - 缓解: {r.mitigation}")
                lines.append("")
        
        if medium:
            lines.append("## 🟡 中风险项")
            for r in medium:
                lines.append(f"- {r.item}")
                lines.append(f"  - 影响: {r.impact}")
                lines.append("")
        
        return '\n'.join(lines)
