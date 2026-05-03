"""FSMAnalyzer - 状态机深度分析器。

基于 IEEE 1800-2017 Section 40.4 标准提取和分析状态机。

Example:
    >>> from debug.analyzers.fsm_analyzer import FSMAnalyzer
    >>> from parse import SVParser
    >>> parser = SVParser()
    >>> parser.parse_file("design.sv")
    >>> analyzer = FSMAnalyzer(parser)
    >>> fsm = analyzer.extract_fsm("top")
    >>> result = analyzer.analyze(fsm)
    >>> print(analyzer.get_report(result))
"""

import os
import re
import sys
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict, deque

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


@dataclass
class StateInfo:
    name: str
    line: int = 0
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
    line_number: int = 0


@dataclass
class FSMInfo:
    name: str
    register_signal: str = ""
    states: List[StateInfo] = field(default_factory=list)
    transitions: List[Transition] = field(default_factory=list)
    encoding: Dict[str, str] = field(default_factory=dict)
    reset_state: str = ""
    complexity_score: int = 0
    fsm_name: str = ""


@dataclass
class FSMAnalysisResult:
    fsm: FSMInfo
    state_count: int = 0
    transition_count: int = 0
    complexity: int = 0
    unreachable_states: List[str] = field(default_factory=list)
    dead_lock_states: List[str] = field(default_factory=list)
    has_initial_state: bool = False
    quality_grade: str = "B"


