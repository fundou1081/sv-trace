"""
Load Tracer - 追踪信号加载点 (使用 pyslang visit API)
"""
import pyslang
from pyslang import SyntaxKind
from typing import List
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.models import Load


class LoadTracer:
    """信号加载点追踪器"""
    
    def __init__(self, parser):
        self.parser = parser
        self.compilation = parser.compilation
        self._loads: List[Load] = []
        self._target_signal = ""
        self._current_module = ""
    
    def find_load(self, signal_name: str, module_name: str = None) -> List[Load]:
        """查找信号被加载的位置"""
        self._loads = []
        self._target_signal = signal_name
        self._current_module = module_name or ""
        
        for key, tree in self.parser.trees.items():
            if not tree or not tree.root:
                continue
            tree.root.visit(self._visit_callback)
        
        return self._loads
    
    def _visit_callback(self, node):
        """Visit callback for finding loads"""
        kind = node.kind
        
        # Track module name
        if kind == SyntaxKind.ModuleDeclaration:
            if hasattr(node, 'header') and hasattr(node.header, 'name'):
                self._current_module = str(node.header.name)
            return pyslang.VisitAction.Advance
        
        # Process always blocks
        if kind == SyntaxKind.AlwaysBlock:
            self._process_always_load(node)
            return pyslang.VisitAction.Skip  # Handle manually
        
        # Process always_ff/comb/latch blocks
        if kind in [SyntaxKind.AlwaysFFBlock, SyntaxKind.AlwaysCombBlock, SyntaxKind.AlwaysLatchBlock]:
            self._process_always_load(node)
            return pyslang.VisitAction.Skip
        
        # Process continuous assignments
        if kind == SyntaxKind.ContinuousAssign:
            self._process_continuous_assign_load(node)
            return pyslang.VisitAction.Advance
        
        return pyslang.VisitAction.Advance
    
    def _process_always_load(self, node):
        """Process always/always_ff/always_comb/always_latch block for loads"""
        try:
            if not hasattr(node, 'statement') or not node.statement:
                return
            
            stmt = node.statement
            stmt_kind = str(stmt.kind) if hasattr(stmt, 'kind') else ''
            
            # always_comb: statement 是 SequentialBlockStatement
            if 'SequentialBlockStatement' in stmt_kind or 'BlockStatement' in stmt_kind:
                self._walk_for_load(stmt)
            
            # always_ff/always_latch: statement 是 TimingControlStatement
            elif 'TimingControl' in stmt_kind:
                if hasattr(stmt, 'statement') and stmt.statement:
                    self._walk_for_load(stmt.statement)
                    
        except Exception as e:
            pass
    
    def _process_continuous_assign_load(self, node):
        """Process continuous assignment for loads"""
        try:
            if hasattr(node, 'assignments') and node.assignments:
                for i in range(len(node.assignments)):
                    assign = node.assignments[i]
                    self._check_rhs_for_load(assign)
        except Exception as e:
            pass
    
    def _walk_for_load(self, stmt):
        """Walk statement tree to find loads"""
        if stmt is None:
            return
        
        if not hasattr(stmt, 'kind'):
            return
        
        stmt_kind = str(stmt.kind)
        
        # Sequential block - iterate items
        if stmt_kind == 'SyntaxKind.SequentialBlockStatement':
            if hasattr(stmt, 'items'):
                for i in range(len(stmt.items)):
                    self._walk_for_load(stmt.items[i])
            return
        
        # Expression statement - check expr (not expression!)
        if stmt_kind == 'SyntaxKind.ExpressionStatement':
            if hasattr(stmt, 'expr') and stmt.expr:
                self._check_assignment_for_load(stmt.expr)
            return
        
        # If statement
        if 'If' in stmt_kind:
            # Check condition
            if hasattr(stmt, 'expr') and stmt.expr:
                self._check_expr_for_load(stmt.expr)
            # Recurse into branches
            if hasattr(stmt, 'statement') and stmt.statement:
                self._walk_for_load(stmt.statement)
            if hasattr(stmt, 'elseClause') and stmt.elseClause:
                self._walk_for_load(stmt.elseClause.clause)
            return
        
        # Case statement
        if 'Case' in stmt_kind:
            if hasattr(stmt, 'expr') and stmt.expr:
                self._check_expr_for_load(stmt.expr)
            if hasattr(stmt, 'items'):
                for i in range(len(stmt.items)):
                    case = stmt.items[i]
                    if hasattr(case, 'clause') and case.clause:
                        self._walk_for_load(case.clause)
            return
        
        # For loop
        if 'ForLoop' in stmt_kind:
            if hasattr(stmt, 'statement') and stmt.statement:
                self._walk_for_load(stmt.statement)
            return
        
        # While loop
        if 'WhileLoop' in stmt_kind:
            if hasattr(stmt, 'statement') and stmt.statement:
                self._walk_for_load(stmt.statement)
            return
    
    def _check_assignment_for_load(self, expr):
        """Check if assignment expression uses target signal"""
        if expr is None:
            return
        
        if not hasattr(expr, 'kind'):
            return
        
        kind_str = str(expr.kind)
        
        # Assignment expression - check RHS
        if 'Assignment' in kind_str or 'Nonblocking' in kind_str:
            if hasattr(expr, 'right') and expr.right:
                self._check_expr_for_load(expr.right)
            return
        
        # Other expressions - recurse
        self._check_expr_for_load(expr)
    
    def _check_expr_for_load(self, expr):
        """Check if expression contains target signal"""
        if expr is None:
            return
        
        if not hasattr(expr, 'kind'):
            return
        
        kind_str = str(expr.kind)
        
        # Identifier - check if it matches target signal
        if 'Identifier' in kind_str:
            name = str(expr).strip()
            # Handle array subscript: data_in[i] -> extract base name
            base_name = name.split('[')[0] if '[' in name else name
            if base_name == self._target_signal:
                self._add_load(str(expr), expr)
            # Don't return here - may need to handle parent expressions
        
        # ParenthesizedExpression - recurse into inner expression
        if 'Parenthesized' in kind_str:
            if hasattr(expr, 'inner') and expr.inner:
                self._check_expr_for_load(expr.inner)
            # Also check for 'expression' attribute (some pyslang versions)
            elif hasattr(expr, 'expression') and expr.expression:
                self._check_expr_for_load(expr.expression)
            return
        
        # InvocationExpression (function call) - extract all identifiers from the expression
        if 'Invocation' in kind_str:
            # 将整个表达式转为字符串，提取标识符
            expr_str = str(expr)
            # 简单提取所有单词作为潜在标识符
            import re
            identifiers = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', expr_str)
            for ident in identifiers:
                # 跳过关键字
                if ident in {'module', 'endmodule', 'function', 'endfunction', 'input', 'output',
                      'logic', 'reg', 'wire', 'always', 'begin', 'end', 'if', 'else',
                      'case', 'endcase', 'for', 'while', 'return', 'posedge', 'negedge',
                      'assign', 'parameter', 'localparam', 'genvar', 'signed', 'unsigned'}:
                    continue
                # 检查是否是目标信号
                if ident == self._target_signal:
                    self._add_load(ident, expr)
            return
        
        # ElementSelect (array[i]) - extract base name and check
        if 'ElementSelect' in kind_str:
            name = str(expr).strip()
            # Extract base name (before [)
            base_name = name.split('[')[0] if '[' in name else name
            if base_name == self._target_signal:
                self._add_load(str(expr), expr)
            # Also recurse into the selector for nested cases
            if hasattr(expr, 'selector') and expr.selector:
                self._check_expr_for_load(expr.selector)
            return
        
        # Binary/Arithmetic/Logic expression - check both sides
        if kind_str.endswith('Expression') or 'Binary' in kind_str:
            if hasattr(expr, 'left') and expr.left:
                self._check_expr_for_load(expr.left)
            if hasattr(expr, 'right') and expr.right:
                self._check_expr_for_load(expr.right)
            return
        
        # Conditional expression (?:)
        if 'Conditional' in kind_str:
            if hasattr(expr, 'predicate') and expr.predicate:
                self._check_expr_for_load(expr.predicate)
            if hasattr(expr, 'left') and expr.left:
                self._check_expr_for_load(expr.left)
            if hasattr(expr, 'right') and expr.right:
                self._check_expr_for_load(expr.right)
            return
        
        # Function call - check arguments
        if 'Call' in kind_str:
            if hasattr(expr, 'arguments') and expr.arguments:
                for i in range(len(expr.arguments)):
                    arg = expr.arguments[i]
                    if hasattr(arg, 'expr'):
                        self._check_expr_for_load(arg.expr)
            return
    
    def _check_rhs_for_load(self, assign):
        """Check if assignment RHS contains target signal"""
        if not hasattr(assign, 'right') or not assign.right:
            return
        
        rhs = assign.right
        self._check_expr_for_load(rhs)
    
    def _add_load(self, context: str, node):
        """Add a load record"""
        line = 0
        if hasattr(node, 'sourceRange') and node.sourceRange:
            try:
                line = node.sourceRange.start.offset if hasattr(node.sourceRange.start, 'offset') else 0
            except:
                line = 0
        
        load = Load(
            signal_name=self._target_signal,
            context=context,
            line=line,
            module=self._current_module.strip(),
            statement_type="",
            condition=""
        )
        
        self._loads.append(load)


