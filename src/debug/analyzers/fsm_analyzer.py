"""FSMAnalyzer - 状态机深度分析器。

基于 IEEE 1800-2017 Section 40.4 标准，使用 pyslang AST 提取和分析状态机。

标准支持:
- 40.4.1: tool state_vector signal_name [enum]
- 40.4.2: tool state_vector signal[n:n] FSM_name enum
- 40.4.3: tool state_vector {sig1,sig2,...} FSM_name enum  
- 40.4.4: tool enum enumeration_name (next state)
- 40.4.5: 双信号声明 (第一个current, 第二个next)
- Fallback: 模式识别CaseStatement

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
    next_signal: str = ""
    states: List[StateInfo] = field(default_factory=list)
    transitions: List[Transition] = field(default_factory=list)
    encoding: Dict[str, str] = field(default_factory=dict)
    reset_state: str = ""
    complexity_score: int = 0
    fsm_name: str = ""
    source_type: str = "unknown"  # pragma_40.4.1, pragma_40.4.2, etc.


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
    """状态机深度分析器 - 基于 IEEE 1800-2017 Section 40.4"""
    
    def __init__(self, parser):
        self.parser = parser
        self.fsms: Dict[str, FSMInfo] = {}
    
    def _walk(self, node):
        """Walk SyntaxNodes, skipping Tokens."""
        try:
            for child in node:
                yield child
                yield from self._walk(child)
        except TypeError:
            pass
    
    def _get_module_tree(self, module_name: str):
        """Get AST tree for a specific module."""
        import pyslang
        for fname in self.parser.trees.keys():
            try:
                with open(fname, 'r') as f:
                    content = f.read()
            except:
                continue
            
            if f'module {module_name}' in content:
                try:
                    tree = pyslang.SyntaxTree.fromText(content)
                    return tree
                except:
                    continue
        return None
    
    def _check_pragma(self, root) -> Tuple[Optional[dict], Optional[str], Optional[str]]:
        """Check for IEEE 1800-2017 Section 40.4 pragmas.
        
        Returns:
            (pragma_info dict, enum_name, fsm_name)
            
        pragma_info contains:
            - state_vector: signal name or part-select or concatenation
            - is_part_select: bool
            - is_concat: bool  
            - next_signal: optional next state signal
        """
        info = {
            'state_vector': None,
            'is_part_select': False,
            'is_concat': False,
            'next_signal': None,
            'source': None,
            'has_enum': False
        }
        enum_name = None
        fsm_name = None
        
        try:
            text = str(root)
            
            # Pattern 40.4.1: /* tool state_vector signal_name [enum name] */
            m = re.search(r'/\*\s*tool state_vector\s+(\w+)\s*(?:enum\s+(\w+))?\s*\*/', text)
            if m:
                info['state_vector'] = m.group(1)
                info['source'] = '40.4.1'
                if m.group(2):
                    enum_name = m.group(2)
                    info['has_enum'] = True
            
            # Pattern 40.4.2: /* tool state_vector signal[n:n] FSM_name enum name */
            if not info['state_vector']:
                m = re.search(r'/\*\s*tool state_vector\s+(\w+)\[(\d+):(\d+)\]\s+(\w+)\s+enum\s+(\w+)\s*\*/', text)
                if m:
                    info['state_vector'] = m.group(1)
                    info['is_part_select'] = True
                    info['source'] = '40.4.2'
                    fsm_name = m.group(4)
                    enum_name = m.group(5)
                    info['has_enum'] = True
            
            # Pattern 40.4.3: /* tool state_vector {sig1,sig2,...} FSM_name enum name */
            if not info['state_vector']:
                m = re.search(r'/\*\s*tool state_vector\s+\{(\w+(?:,\w+)*)\}\s+(\w+)\s+enum\s+(\w+)\s*\*/', text)
                if m:
                    info['state_vector'] = m.group(1)
                    info['is_concat'] = True
                    info['source'] = '40.4.3'
                    fsm_name = m.group(2)
                    enum_name = m.group(3)
                    info['has_enum'] = True
            
            # Pattern 40.4.5: separate signal declaration with pragma
            # /* tool state_vector cs */ logic... cs, ns, ...
            if not info['state_vector']:
                m = re.search(r'/\*\s*tool state_vector\s+(\w+)\s*\*/\s*logic.*?(\w+)\s*,\s*(\w+)', text)
                if m:
                    info['state_vector'] = m.group(1)
                    # Assume first signal is current, second is next
                    info['next_signal'] = m.group(3)
                    info['source'] = '40.4.5'
            
            # Pattern: /* tool enum enumeration_name */ for next state (40.4.4)
            if not enum_name:
                m = re.search(r'/\*\s*tool enum\s+(\w+)\s*\*/', text)
                if m:
                    enum_name = m.group(1)
                    info['has_enum'] = True
                    if not info['source']:
                        info['source'] = '40.4.4'
        
        except:
            pass
        
        return info, enum_name, fsm_name
    
    def _check_enum(self, root, enum_name: str) -> List[str]:
        """Extract states from enum declaration (40.4.6)."""
        if not enum_name:
            return []
        
        states = []
        
        for node in self._walk(root):
            if node.kind.name == 'EnumDeclaration':
                name = str(node.name).strip() if hasattr(node, 'name') else ''
                if name == enum_name:
                    for child in self._walk(node):
                        if child.kind.name == 'EnumConstant':
                            states.append(str(child).strip())
                    break
        
        return states
    
    def _extract_target_from_clause(self, clause, next_var: str) -> Optional[str]:
        """Extract target state from a case item clause."""
        if not clause:
            return None
        for node in self._walk(clause):
            if node.kind.name == 'AssignmentExpression':
                left = str(node.left).strip() if hasattr(node, 'left') else ''
                right = str(node.right).strip() if hasattr(node, 'right') else ''
                if left == next_var:
                    if '?' in right:
                        right = right.split('?')[1].split(':')[0].strip()
                    return right
        return None
    
    def _find_next_state_from_declaration(self, root, current_signal: str) -> Optional[str]:
        """Find next state signal from signal declaration (40.4.5)."""
        # Look for: signal_name, next_signal in same declaration
        # Pattern: current_signal, next_signal in logic/reg declaration
        try:
            text = str(root)
            pattern = rf'(\b{re.escape(current_signal)}\b),?(\s+\w+){{1,3}},?(\s+\w+)'
            for m in re.finditer(pattern, text):
                if m.lastindex() >= 3:
                    return m.group(3).strip()
        except:
            pass
        return None
    
    def _extract_fsm_from_ast(self, tree) -> Optional[FSMInfo]:
        """Extract FSM from AST per IEEE 1800-2017 Section 40.4."""
        root = tree.root
        state_var = None
        next_var = None
        reset_state = None
        transitions = []
        source_type = "unknown"
        fsm_name = ""
        
        # Step 1: Check for IEEE 1800-2017 Section 40.4 Pragma
        pragma_info, enum_name, fsm_name = self._check_pragma(root)
        
        if pragma_info and pragma_info.get('state_vector'):
            state_var = pragma_info['state_vector']
            source_type = pragma_info.get('source', '40.4.1')
            
            # Get enum states if available
            enum_states = []
            if enum_name:
                enum_states = self._check_enum(root, enum_name)
            
            # Find next state signal (40.4.4, 40.4.5)
            if pragma_info.get('next_signal'):
                next_var = pragma_info['next_signal']
            else:
                # Try to find from declaration (40.4.5)
                next_var = self._find_next_state_from_declaration(root, state_var)
                if not next_var:
                    next_var = state_var.replace('_q', '_d') if state_var.endswith('_q') else state_var + '_d'
            
            # If we have enum states, extract transitions
            if enum_states and state_var:
                # Find CaseStatement for this state machine
                for node in self._walk(root):
                    if node.kind.name == 'CaseStatement':
                        case_expr = str(node.expr).strip() if hasattr(node, 'expr') else ''
                        if case_expr == state_var:
                            for item in self._walk(node.items):
                                if item.kind.name == 'StandardCaseItem':
                                    sname = None
                                    for expr in item.expressions:
                                        sn = str(expr).strip()
                                        if sn and not sn.startswith('//'):
                                            sname = sn
                                            break
                                    if sname and hasattr(item, 'clause'):
                                        target = self._extract_target_from_clause(item.clause, next_var or state_var)
                                        if target:
                                            transitions.append(Transition(
                                                from_state=sname,
                                                to_state=target
                                            ))
                            break
        
        # Step 2: Fallback - Pattern matching (CaseStatement)
        if not state_var:
            for node in self._walk(root):
                if node.kind.name == 'CaseStatement':
                    case_expr = str(node.expr).strip() if hasattr(node, 'expr') else ''
                    
                    # Skip one-hot style: case(1'b1) - skip for now
                    if case_expr == "1'b1":
                        continue
                    
                    if case_expr and (case_expr.endswith('_q') or '_state' in case_expr.lower()):
                        source_type = 'pattern'
                        state_var = case_expr
                        
                        # Find next_var
                        for nn in self._walk(root):
                            if nn.kind.name in ['AlwaysCombBlock', 'AlwaysBlock']:
                                for aa in self._walk(nn):
                                    if aa.kind.name == 'AssignmentExpression':
                                        left = str(aa.left).strip() if hasattr(aa, 'left') else ''
                                        if left == 'state_d':
                                            next_var = left
                                            break
                                if next_var:
                                    break
                        break
        
        if not state_var:
            return None
        
        # Find CaseStatement to extract transitions
        case_stmt = None
        for node in self._walk(root):
            if node.kind.name == 'CaseStatement':
                case_expr = str(node.expr).strip() if hasattr(node, 'expr') else ''
                if case_expr == state_var:
                    case_stmt = node
                    break
        
        if not case_stmt:
            return None
        
        # Extract transitions from case items
        for node in self._walk(case_stmt.items):
            if node.kind.name == 'StandardCaseItem':
                state_name = None
                for expr in node.expressions:
                    sn = str(expr).strip()
                    if sn and not sn.startswith('//'):
                        state_name = sn
                        break
                
                if state_name and hasattr(node, 'clause'):
                    target = self._extract_target_from_clause(node.clause, next_var or state_var)
                    if target:
                        transitions.append(Transition(
                            from_state=state_name,
                            to_state=target
                        ))
        
        if not transitions:
            return None
        
        # Find reset state from always_ff
        for node in self._walk(root):
            if node.kind.name == 'AlwaysFFBlock':
                for inner in self._walk(node):
                    if inner.kind.name == 'NonblockingAssignmentExpression':
                        left = str(inner.left).strip() if hasattr(inner, 'left') else ''
                        right = str(inner.right).strip() if hasattr(inner, 'right') else ''
                        if left == state_var:
                            reset_state = right
                            break
                if reset_state:
                    break
        
        # Build FSMInfo
        fsm_info = FSMInfo(
            name=state_var,
            register_signal=state_var,
            next_signal=next_var or "",
            reset_state=reset_state,
            source_type=source_type,
            fsm_name=fsm_name or ""
        )
        fsm_info.transitions = transitions
        
        # Infer states
        state_names = set()
        for t in transitions:
            state_names.add(t.from_state)
            state_names.add(t.to_state)
        
        in_deg = defaultdict(int)
        out_deg = defaultdict(int)
        for t in transitions:
            out_deg[t.from_state] += 1
            in_deg[t.to_state] += 1
        
        for name in sorted(state_names):
            si = StateInfo(name=name)
            si.in_degree = in_deg.get(name, 0)
            si.out_degree = out_deg.get(name, 0)
            if name == reset_state:
                si.is_initial = True
            fsm_info.states.append(si)
        
        return fsm_info
    
    def extract_fsm(self, module_name: str, state_register: str = None) -> Optional[FSMInfo]:
        """Extract FSM from module."""
        tree = self._get_module_tree(module_name)
        if not tree:
            return None
        
        return self._extract_fsm_from_ast(tree)
    
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
            f"\nIEEE 1800-2017 Section 40.4 Source: {fsm.source_type}",
        ]
        if fsm.fsm_name:
            lines.append(f"FSM Name: {fsm.fsm_name}")
        lines.extend([
            f"Statistics: States={result.state_count}, Transitions={result.transition_count}",
            f"Complexity={result.complexity}, Grade={result.quality_grade}",
            f"Reset State={fsm.reset_state or 'N/A'}",
        ])
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
