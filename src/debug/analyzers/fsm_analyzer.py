"""
FSMAnalyzer - 状态机分析器
分析状态机的: 状态数量、跳转条件、节点度、环检测、可达性
"""

import sys
import os
import re
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))


@dataclass
class StateInfo:
    """状态信息"""
    name: str
    line: int
    transitions: List['Transition'] = field(default_factory=list)
    in_degree: int = 0
    out_degree: int = 0
    is_initial: bool = False
    is_final: bool = False


@dataclass
class Transition:
    """状态跳转"""
    from_state: str
    to_state: str
    condition: str = ""
    line: int = 0


@dataclass
class FSMGraph:
    """状态机图"""
    states: Dict[str, StateInfo] = field(default_factory=dict)
    transitions: List[Transition] = field(default_factory=list)
    initial_state: str = ""
    final_states: List[str] = field(default_factory=list)


@dataclass
class CycleInfo:
    """环信息"""
    states: List[str]
    length: int
    is_deadlock: bool  # 死锁: 环中没有出口
    is_orphan: bool     # 孤立: 不可达状态


@dataclass
class FSMReport:
    """状态机报告"""
    fsm_count: int = 0
    graphs: List[FSMGraph] = field(default_factory=list)
    
    total_states: int = 0
    total_transitions: int = 0
    total_cycles: int = 0
    deadlocks: List[CycleInfo] = field(default_factory=list)
    orphans: List[str] = field(default_factory=list)
    
    avg_states_per_fsm: float = 0.0
    avg_transitions_per_fsm: float = 0.0
    avg_degree: float = 0.0
    
    complexity_score: float = 0.0
    suggestions: List[str] = field(default_factory=list)


