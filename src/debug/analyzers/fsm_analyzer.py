"""
FSMAnalyzer - 状态机深度分析器
增强版: 复杂度评分、不可达检测、死锁检测
"""

import os
import re
import sys
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict, deque

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from parse import SVParser


@dataclass
class StateInfo:
    name: str
    line: int
    is_initial: bool = False
    is_final: bool = False
    in_degree: int = 0
    out_degree: int = 0
    transitions: List['Transition'] = field(default_factory=list)


@dataclass
class Transition:
    from_state: str
    to_state: str
    condition: str = ""
    line: int = 0


@dataclass
class FSMComplexity:
    """FSM复杂度评分"""
    state_count: int = 0
    transition_count: int = 0
    avg_transitions: float = 0.0
    max_out_degree: int = 0
    complexity_score: float = 0.0
    
    # 安全等级
    SAFE = 50
    WARN = 100
    HIGH = 150
    
    def get_level(self) -> str:
        if self.complexity_score < self.SAFE:
            return "SAFE"
        elif self.complexity_score < self.WARN:
            return "WARN"
        elif self.complexity_score < self.HIGH:
            return "HIGH"
        else:
            return "CRITICAL"


@dataclass
class UnreachableState:
    """不可达状态"""
    name: str
    reason: str  # "no_input", "isolated"


@dataclass
class DeadlockCycle:
    """死锁环"""
    states: List[str]
    length: int
    has_exit: bool = False
    is_reachable: bool = True


@dataclass
class FSMReport:
    """FSM分析报告"""
    module_name: str = ""
    fsm_count: int = 0
    
    # 状态
    states: List[StateInfo] = field(default_factory=list)
    state_names: List[str] = field(default_factory=list)
    
    # 跳转
    transitions: List[Transition] = field(default_factory=list)
    
    # 复杂度
    complexity: FSMComplexity = field(default_factory=FSMComplexity)
    
    # 问题
    unreachable: List[UnreachableState] = field(default_factory=list)
    deadlocks: List[DeadlockCycle] = field(default_factory=list)
    
    # 建议
    suggestions: List[str] = field(default_factory=list)