# =============================================================================
# Enhanced Load Analysis - 使用正则表达式的备用分析器
# =============================================================================

import re
from typing import Set, Dict


class LoadTracerRegex:
    """
    基于正则表达式的信号负载追踪器
    作为LoadTracer的备用/增强方案
    """
    
    def __init__(self, parser):
        self.parser = parser
        self._code_cache: Dict[str, str] = {}
    
    def _get_code(self, filepath: str) -> str:
        """获取源码"""
        if filepath in self._code_cache:
            return self._code_cache[filepath]
        
        # 使用统一的get_source_safe方法
        from parse import get_source_safe
        code = get_source_safe(self.parser, filepath)
        if code:
            self._code_cache[filepath] = code
            return code
        
        return ""
    
    def _find_in_file(self, filepath: str, signal: str) -> List[Load]:
        """在单个文件中查找信号使用"""
        loads = []
        code = self._get_code(filepath)
        if not code:
            return loads
        
        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # 跳过注释
            if not stripped or stripped.startswith('//') or stripped.startswith('/*'):
                continue
            
            # 1. 时钟/复位事件 @(posedge signal) 或 @(negedge signal)
            if re.search(rf'@\s*\([^)]*\b{signal}\b', stripped):
                loads.append(Load(
                    signal_name=signal,
                    context=stripped[:100],
                    line=line_num,
                    condition="clock_event"
                ))
            
            # 2. 条件判断 if/else if
            if re.search(rf'\b(?:if|else\s+if)\s*\([^)]*\b{signal}\b[^)]*\)', stripped):
                loads.append(Load(
                    signal_name=signal,
                    context=stripped[:100],
                    line=line_num,
                    condition=signal
                ))
            
            # 3. case语句
            if re.search(rf'\bcase\s*\([^)]*\b{signal}\b[^)]*\)', stripped):
                loads.append(Load(
                    signal_name=signal,
                    context=stripped[:100],
                    line=line_num,
                    condition=signal
                ))
            
            # 4. 赋值右侧 (排除声明)
            if re.search(rf'\b{signal}\b\s*=', stripped):
                if not re.search(r'\b(?:logic|wire|reg|bit)\s+[^{]*\b(?:=|\Z)', stripped):
                    loads.append(Load(
                        signal_name=signal,
                        context=stripped[:100],
                        line=line_num
                    ))
            
            # 5. 三元表达式
            if re.search(rf'\b{signal}\s*\?', stripped):
                loads.append(Load(
                    signal_name=signal,
                    context=stripped[:100],
                    line=line_num
                ))
        
        return loads
    
    def find_load(self, signal_name: str, module_name: str = None) -> List[Load]:
        """查找信号被使用的所有位置"""
        all_loads = []
        
        for filepath in self.parser.trees.keys():
            loads = self._find_in_file(filepath, signal_name)
            all_loads.extend(loads)
        
        return all_loads
    
    def get_fanout(self, signal_name: str) -> int:
        """获取信号的直接扇出"""
        return len(self.find_load(signal_name))
    
    def get_all_signals(self) -> Set[str]:
        """提取所有信号名"""
        signals = set()
        keywords = {'if', 'else', 'case', 'for', 'while', 'do', 'begin', 'end',
                   'always', 'assign', 'logic', 'wire', 'reg', 'input', 'output',
                   'inout', 'module', 'parameter', 'localparam', 'typedef', 'enum',
                   'posedge', 'negedge', 'or', 'and', 'not', 'xor', 'force',
                   'generate', 'endgenerate', 'function', 'endfunction', 'task',
                   'endtask', 'class', 'endclass', 'package', 'endpackage'}
        
        for filepath in self.parser.trees.keys():
            code = self._get_code(filepath)
            if not code:
                continue
            
            # 提取信号声明
            for pattern in [
                r'\blogic\s*(?:\[[^\]]+\])?\s+([a-zA-Z_]\w*)',
                r'\bwire\s*(?:\[[^\]]+\])?\s+([a-zA-Z_]\w*)',
                r'\breg\s*(?:\[[^\]]+\])?\s+([a-zA-Z_]\w*)',
                r'\binput\s+(?:\[[^\]]+\])?\s+([a-zA-Z_]\w*)',
                r'\boutput\s+(?:\[[^\]]+\])?\s+([a-zA-Z_]\w*)',
            ]:
                for match in re.finditer(pattern, code):
                    sig = match.group(1)
                    if sig not in keywords:
                        signals.add(sig)
        
        return signals


# 添加便捷方法到LoadTracer类
def find_load_regex(self, signal_name: str, module_name: str = None) -> List[Load]:
    """使用正则表达式方式查找信号负载"""
    regex_tracer = LoadTracerRegex(self.parser)
    return regex_tracer.find_load(signal_name, module_name)

def get_fanout_regex(self, signal_name: str) -> int:
    """使用正则表达式方式获取扇出"""
    regex_tracer = LoadTracerRegex(self.parser)
    return regex_tracer.get_fanout(signal_name)

# 扩展LoadTracer类
LoadTracer.find_load_regex = find_load_regex
LoadTracer.get_fanout_regex = get_fanout_regex

__all__ = ['LoadTracer', 'LoadTracerRegex']