class FSMAnalyzer:
    """状态机深度分析器。"""
    
    def __init__(self, parser):
        self.parser = parser
        self.fsms: Dict[str, FSMInfo] = {}
    
    def _get_module_source(self, module_name: str) -> Optional[str]:
        """Get source code for a specific module."""
        for fname in self.parser.trees.keys():
            try:
                with open(fname, 'r') as f:
                    full_source = f.read()
            except:
                continue
            
            mod_start = full_source.find(f'module {module_name}')
            if mod_start == -1:
                continue
            mod_end = full_source.find('endmodule', mod_start)
            if mod_end == -1:
                continue
            return full_source[mod_start:mod_end + len('endmodule')]
        return None
    
    def extract_fsm(self, module_name: str, state_register: str = None) -> Optional[FSMInfo]:
        """Extract FSM."""
        module_source = self._get_module_source(module_name)
        if not module_source:
            return None
        
        # Find always_ff blocks
        ff_blocks = re.findall(r'always_ff\s+@\([^)]+\)\s*begin\s+(.*?)\s+end', module_source, re.DOTALL)
        
        # Find the case variable first (more reliable than guessing from always_ff)
        case_match = re.search(r'(?:unique\s+)?case\s*\(\s*(\w+)\s*\)', module_source)
        state_var = state_register
        if not state_var and case_match:
            state_var = case_match.group(1)
        
        if not state_var:
            for block in ff_blocks:
                m = re.search(r'(\w+)\s*<=', block)
                if m:
                    cand = m.group(1)
                    if cand not in ['clk', 'clock', 'rst', 'reset', 'enable']:
                        state_var = cand
                        break
        
        if not state_var:
            return None
        
        # Find next_state signal (e.g., next_state, state_next, state_d)
        next_var = None
        next_matches = re.findall(r'(next_\w+|\w+_next|state_d)\s*=\s*([^;]+)', module_source)
        for name, _ in next_matches:
            if 'next' in name.lower() or name == 'state_d':
                next_var = name
                break
        
        # Build FSMInfo
        fsm_info = FSMInfo(name=state_var, register_signal=state_var)
        
        # Extract transitions from case block
        # Standard FSM: case(state_var) or unique case(state_var)
        case_pattern = rf'(?:unique\s+)?case\s*\(\s*{state_var}\s*\)(.*?)endcase'
        case_m = re.search(case_pattern, module_source, re.DOTALL)
        
        # One-hot FSM: case(1'b1) or unique case(1'b1)
        if not case_m:
            case_pattern = r"(?:unique\s+)?case\s*\(\s*1'b1\s*\)(.*?)endcase"
            case_m = re.search(case_pattern, module_source, re.DOTALL)
        
        if case_m:
            case_body = case_m.group(1)
            
            # Determine which pattern to use based on next_var type
            if next_var and next_var != 'state_d':
                # Pattern: STATE: if (cond) next_var = TARGET;
                assign_pattern = rf'(\w+)\s*:\s*(?:if\s*\([^)]+\)\s+)?{re.escape(next_var)}\s*=\s*(\w+)'
                when_matches = re.findall(assign_pattern, case_body)
            elif next_var == 'state_d':
                # Pattern: STATE: ... state_d = TARGET; (state_d assignment, OpenTitan style)
                assign_pattern = r'(\w+)\s*:.*?state_d\s*=\s*(\w+)'
                when_matches = re.findall(assign_pattern, case_body, re.DOTALL)
            else:
                # Try state_d = TARGET (direct FSM assignment, common in OpenTitan)
                assign_pattern_d = r'(\w+)\s*:.*?state_d\s*=\s*(\w+)'
                dm = re.findall(assign_pattern_d, case_body, re.DOTALL)
                
                # Try state_var <= TARGET (sequential always_ff)
                assign_pattern_q = r'(\w+)\s*:.*?' + re.escape(state_var) + r'\s*<=\s*(\w+)'
                qm = re.findall(assign_pattern_q, case_body, re.DOTALL)
                
                when_matches = dm if len(dm) > len(qm) else qm
            
            for match in when_matches:
                if len(match) == 3:
                    from_state, _, to_state = match
                elif len(match) == 2:
                    from_state, to_state = match
                else:
                    from_state, to_state = match[0], match[-1]
                fsm_info.transitions.append(Transition(
                    from_state=from_state.strip(),
                    to_state=to_state.strip()
                ))
        
        # Infer states from transitions
        state_names = set()
        for t in fsm_info.transitions:
            state_names.add(t.from_state)
            state_names.add(t.to_state)
        for name in sorted(state_names):
            fsm_info.states.append(StateInfo(name=name))
        
        # Calculate degrees
        in_deg = defaultdict(int)
        out_deg = defaultdict(int)
        for t in fsm_info.transitions:
            out_deg[t.from_state] += 1
            in_deg[t.to_state] += 1
        for s in fsm_info.states:
            s.in_degree = in_deg.get(s.name, 0)
            s.out_degree = out_deg.get(s.name, 0)
            s.transitions = [t for t in fsm_info.transitions if t.from_state == s.name]
        
        # Find reset state
        reset_found = False
        for block in ff_blocks:
            if state_var in block:
                rm = re.search(r"if\s*\(\s*!?\w+\s*\)\s*(\w+)\s*<=\s*(\w+)", block)
                if rm:
                    fsm_info.reset_state = rm.group(3)
                    reset_found = True
                    break
        
        # If not found in always_ff, check FSM macro (e.g., `PRIM_FLOP_SPARSE_FSM)
        if not reset_found:
            fsm_macro = re.search(r'`PRIM_FLOP_SPARSE_FSM\([^,]+,[^,]+,[^,]+,[^,]+,\s*(\w+)\)', module_source)
            if fsm_macro:
                fsm_info.reset_state = fsm_macro.group(1)
        
        # Mark initial and final states
        for s in fsm_info.states:
            if s.name == fsm_info.reset_state:
                s.is_initial = True
            if s.out_degree == 0 and len(fsm_info.states) > 1:
                s.is_final = True
        
        return fsm_info
    
    def analyze(self, fsm: FSMInfo) -> FSMAnalysisResult:
        """Analyze FSM."""
        if not fsm:
            return FSMAnalysisResult(fsm=FSMInfo(name=""))
        
        complexity = self.calculate_complexity(fsm)
        fsm.complexity_score = complexity
        unreachable = self.find_unreachable_states(fsm)
        deadlocks = self.find_deadlock_states(fsm)
        grade = self.grade_fsm(fsm)
        
        return FSMAnalysisResult(
            fsm=fsm,
            state_count=len(fsm.states),
            transition_count=len(fsm.transitions),
            complexity=complexity,
            unreachable_states=unreachable,
            dead_lock_states=deadlocks,
            has_initial_state=bool(fsm.reset_state),
            quality_grade=grade
        )
    
    def calculate_complexity(self, fsm: FSMInfo) -> int:
        if not fsm.states:
            return 0
        total = len(fsm.transitions)
        avg_out = total / len(fsm.states) if fsm.states else 0
        return int(len(fsm.states) * avg_out)
    
    def find_unreachable_states(self, fsm: FSMInfo) -> List[str]:
        if not fsm.states:
            return []
        initial = fsm.reset_state
        if not initial:
            for s in fsm.states:
                if s.is_initial:
                    initial = s.name
                    break
        if not initial:
            return []
        reachable = {initial}
        queue = deque([initial])
        while queue:
            current = queue.popleft()
            for t in fsm.transitions:
                if t.from_state == current and t.to_state not in reachable:
                    reachable.add(t.to_state)
                    queue.append(t.to_state)
        return [s.name for s in fsm.states if s.name not in reachable]
    
    def find_deadlock_states(self, fsm: FSMInfo) -> List[str]:
        return [s.name for s in fsm.states if not s.is_final and s.out_degree == 0]
    
    def suggest_encoding(self, fsm: FSMInfo) -> Dict[str, str]:
        n = len(fsm.states)
        if n <= 2:
            bits, typ = 1, "binary"
        elif n <= 4:
            bits, typ = 2, "binary"
        elif n <= 8:
            bits, typ = 3, "binary"
        elif n <= 16:
            bits, typ = 4, "gray"
        else:
            bits, typ = n, "one-hot"
        encoding = {}
        for i, s in enumerate(sorted(fsm.states, key=lambda x: x.name)):
            if typ == "binary":
                encoding[s.name] = format(i, f'0{bits}b')
            elif typ == "gray":
                encoding[s.name] = format(i ^ (i >> 1), f'0{bits}b')
            else:
                encoding[s.name] = '0' * i + '1' + '0' * (n - i - 1)
        return encoding
    
    def grade_fsm(self, fsm: FSMInfo) -> str:
        c = self.calculate_complexity(fsm)
        u = len(self.find_unreachable_states(fsm))
        d = len(self.find_deadlock_states(fsm))
        if c > 150 or u > 0 or d > 0:
            return "D"
        elif c > 100 or d > 0:
            return "C"
        elif c > 50:
            return "B"
        return "A"
    
    def get_report(self, result: FSMAnalysisResult) -> str:
        fsm = result.fsm
        lines = [
            "=" * 60,
            f"FSM ANALYSIS: {fsm.name}",
            "=" * 60,
            f"\nStatistics: States={result.state_count}, Transitions={result.transition_count}",
            f"Complexity={result.complexity}, Grade={result.quality_grade}",
            f"Reset State={fsm.reset_state or 'N/A'}",
        ]
        if result.complexity > 100:
            lines.append(f"\nWARNING: High Complexity ({result.complexity})")
        if result.unreachable_states:
            lines.append(f"\nUnreachable: {', '.join(result.unreachable_states)}")
        if result.dead_lock_states:
            lines.append(f"\nDeadlock: {', '.join(result.dead_lock_states)}")
        enc = self.suggest_encoding(fsm)
        lines.append(f"\nEncoding: {enc}")
        lines.append(f"\nStates:")
        for s in fsm.states[:10]:
            flags = []
            if s.is_initial:
                flags.append("INIT")
            if s.is_final:
                flags.append("FINAL")
            flag_str = f" [{','.join(flags)}]" if flags else ""
            lines.append(f"  {s.name}{flag_str} (in:{s.in_degree} out:{s.out_degree})")
        return "\n".join(lines)
