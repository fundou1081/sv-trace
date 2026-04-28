"""
Coverage Stimulus Suggester
根据代码条件自动生成coverage激励和covergroup
"""
import pyslang
from pyslang import SyntaxKind
import re
from typing import List, Dict, Any


class Condition:
    def __init__(self, expr, type, branch, line=0):
        self.expr = expr
        self.type = type
        self.branch = branch
        self.line = line


class CoveragePoint:
    def __init__(self, id, condition, type, suggestions, line=0):
        self.id = id
        self.condition = condition
        self.type = type
        self.suggestions = suggestions
        self.line = line


class Stimulus:
    def __init__(self, name, description, input_values, expected):
        self.name = name
        self.description = description
        self.input_values = input_values
        self.expected = expected


class CoverageStimulusSuggester:
    def __init__(self, parser=None):
        self.parser = parser
        self.conditions = []
        self.coverage_points = []
        self.stimuli = []
        if parser:
            self._extract()
    
    def _extract(self):
        for key, tree in self.parser.trees.items():
            if not tree or not tree.root:
                continue
            self._find_conditions(tree.root)
    
    def extract_from_text(self, source: str):
        """从源码文本提取条件"""
        import pyslang
        
        try:
            tree = pyslang.SyntaxTree.fromText(source)
            if tree and tree.root:
                self._find_conditions(tree.root)
        except Exception as e:
            print(f"Parse error: {e}")
        
        return self
    
    def _find_conditions(self, node):
        # 使用visit遍历所有节点
        def callback(n):
            kind = n.kind
            if kind == SyntaxKind.ConditionalStatement:
                self._extract_if_condition(n)
            elif kind == SyntaxKind.CaseStatement:
                self._extract_case_branches(n)
            elif kind == SyntaxKind.ConditionalExpression:
                self._extract_ternary(n)
            return pyslang.VisitAction.Advance
        node.visit(callback)
    
    def _extract_if_condition(self, node):
        # 使用 predicate 获取条件
        if hasattr(node, 'predicate') and node.predicate:
            expr = str(node.predicate)
            self.conditions.append(Condition(expr, 'if', 'condition'))
        
        # 处理if body
        if hasattr(node, 'statement') and node.statement:
            self._find_conditions(node.statement)
        
        # 处理else
        if hasattr(node, 'elseClause') and node.elseClause:
            ec = node.elseClause
            if hasattr(ec, 'clause') and ec.clause:
                self._find_conditions(ec.clause)
            elif hasattr(ec, 'statement') and ec.statement:
                self._find_conditions(ec.statement)
    
    def _extract_case_branches(self, node):
        if hasattr(node, 'items') and node.items:
            for i in range(len(node.items)):
                item = node.items[i]
                self.conditions.append(Condition(f'case_{i}', 'case', f'case_{i}'))
                if hasattr(item, 'clause') and item.clause:
                    self._find_conditions(item.clause)
    
    def _extract_ternary(self, node):
        if hasattr(node, 'condition') and node.condition:
            self.conditions.append(Condition(str(node.condition), 'ternary', 'condition'))
    
    def get_coverage_points(self):
        if self.coverage_points:
            return self.coverage_points
        
        for i, cond in enumerate(self.conditions):
            point = CoveragePoint(
                f'cp_{i}',
                cond.expr,
                cond.type,
                self._generate_suggestions(cond),
                cond.line
            )
            self.coverage_points.append(point)
        return self.coverage_points
    
    def _generate_suggestions(self, cond):
        if cond.type == 'if':
            return [f"Set '{cond.expr}' to true (1)", f"Set '{cond.expr}' to false (0)"]
        elif cond.type == 'case':
            return [f"Cover branch '{cond.branch}'"]
        elif cond.type == 'ternary':
            return ["Set ternary to true", "Set ternary to false"]
        return []
    
    def suggest(self):
        if self.stimuli:
            return self.stimuli
        
        points = self.get_coverage_points()
        for i, point in enumerate(points):
            stimulus = Stimulus(
                f'stimulus_{i}',
                f"Cover: {point.condition}",
                self._extract_signals(point.condition),
                {}
            )
            self.stimuli.append(stimulus)
        return self.stimuli
    
    def _extract_signals(self, expr):
        signals = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', expr)
        keywords = {'if', 'else', 'case', 'end', 'begin', 'module', 'input', 'output', 'wire', 'reg', 'logic', 'posedge', 'negedge'}
        signals = [s for s in signals if s not in keywords]
        return dict((s, 0) for s in signals[:5])
    
    def generate_bins(self, signal, width=1, expr=''):
        """生成coverpoint的bins"""
        lines = []
        
        if width == 1:
            # 单bit
            lines.append(f"  {signal}_cp: coverpoint {signal} {{")
            lines.append("    bins one = {1'b1};")
            lines.append("    bins zero = {1'b0};")
            lines.append("  }")
        else:
            # 多bit
            w = width
            max_val = (1 << width) - 1
            lines.append(f"  {signal}_cp: coverpoint {signal} {{")
            lines.append(f"    bins zero = {{{w}'h0}};")
            lines.append(f"    bins max = {{{w}'h{max_val:x}}};")
            lines.append("    bins mid = {default};")
            lines.append("  }")
        
        # 间接信号带表达式
        if expr:
            lines.append(f"  // Derived: {expr}")
            lines.append(f"  {signal}_result: coverpoint ({expr}) {{")
            lines.append("    bins asserted = {1'b1};")
            lines.append("    bins deasserted = {1'b0};")
            lines.append("  }")
        
        return '\n'.join(lines)
    
    def generate_covergroup(self, module_name="dut") -> str:
        """生成SystemVerilog covergroup"""
        points = self.get_coverage_points()
        
        lines = []
        lines.append(f"// Auto-generated Covergroup for {module_name}")
        lines.append(f"covergroup cg_{module_name}(input {module_name} dut);")
        
        for point in points:
            if point.type == 'if':
                signals = self._extract_signals(point.condition)
                lines.append(f"  // Condition: {point.condition}")
                for sig in signals.keys():
                    lines.append(f"  {sig}: coverpoint dut.{sig} {{")
                    lines.append("    bins true = {1};")
                    lines.append("    bins false = {0};")
                    lines.append("  }")
                if len(signals) >= 2:
                    lines.append(f"  cross {', '.join(signals.keys())};")
            elif point.type == 'case':
                lines.append(f"  // Case branch: {point.branch}")
                lines.append(f"  case_branch: coverpoint dut.{point.condition} {{")
                lines.append("    bins default = {default};")
                lines.append("  }")
        
        lines.append("endgroup")
        lines.append("")
        lines.append(f"// cg_{module_name} cg = new(dut);")
        
        return '\n'.join(lines)
    
    def generate_coverpoint(self, signal_name, values=None):
        """生成单个coverpoint"""
        lines = [f"  {signal_name}_cp: coverpoint {signal_name} {{"]
        
        if values:
            for v in values:
                lines.append(f"    bins val_{v} = {{{v}}};")
        else:
            lines.append("    bins zero = {0};")
            lines.append("    bins one = {1};")
            lines.append("    bins default = {default};")
        
        lines.append("  }")
        return '\n'.join(lines)
    
    def analyze(self):
        return {
            'conditions': len(self.conditions),
            'coverage_points': len(self.get_coverage_points()),
            'stimuli': len(self.suggest()),
            'details': [
                {'id': p.id, 'condition': p.condition, 'type': p.type, 'suggestions': p.suggestions}
                for p in self.get_coverage_points()
            ]
        }




    def generate_illegal_bins(self, signal, illegal_values):
        """生成illegal bins用于不可能出现的情况"""
        lines = []
        lines.append(signal + '_cp: coverpoint ' + signal + ' {')
        lines.append('    bins valid = {default};')
        for val in illegal_values:
            lines.append('    illegal bins i_' + val + ' = {' + val + '};')
        lines.append('  }')
        lines.append('  // illegal: should never be hit')
        return chr(10).join(lines)

    def generate_ignore_bins(self, signal, ignore_values):
        """生成ignore bins用于不关心的值"""
        lines = []
        lines.append(signal + '_cp: coverpoint ' + signal + ' {')
        lines.append('    bins valid = {default};')
        for val in ignore_values:
            lines.append('    ignore_bins i_' + val + ' = {' + val + '};')
        lines.append('  }')
        return chr(10).join(lines)




    def generate_nested_if_coverage(self, conditions, module_name='dut'):
        """生成多层嵌套if的coverage (自动生成交叉coverage)"""
        lines = []
        lines.append('// Nested IF Coverage for ' + module_name)
        lines.append('covergroup cg_' + module_name + '(input ' + module_name + ' dut);')
        
        # 每个条件生成coverpoint
        for i, cond in enumerate(conditions):
            expr = cond.expr
            # 提取信号
            sigs = self._extract_signals(expr)
            for sig in sigs.keys():
                lines.append('  ' + sig + ': coverpoint dut.' + sig + ' {')
                lines.append('    bins ' + sig + '_true = {1};')
                lines.append('    bins ' + sig + '_false = {0};')
                lines.append('  }')
        
        # 生成嵌套深度交叉
        all_sigs = set()
        for cond in conditions:
            all_sigs.update(self._extract_signals(cond.expr).keys())
        
        all_sigs = list(all_sigs)
        
        if len(all_sigs) >= 2:
            lines.append('  // 嵌套深度 = ' + str(len(conditions)))
            lines.append('  cross ' + ', '.join(all_sigs) + ';')
        
        lines.append('endgroup')
        
        return chr(10).join(lines)


__all__ = ['CoverageStimulusSuggester', 'Condition', 'CoveragePoint', 'Stimulus']