class FSMAnalyzer:
    """状态机分析器"""
    
    def __init__(self, parser):
        self.parser = parser
    
    def analyze(self) -> FSMReport:
        """执行状态机分析"""
        graphs = []
        all_cycles = []
        all_orphans = []
        
        for path, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            try:
                with open(path, 'r') as f:
                    content = f.read()
            except:
                continue
            
            fsm_graphs = self._extract_fsms(content, path)
            graphs.extend(fsm_graphs)
        
        # 分析每个状态机
        for graph in graphs:
            self._calculate_degrees(graph)
            cycles = self._find_cycles(graph)
            all_cycles.extend(cycles)
            
            # 找孤立状态
            for state_name, state in graph.states.items():
                if state.in_degree == 0 and state.out_degree == 0:
                    all_orphans.append(state_name)
                elif state.in_degree == 0 and state_name != graph.initial_state:
                    all_orphans.append(state_name)
        
        # 统计
        total_states = sum(len(g.states) for g in graphs)
        total_transitions = sum(len(g.transitions) for g in graphs)
        
        # 计算平均度
        avg_degree = 0
        if total_states > 0:
            total_degree = sum(
                s.in_degree + s.out_degree 
                for g in graphs 
                for s in g.states.values()
            )
            avg_degree = total_degree / total_states
        
        # 复杂度评分 (基于状态数、跳转数、环数)
        complexity = self._calculate_complexity(total_states, total_transitions, len(all_cycles))
        
        # 生成建议
        suggestions = self._generate_suggestions(
            total_states, total_transitions, all_cycles, all_orphans
        )
        
        return FSMReport(
            fsm_count=len(graphs),
            graphs=graphs,
            total_states=total_states,
            total_transitions=total_transitions,
            total_cycles=len(all_cycles),
            deadlocks=[c for c in all_cycles if c.is_deadlock],
            orphans=all_orphans,
            avg_states_per_fsm=total_states / len(graphs) if graphs else 0,
            avg_transitions_per_fsm=total_transitions / len(graphs) if graphs else 0,
            avg_degree=avg_degree,
            complexity_score=complexity,
            suggestions=suggestions
        )
    
    def _extract_fsms(self, content: str, path: str) -> List[FSMGraph]:
        """提取状态机"""
        graphs = []
        
        # 状态机模式: 通常是case(state)结构
        # 查找case语句,分析其中的状态定义
        
        # 方法1: typedef enum识别状态
        enums = re.findall(r'typedef\s+enum\s*\{([^}]+)\}\s*(\w+)', content)
        
        if enums:
            for enum_body, enum_name in enums:
                states = [s.strip().split()[-1] for s in enum_body.split(',')]
                
                graph = FSMGraph()
                graph.initial_state = states[0] if states else ""
                
                for state in states:
                    graph.states[state] = StateInfo(name=state, line=0)
                
                # 查找状态转换
                # 简化: 查找 state : 模式
                trans_pattern = rf'({states[0]}|{"|".join(states)})\s*:\s*(\w+)\s*<='
                transitions = re.findall(trans_pattern, content)
                
                for from_state, to_state in transitions:
                    trans = Transition(from_state=from_state, to_state=to_state)
                    graph.transitions.append(trans)
                    
                    if from_state in graph.states:
                        graph.states[from_state].transitions.append(trans)
                
                graphs.append(graph)
        
        # 方法2: 简单状态机检测 (无enum的情况)
        # 查找包含state关键字的case语句
        state_vars = re.findall(r'case\s*\(\s*(\w+_state|state|curr_state)\s*\)', content)
        
        if state_vars and not enums:
            graph = FSMGraph()
            
            # 查找可能的状态名
            state_names = re.findall(r'(\w+)\s*:\s*(?:if|case|begin)', content)
            for name in set(state_names):
                if len(name) < 20 and not any(kw in name.lower() for kw in ['if', 'case', 'begin']):
                    graph.states[name] = StateInfo(name=name, line=0)
            
            if graph.states:
                graph.initial_state = list(graph.states.keys())[0]
                graphs.append(graph)
        
        return graphs
    
    def _calculate_degrees(self, graph: FSMGraph):
        """计算节点度"""
        for trans in graph.transitions:
            if trans.from_state in graph.states:
                graph.states[trans.from_state].out_degree += 1
            
            if trans.to_state in graph.states:
                graph.states[trans.to_state].in_degree += 1
        
        # 初始状态
        if graph.initial_state in graph.states:
            graph.states[graph.initial_state].is_initial = True
    
    def _find_cycles(self, graph: FSMGraph) -> List[CycleInfo]:
        """找环 (DFS)"""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(state: str, path: List[str]) -> List[str]:
            visited.add(state)
            rec_stack.add(state)
            path.append(state)
            
            if state in graph.states:
                for trans in graph.states[state].transitions:
                    next_state = trans.to_state
                    
                    if next_state not in visited:
                        result = dfs(next_state, path.copy())
                        if result:
                            return result
                    elif next_state in rec_stack:
                        # 找到环
                        cycle_start = path.index(next_state)
                        cycle_states = path[cycle_start:]
                        return cycle_states
            
            rec_stack.remove(state)
            return None
        
        for state in graph.states:
            if state not in visited:
                cycle = dfs(state, [])
                if cycle:
                    # 检查是否为死锁环 (没有出口)
                    has_exit = False
                    for cs in cycle:
                        if cs in graph.states:
                            for trans in graph.states[cs].transitions:
                                if trans.to_state not in cycle:
                                    has_exit = True
                                    break
                    
                    cycles.append(CycleInfo(
                        states=cycle,
                        length=len(cycle),
                        is_deadlock=not has_exit,
                        is_orphan=False
                    ))
        
        return cycles
    
    def _calculate_complexity(self, states: int, transitions: int, cycles: int) -> float:
        """计算复杂度分数"""
        # 简单复杂度模型: 状态数 + 跳转数 + 环数惩罚
        complexity = states * 1.0 + transitions * 0.5 + cycles * 5.0
        
        # 归一化到0-100
        if states == 0:
            return 0
        
        normalized = min(100, complexity / max(1, states) * 10)
        return normalized
    
    def _generate_suggestions(
        self, 
        states: int, 
        transitions: int, 
        cycles: List[CycleInfo],
        orphans: List[str]
    ) -> List[str]:
        """生成建议"""
        suggestions = []
        
        if states > 20:
            suggestions.append(
                f"状态机较大({states}个状态), 考虑拆分为子状态机"
            )
        
        deadlocks = [c for c in cycles if c.is_deadlock]
        if deadlocks:
            suggestions.append(
                f"发现{len(deadlocks)}个死锁环, 无法从这些状态退出"
            )
            for d in deadlocks:
                suggestions.append(f"  死锁状态: {'->'.join(d.states)}")
        
        if orphans:
            suggestions.append(
                f"发现{len(orphans)}个孤立状态, 这些状态不可达"
            )
        
        if cycles and not deadlocks:
            suggestions.append(
                f"状态机包含{len(cycles)}个循环, 需验证所有状态可退出"
            )
        
        if not suggestions:
            suggestions.append("状态机结构良好")
        
        return suggestions
    
    def print_report(self, report: FSMReport):
        """打印报告"""
        print("="*60)
        print("FSM Analysis Report")
        print("="*60)
        
        print(f"\nStatistics:")
        print(f"  FSM count: {report.fsm_count}")
        print(f"  Total states: {report.total_states}")
        print(f"  Total transitions: {report.total_transitions}")
        print(f"  Total cycles: {report.total_cycles}")
        print(f"  Deadlocks: {len(report.deadlocks)}")
        print(f"  Orphan states: {len(report.orphans)}")
        print(f"  Avg states/FSM: {report.avg_states_per_fsm:.1f}")
        print(f"  Avg degree: {report.avg_degree:.2f}")
        print(f"  Complexity score: {report.complexity_score:.1f}")
        
        if report.graphs:
            for i, graph in enumerate(report.graphs):
                print(f"\nFSM {i+1}:")
                print(f"  Initial: {graph.initial_state}")
                print(f"  States: {len(graph.states)}")
                print(f"  Transitions: {len(graph.transitions)}")
                
                # 节点度分析
                print(f"  Node degrees:")
                for name, state in graph.states.items():
                    print(f"    {name}: in={state.in_degree}, out={state.out_degree}")
        
        print("="*60)
        
        if report.suggestions:
            print(f"\nSuggestions:")
            for s in report.suggestions:
                print(f"  - {s}")


__all__ = ['FSMAnalyzer', 'FSMReport', 'FSMGraph', 'StateInfo', 'Transition', 'CycleInfo']
