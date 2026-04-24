"""
FSMExtractor - 状态机提取器
"""
import sys
import os
import re
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))


@dataclass
class FSMState:
    name: str
    encoding: int = 0
    is_reset: bool = False
    transitions: List[Tuple[str, str]] = field(default_factory=list)


@dataclass
class FSMInfo:
    name: str
    state_var: str
    states: List[FSMState] = field(default_factory=list)
    reset_state: str = ""
    encoding_type: str = "auto"
    confidence: float = 0.0
    always_ff_block: str = ""
    always_comb_block: str = ""

    def visualize(self) -> str:
        lines = [f"FSM: {self.name}", "=" * 50]
        lines.append(f"State Variable: {self.state_var}")
        lines.append(f"Reset State: {self.reset_state}")
        lines.append(f"Encoding: {self.encoding_type}")
        lines.append(f"Confidence: {self.confidence:.2f}")
        lines.append("")
        lines.append("States:")
        for state in self.states:
            reset_tag = " [RESET]" if state.is_reset else ""
            lines.append(f"  {state.name}{reset_tag}")
            for cond, next_s in state.transitions:
                lines.append(f"    --[{cond}]--> {next_s}")
        return "\n".join(lines)


class FSMExtractor:
    def __init__(self, parser):
        self.parser = parser
    
    def extract(self) -> List[FSMInfo]:
        fsm_list = []
        
        for tree in self.parser.trees.values():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            root = tree.root
            if not hasattr(root, 'members'):
                continue
            
            for i in range(len(root.members)):
                member = root.members[i]
                if 'ModuleDeclaration' not in str(type(member)):
                    continue
                
                if not hasattr(member, 'members'):
                    continue
                
                # 收集所有过程块
                ff_stmt = None
                comb_stmt = None
                
                for j in range(len(member.members)):
                    stmt = member.members[j]
                    
                    if 'ProceduralBlock' in str(type(stmt)):
                        stmt_str = str(stmt.statement) if hasattr(stmt, 'statement') else ''
                        
                        if '@(posedge' in stmt_str or '@(negedge' in stmt_str:
                            # 检查是否包含 state <= next_state 模式
                            if re.search(r'\w+\s*<=?\s*next_state', stmt_str):
                                ff_stmt = stmt_str
                        else:
                            # always_comb
                            if 'case' in stmt_str and 'next_state' in stmt_str:
                                comb_stmt = stmt_str
                
                # 如果找到了 FF+Comb 对，尝试提取 FSM
                if ff_stmt and comb_stmt:
                    # 查找状态变量
                    state_var = self._find_state_var(ff_stmt, comb_stmt)
                    if state_var:
                        fsm = self._analyze_fsm(state_var, ff_stmt, comb_stmt)
                        if fsm and self._is_likely_fsm(fsm):
                            fsm_list.append(fsm)
        
        return fsm_list
    
    def _find_state_var(self, ff_stmt: str, comb_stmt: str) -> Optional[str]:
        """查找状态变量"""
        # 从 always_ff 中查找被赋值的信号
        # 模式: signal <= next_state
        for match in re.finditer(r'(\w+)\s*<=?\s*next_state', ff_stmt):
            sig = match.group(1)
            if sig not in ['clk', 'clock', 'rst', 'reset']:
                # 确认在 always_comb 中有 case(state_var)
                if f'case ({sig})' in comb_stmt or f'case({sig})' in comb_stmt:
                    return sig
        return None
    
    def _analyze_fsm(self, state_var: str, ff_stmt: str, comb_stmt: str) -> Optional[FSMInfo]:
        """分析状态机"""
        
        # 提取所有状态名
        state_names = set()
        
        # 从 always_comb 的 case 中提取
        case_match = re.search(r'case\s*\(\s*' + state_var + r'\s*\)(.*?)endcase', comb_stmt, re.DOTALL)
        if case_match:
            case_body = case_match.group(1)
            for sm in re.finditer(r'(\w+)\s*:', case_body):
                state_names.add(sm.group(1))
        
        states = [FSMState(name=name) for name in state_names]
        
        if not states:
            return None
        
        # 查找复位状态
        reset_state = ""
        reset_pattern = rf'if\s*\([^)]+\)\s*{state_var}\s*<=?\s*(\w+)'
        match = re.search(reset_pattern, ff_stmt)
        if match:
            reset_state = match.group(1)
        
        if reset_state:
            for s in states:
                if s.name == reset_state:
                    s.is_reset = True
        
        # 提取转换关系
        for s in states:
            s.transitions = self._extract_transitions(state_var, comb_stmt, s.name)
        
        fsm = FSMInfo(
            name=f"fsm_{state_var}",
            state_var=state_var,
            states=states,
            reset_state=reset_state,
            always_ff_block=ff_stmt,
            always_comb_block=comb_stmt
        )
        
        fsm.confidence = self._calculate_confidence(fsm)
        
        return fsm
    
    def _extract_transitions(self, state_var: str, comb_stmt: str, state_name: str) -> List[Tuple[str, str]]:
        """提取从某个状态出发的转换"""
        transitions = []
        
        # 找到 state_name: 后的代码块
        pattern = rf'{state_name}\s*:\s*(.*?)(?=\n\s*\w+\s*:|\n\s*endcase)'
        match = re.search(pattern, comb_stmt, re.DOTALL)
        
        if not match:
            return transitions
        
        block = match.group(1)
        
        # 查找 next_state = XXX
        for ns_match in re.finditer(r'next_state\s*=\s*(\w+)', block):
            next_state = ns_match.group(1)
            condition = self._extract_condition(block)
            transitions.append((condition, next_state))
        
        return transitions
    
    def _extract_condition(self, block: str) -> str:
        """从代码块中提取条件"""
        if_match = re.search(r'if\s*\(([^)]+)\)', block)
        if if_match:
            return if_match.group(1).strip()
        return "always"
    
    def _is_likely_fsm(self, fsm: FSMInfo) -> bool:
        if len(fsm.states) < 2:
            return False
        if not fsm.reset_state:
            return False
        if fsm.confidence < 0.3:
            return False
        return True
    
    def _calculate_confidence(self, fsm: FSMInfo) -> float:
        score = 0.0
        if len(fsm.states) >= 2:
            score += 0.3
        if fsm.reset_state:
            score += 0.3
        total_transitions = sum(len(s.transitions) for s in fsm.states)
        if total_transitions >= len(fsm.states):
            score += 0.2
        if all(not s.name.isdigit() for s in fsm.states):
            score += 0.2
        return min(score, 1.0)


def extract_fsm(parser) -> List[FSMInfo]:
    return FSMExtractor(parser).extract()
