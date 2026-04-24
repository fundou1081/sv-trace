"""
SignalFlowAnalyzer - 统一信号流分析器 + 代码召回
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Set
import re


@dataclass
class FlowNode:
    signal_name: str = ""
    module: str = ""
    file: str = ""
    line: int = 0
    drivers: List[dict] = field(default_factory=list)
    loads: List[dict] = field(default_factory=list)
    controlling_signals: List[str] = field(default_factory=list)
    has_bit_selection: bool = False
    driven_bits: List[int] = field(default_factory=list)


@dataclass
class SignalFlow:
    root_signal: str = ""
    path: str = ""
    node: FlowNode = None
    upstream_signals: List[str] = field(default_factory=list)
    downstream_signals: List[str] = field(default_factory=list)
    code_snippets: List[dict] = field(default_factory=list)


def offset_to_line(content: str, offset: int) -> int:
    return len(content[:offset].split('\n'))


class ScopeExtractor:
    """Scope 代码召回器"""
    MAX_LINES = 40
    SCOPE_STARTS: Set[str] = {
        'always_ff', 'always_comb', 'always_latch',
        'function', 'task', 'module', 'interface', 'program', 'generate',
    }
    
    def __init__(self, parser):
        self.parser = parser
    
    def extract_with_scope(self, signal_name: str, max_lines: int = None) -> List[dict]:
        if max_lines is None:
            max_lines = self.MAX_LINES
        
        snippets = []
        
        for file_path, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            root = tree.root
            
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
            except:
                continue
            
            # 信号定义
            info = self._find_signal_location(root, signal_name, file_path, content)
            if info:
                snippet = self._extract_scope_code(
                    file_path, info['line'], signal_name, max_lines
                )
                if snippet:
                    snippets.append(snippet)
            
            # 信号赋值
            usage_lines = self._find_signal_usage(root, signal_name, content)
            for line in usage_lines:
                snippet = self._extract_scope_code(
                    file_path, line, signal_name, max_lines
                )
                if snippet and not any(s['target_line'] == line for s in snippets):
                    snippets.append(snippet)
        
        return snippets
    
    def _find_signal_location(self, root, signal_name: str, file_path: str, content: str) -> dict:
        members = getattr(root, 'members', None)
        if not members:
            return None
        
        for i in range(len(members)):
            member = members[i]
            if not member:
                continue
            
            if 'ModuleDeclaration' in str(type(member)):
                mod_members = getattr(member, 'members', None) or getattr(member, 'body', None)
                if not mod_members:
                    continue
                
                for j in range(len(mod_members)):
                    mm = mod_members[j]
                    if not mm:
                        continue
                    
                    if 'DataDeclaration' in str(type(mm)):
                        rng = getattr(mm, 'sourceRange', None)
                        if rng:
                            offset = rng.start.offset
                            line = offset_to_line(content, offset)
                            return {'file': file_path, 'line': line, 'offset': offset}
        
        return None
    
    def _find_signal_usage(self, root, signal_name: str, content: str) -> List[int]:
        lines = []
        
        def visit(node, depth=0):
            if depth > 20:
                return
            if not node:
                return
            
            if 'AssignmentExpression' in str(type(node)):
                left = getattr(node, 'left', None)
                if left:
                    try:
                        left_str = str(left).strip()
                        if signal_name == left_str or (left_str.startswith(signal_name + '[') and signal_name in left_str):
                            rng = getattr(node, 'sourceRange', None)
                            if rng:
                                lines.append(offset_to_line(content, rng.start.offset))
                    except:
                        pass
            
            for attr in ['members', 'body', 'statements', 'items', 'left', 'right', 
                       'expression', 'expressions', 'predicate', 'condition']:
                if hasattr(node, attr):
                    child = getattr(node, attr)
                    if child:
                        if isinstance(child, list):
                            for c in child:
                                visit(c, depth+1)
                        else:
                            visit(child, depth+1)
        
        visit(root)
        return list(set(lines))
    
    def _extract_scope_code(self, file_path: str, target_line: int,
                           signal_name: str, max_lines: int) -> dict:
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
        except:
            return None
        
        total_lines = len(lines)
        if target_line <= 0 or target_line > total_lines:
            return None
        
        scope_start = self._find_scope_start(lines, target_line)
        scope_end = self._find_scope_end(lines, target_line)
        
        start_line = max(0, scope_start - 1)
        end_line = min(total_lines, scope_end)
        actual_lines = end_line - start_line + 1
        
        # 带行号版本
        if actual_lines > max_lines:
            center = target_line - 1
            half = max_lines // 2
            new_start = max(0, center - half)
            new_end = min(total_lines, center + half)
            truncated = True
        else:
            new_start = start_line
            new_end = end_line
            truncated = False
        
        # 带行号代码
        code_with_line = []
        for i in range(new_start, new_end):
            code_with_line.append(f"{i + 1}: {lines[i].rstrip()}")
        code_with_line_num = '\n'.join(code_with_line)
        
        # 原文代码 (无行号)
        raw_lines = lines[new_start:new_end]
        raw_code = self._normalize_indent(''.join(raw_lines))
        
        scope_type = self._detect_scope_type(lines, scope_start)
        file_name = os.path.basename(file_path)
        
        return {
            'file': file_name,
            'full_path': file_path,
            'start_line': new_start + 1,
            'end_line': new_end,
            'target_line': target_line,
            'signal': signal_name,
            'code': code_with_line_num,      # 带行号
            'raw_code': raw_code,           # 原文
            'truncated': truncated,
            'scope_type': scope_type,
        }
    
    def _find_scope_start(self, lines: List[str], target_line: int) -> int:
        for i in range(target_line - 1, -1, -1):
            line = lines[i].strip()
            if line in self.SCOPE_STARTS:
                return i + 1
            for kw in self.SCOPE_STARTS:
                if line.startswith(kw):
                    return i + 1
            simple_kw = ['if ', 'case(', 'case ', 'for(', 'for ', 'while(', 'while ']
            for kw in simple_kw:
                if line.startswith(kw):
                    return i + 1
        return max(0, target_line - 1)
    
    def _find_scope_end(self, lines: List[str], target_line: int) -> int:
        line_count = len(lines)
        for i in range(target_line - 1, line_count):
            line = lines[i].strip()
            if line == 'end' or line.startswith('endcase') or line.startswith('endmodule') or \
               line.startswith('endfunction') or line.startswith('endtask'):
                return i + 1
        return min(line_count, target_line + 30)
    
    def _detect_scope_type(self, lines: List[str], line_num: int) -> str:
        for i in range(line_num - 1, -1, -1):
            line = lines[i].strip()
            if 'always_ff' in line: return 'always_ff'
            if 'always_comb' in line: return 'always_comb'
            if 'always_latch' in line: return 'always_latch'
            if 'function ' in line: return 'function'
            if 'task ' in line: return 'task'
            if 'module ' in line: return 'module'
            if 'interface ' in line: return 'interface'
            if line == 'begin' or 'begin' in line: return 'begin'
        return 'statement'
    
    def _normalize_indent(self, code: str) -> str:
        lines = code.split('\n')
        if not lines:
            return code
        min_indent = float('inf')
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                min_indent = min(min_indent, indent)
        if min_indent > 0 and min_indent != float('inf'):
            result = []
            for line in lines:
                if line.strip():
                    result.append(line[min_indent:])
                else:
                    result.append(line)
            return '\n'.join(result)
        return code


class SignalFlowAnalyzer:
    def __init__(self, parser):
        self.parser = parser
        self._driver = None
        self._load = None
        self._cf = None
        self._bs = None
    
    def _get_driver(self):
        if not self._driver:
            from .driver import DriverTracer
            self._driver = DriverTracer(self.parser)
        return self._driver
    
    def _get_load(self):
        if not self._load:
            from .load import LoadTracer
            self._load = LoadTracer(self.parser)
        return self._load
    
    def _get_cf(self):
        if not self._cf:
            from .controlflow import ControlFlowTracer
            self._cf = ControlFlowTracer(self.parser)
        return self._cf
    
    def _get_bs(self):
        if not self._bs:
            from .bitselect import BitSelectTracer
            self._bs = BitSelectTracer(self.parser)
        return self._bs
    
    def analyze(self, signal_path: str) -> SignalFlow:
        signal_name = signal_path.split('.')[-1]
        
        node = FlowNode(signal_name=signal_name)
        flow = SignalFlow(root_signal=signal_name, path=signal_path, node=node)
        
        drivers = self._get_driver().find_driver(signal_name)
        node.drivers = [{'kind': d.kind.name, 'expr': d.sources[0] if d.sources else ''} for d in drivers]
        
        for d in drivers:
            sigs = self._extract_signals(d.sources[0] if d.sources else '')
            for s in sigs:
                if s not in flow.upstream_signals and s != signal_name:
                    flow.upstream_signals.append(s)
        
        loads = self._get_load().find_load(signal_name)
        node.loads = [{'signal': l.signal_name} for l in loads]
        
        for l in loads:
            if l.context:
                sigs = self._extract_signals(l.context)
                for s in sigs:
                    if s not in flow.downstream_signals and s != signal_name:
                        flow.downstream_signals.append(s)
        
        cf = self._get_cf().find_control_dependencies(signal_name)
        node.controlling_signals = cf.controlling_signals
        
        bs = self._get_bs().trace_signal_with_bitselect(signal_name)
        node.has_bit_selection = bs['has_bit_selection']
        node.driven_bits = self._get_bs().get_driven_bits(signal_name)
        
        flow.code_snippets = ScopeExtractor(self.parser).extract_with_scope(signal_name)
        
        return flow
    
    def _extract_signals(self, expr: str) -> List[str]:
        if not expr:
            return []
        keywords = {
            'if', 'else', 'case', 'endcase', 'begin', 'end',
            'for', 'while', 'posedge', 'negedge', 'and', 'or', 'not',
            'null', '1', '0', 'true', 'false',
        }
        signals = []
        pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'
        for match in re.finditer(pattern, expr):
            name = match.group()
            if name not in keywords and name not in signals:
                signals.append(name)
        return signals
    
    def visualize(self, signal_path: str) -> str:
        flow = self.analyze(signal_path)
        node = flow.node
        
        lines = [f"=== Signal Flow: {signal_path} ==="]
        
        lines.append(f"\n[Drivers] ({len(node.drivers)})")
        for d in node.drivers:
            lines.append(f"  {d['kind']}: {d['expr'][:30]}")
        
        lines.append(f"\n[Loads] ({len(node.loads)})")
        for l in node.loads[:3]:
            lines.append(f"  {l.get('signal', 'unknown')}")
        
        if node.controlling_signals:
            lines.append(f"\n[Control] {node.controlling_signals}")
        
        if node.has_bit_selection:
            lines.append(f"\n[Bits] driven={node.driven_bits}")
        
        lines.append(f"\n[Data Flow]")
        if flow.upstream_signals:
            lines.append(f"  {flow.upstream_signals[0]} → {node.signal_name}")
        else:
            lines.append(f"  [constant] → {node.signal_name}")
        
        if flow.downstream_signals:
            lines.append(f"  {node.signal_name} → {flow.downstream_signals[0]}")
        else:
            lines.append(f"  {node.signal_name} → [unused]")
        
        # 代码片段 - 带行号
        lines.append(f"\n[Code with Line Numbers] ({len(flow.code_snippets)})")
        for snippet in flow.code_snippets:
            file_name = snippet.get('file', '')
            start = snippet.get('start_line', 0)
            end = snippet.get('end_line', 0)
            target = snippet.get('target_line', 0)
            scope_type = snippet.get('scope_type', 'unknown')
            
            lines.append(f"\n  📄 {file_name}:{start}-{end} (line {target})")
            lines.append(f"     Scope: {scope_type}")
            
            code = snippet.get('code', '')
            code_lines = [l for l in code.split('\n') if l]
            if len(code_lines) > 15:
                front = '\n'.join(code_lines[:8])
                back = '\n'.join(code_lines[-8:])
                lines.append(f"     Code:\n{front}\n     ...\n{back}")
            else:
                lines.append(f"     Code:\n{code}")
        
        # 代码片段 - 原文
        lines.append(f"\n[Code Raw] ({len(flow.code_snippets)})")
        for snippet in flow.code_snippets:
            file_name = snippet.get('file', '')
            start = snippet.get('start_line', 0)
            end = snippet.get('end_line', 0)
            scope_type = snippet.get('scope_type', 'unknown')
            
            lines.append(f"\n  📄 {file_name}:{start}-{end}")
            lines.append(f"     Scope: {scope_type}")
            
            raw = snippet.get('raw_code', '')
            raw_lines = [l for l in raw.split('\n') if l]
            if len(raw_lines) > 15:
                front = '\n'.join(raw_lines[:8])
                back = '\n'.join(raw_lines[-8:])
                lines.append(f"     Code:\n{front}\n     ...\n{back}")
            else:
                lines.append(f"     Code:\n{raw}")
        
        return '\n'.join(lines)


def analyze_signal(parser, signal_path: str):
    return SignalFlowAnalyzer(parser).analyze(signal_path)


def visualize_signal(parser, signal_path: str):
    return SignalFlowAnalyzer(parser).visualize(signal_path)
