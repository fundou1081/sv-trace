"""
InterfaceChange - 接口变更检测
检测接口信号的变化
"""
from typing import List, Dict, Set
from dataclasses import dataclass

@dataclass
class InterfaceChange:
    """接口变更"""
    signal: str
    change_type: str  # added/removed/renamed/type_changed
    old_value: str = ""
    new_value: str = ""

class InterfaceChangeDetector:
    """接口变更检测器"""
    
    def detect(self, old_ports: List[str], new_ports: List[str]) -> List[InterfaceChange]:
        """检测接口变更"""
        changes = []
        
        old_set = set(old_ports)
        new_set = set(new_ports)
        
        # 新增
        for p in new_set - old_set:
            changes.append(InterfaceChange(signal=p, change_type='added'))
        
        # 移除
        for p in old_set - new_set:
            changes.append(InterfaceChange(signal=p, change_type='removed'))
        
        return changes
    
    def generate_report(self, changes: List[InterfaceChange]) -> str:
        """生成变更报告"""
        lines = []
        lines.append("# 接口变更报告")
        lines.append("")
        
        added = [c for c in changes if c.change_type == 'added']
        removed = [c for c in changes if c.change_type == 'removed']
        
        lines.append(f"新增信号: {len(added)}")
        for c in added:
            lines.append(f"  + {c.signal}")
        
        lines.append(f"\n移除信号: {len(removed)}")
        for c in removed:
            lines.append(f"  - {c.signal}")
        
        return '\n'.join(lines)