class FSMAnalyzer:
    """状态机分析器"""
    
    def __init__(self, parser):
        self.parser = parser
    
    def analyze(self) -> FSMReport:
        """分析所有FSM"""
        report = FSMReport()
        
        # 分析每个文件
        for path in self.parser.trees:
            if not path:
                continue
            
            try:
                with open(path, 'r') as f:
                    content = f.read()
            except:
                continue
            
            # 提取FSM
            fsm_data = self._extract_fsm(content)
            
            if not fsm_data['states']:
                continue
            
            # 更新报告
            if not report.module_name:
                report.module_name = os.path.basename(path).replace('.sv', '')
            
            # 添加状态
            for s in fsm_data['states']:
                report.state_names.append(s)
                st = StateInfo(name=s, line=fsm_data['lines'].get(s, 0))
                report.states.append(st)
            
            # 添加跳转
            for t in fsm_data['transitions']:
                report.transitions.append(t)
        
        report.fsm_count = len(set(report.state_names))
        
        if report.fsm_count == 0:
            return report
        
        # 计算复杂度
        report.complexity = self._calculate_complexity(report)
        
        # 检测不可达状态
        report.unreachable = self._find_unreachable(report)
        
        # 检测死锁
        report.deadlocks = self._find_deadlocks(report)
        
        # 生成建议
        report.suggestions = self._generate_suggestions(report)
        
        return report
    
    def _extract_fsm(self, content: str) -> Dict:
        """提取FSM"""
        data = {'states': [], 'transitions': [], 'lines': {}, 'initial': ''}
        
        # 方法1: typedef enum
        # 只提取大写状态名
        for match in re.finditer(r'typedef\s+enum[^{]*\{([^}]+)\}', content):
            body = match.group(1)
            states = re.findall(r'([A-Z_][A-Z0-9_]*)', body)
            data['states'].extend(states)
            
            # 假设第一个是初始状态
            if states and not data['initial']:
                data['initial'] = states[0]
        
        # 方法2: case语句中的状态
        if not data['states']:
            # 查找case (state)语句
            case_stmts = re.findall(r'case\s*\(\s*(\w+_state|current_state|state)\s*\)', content)
            for var in case_stmts[:1]:
                # 查找对应的状态定义
                patterns = [
                    rf'{var}\s*==\s*(\w+)',
                    rf'{var}:\s*//\s*(\w+)',
                ]
                for p in patterns:
                    matches = re.findall(p, content)
                    data['states'].extend(matches)
        
        # 去重
        data['states'] = list(set(data['states']))
        
        # 查找跳转
        # 从case语句提取跳转
        for match in re.finditer(r'([A-Z_][A-Z0-9_]*)\s*:\s*(?:if|case)\s*\(?([^)]+)\)\s*([A-Z_][A-Z0-9_]*)', content):
            from_st, cond, to_st = match.groups()
            if from_st in data['states'] and to_st in data['states']:
                data['transitions'].append(Transition(
                    from_state=from_st,
                    to_state=to_st,
                    condition=cond[:50] if cond else ''
                ))
        
        return data
    
    def _calculate_complexity(self, report: FSMReport) -> FSMComplexity:
        """计算复杂度"""
        c = FSMComplexity()
        c.state_count = report.fsm_count
        c.transition_count = len(report.transitions)
        
        # 计算平均出度
        out_degrees = defaultdict(int)
        for t in report.transitions:
            out_degrees[t.from_state] += 1
        
        if out_degrees:
            c.max_out_degree = max(out_degrees.values())
            c.avg_transitions = sum(out_degrees.values()) / len(out_degrees)
        
        # 复杂度 = 状态数 × 平均出度
        c.complexity_score = c.state_count * c.avg_transitions
        
        return c
    
    def _find_unreachable(self, report: FSMReport) -> List[UnreachableState]:
        """找不可达状态"""
        unreachable = []
        
        if not report.state_names:
            return unreachable
        
        # BFS找可达状态
        reachable = set()
        queue = deque([report.state_names[0] if report.state_names else None])
        
        while queue:
            state = queue.popleft()
            if state and state not in reachable:
                reachable.add(state)
                
                # 找到所有可达的下一个状态
                for t in report.transitions:
                    if t.from_state == state:
                        if t.to_state not in reachable:
                            queue.append(t.to_state)
        
        # 检查不可达
        for s in report.state_names:
            if s not in reachable:
                unreachable.append(UnreachableState(
                    name=s,
                    reason="no_input_path"
                ))
        
        return unreachable
    
    def _find_deadlocks(self, report: FSMReport) -> List[DeadlockCycle]:
        """找死锁环"""
        deadlocks = []
        
        # 简化: 找所有强连通分量
        state_set = set(report.state_names)
        
        for start in state_set:
            # DFS找环
            path = []
            visited = set()
            
            def dfs(current, path):
                if current in visited:
                    return None
                visited.add(current)
                path.append(current)
                
                # 找下一个状态
                next_states = [t.to_state for t in report.transitions if t.from_state == current]
                
                for next_st in next_states:
                    if next_st == start and len(path) > 1:
                        # 找到环
                        return path
                    result = dfs(next_st, path[:])
                    if result:
                        return result
                
                return None
            
            cycle = dfs(start, [])
            if cycle:
                # 检查是否有出口
                has_exit = False
                for st in cycle:
                    for t in report.transitions:
                        if t.from_state == st and t.to_state not in cycle:
                            has_exit = True
                            break
                
                if not has_exit:
                    deadlocks.append(DeadlockCycle(
                        states=cycle,
                        length=len(cycle),
                        has_exit=False
                    ))
        
        return deadlocks
    
    def _generate_suggestions(self, report: FSMReport) -> List[str]:
        """生成建议"""
        suggestions = []
        
        # 复杂度建议
        level = report.complexity.get_level()
        if level != "SAFE":
            suggestions.append(
                f"FSM复杂度{level}({report.complexity.complexity_score}), 考虑拆分"
            )
        
        # 不可达建议
        if report.unreachable:
            suggestions.append(
                f"发现{len(report.unreachable)}个不可达状态: {[u.name for u in report.unreachable]}"
            )
        
        # 死锁建议
        if report.deadlocks:
            suggestions.append(
                f"发现{len(report.deadlocks)}个死锁环"
            )
        
        if not suggestions:
            suggestions.append("状态机结构良好")
        
        return suggestions
    
    def print_report(self, report: FSMReport):
        """打印报告"""
        print("="*60)
        print(f"FSM Analysis: {report.module_name}")
        print("="*60)
        
        print(f"\n[States]")
        print(f"  Count: {report.fsm_count}")
        print(f"  States: {report.state_names[:10]}...")
        
        print(f"\n[Complexity]")
        c = report.complexity
        print(f"  Transitions: {c.transition_count}")
        print(f"  Avg/State: {c.avg_transitions:.1f}")
        print(f"  Score: {c.complexity_score} ({c.get_level()})")
        
        print(f"\n[Issues]")
        print(f"  Unreachable: {len(report.unreachable)}")
        print(f"  Deadlocks: {len(report.deadlocks)}")
        
        if report.suggestions:
            print(f"\n[Suggestions]")
            for s in report.suggestions:
                print(f"  - {s}")
        
        print("="*60)


__all__ = ['FSMAnalyzer', 'FSMReport']


# ============================================================================
# FSM 增强功能 - 状态编码建议
# ============================================================================

def recommend_encoding(self, state_count: int) -> dict:
    """根据状态数量推荐状态编码方式"""
    
    if state_count <= 0:
        return {"encoding": "unknown", "bits": 0, "reason": "无有效状态"}
    
    if state_count == 1:
        return {
            "encoding": "binary", 
            "bits": 1, 
            "reason": "单状态只需要1位",
            "one_hot_value": "1b0",
            "power_estimate": "low"
        }
    
    if state_count == 2:
        return {
            "encoding": "binary", 
            "bits": 1, 
            "reason": "2状态用binary最省资源",
            "binary_value": "1'b0 / 1'b1",
            "gray_value": "1'b0 / 1'b1",
            "one_hot_value": "2'b01 / 2'b10",
            "power_estimate": "low"
        }
    
    if state_count <= 4:
        return {
            "encoding": "binary", 
            "bits": 2, 
            "reason": "4状态用binary最省资源",
            "binary_value": "2'b00/01/10/11",
            "gray_value": "2'b00/01/11/10",
            "one_hot_value": "4'b0001/0010/0100/1000",
            "power_estimate": "low"
        }
    
    if state_count <= 8:
        return {
            "encoding": "gray", 
            "bits": 3, 
            "reason": "3-8状态推荐Gray编码，减少亚稳态",
            "binary_value": "3'b000-111",
            "gray_value": "3'b000/001/011/010/110/111/101/100",
            "one_hot_value": "8'b00000001/.../10000000",
            "power_estimate": "medium"
        }
    
    if state_count <= 16:
        return {
            "encoding": "one_hot", 
            "bits": state_count, 
            "reason": "8-16状态推荐one-hot，高速设计首选",
            "encoding_scheme": "one_hot",
            "power_estimate": "medium-high",
            "note": "one-hot每个状态1位寄存器，组合逻辑少"
        }
    
    # 16+ 状态
    if state_count <= 32:
        return {
            "encoding": "one_hot", 
            "bits": state_count, 
            "reason": "多状态建议one-hot或考虑拆分",
            "power_estimate": "high",
            "suggestion": "状态数超过16，建议考虑模块化拆分"
        }
    
    # 32+ 状态：强烈建议拆分
    return {
        "encoding": "one_hot", 
        "bits": state_count, 
        "reason": "状态数过多，必须拆分或使用层级状态机",
        "power_estimate": "very_high",
        "warning": "CRITICAL: 状态数过多，必须拆分!"
    }


def get_encoding_power_estimate(self, encoding: str, bits: int, 
                                  toggle_rate: float = 0.2) -> dict:
    """估算不同编码的功耗"""
    
    base_power = bits * toggle_rate
    
    estimates = {
        "binary": {
            "description": "二进制编码",
            "switching_power": base_power * 1.0,
            "glitch_risk": "medium",
            "notes": "状态跳转时多位翻转，功耗较高"
        },
        "gray": {
            "description": "格雷码",
            "switching_power": base_power * 0.5,
            "glitch_risk": "low",
            "notes": "相邻状态只有1位翻转"
        },
        "one_hot": {
            "description": "独热码",
            "switching_power": base_power * 0.3,
            "glitch_risk": "low",
            "notes": "每次跳转只翻转1位，但寄存器多"
        }
    }
    
    return estimates.get(encoding, {})


# 添加到 FSMAnalyzer 类
FSMAnalyzer.recommend_encoding = recommend_encoding
FSMAnalyzer.get_encoding_power_estimate = get_encoding_power_estimate


__all__ = ['FSMAnalyzer', 'FSMReport', 'FSMComplexity', 'StateInfo', 'Transition']
