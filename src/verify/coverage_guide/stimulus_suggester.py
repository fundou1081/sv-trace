"""
Coverage Stimulus Suggester
根据代码条件自动生成coverage测试激励
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
    
    def _find_conditions(self, node):
        def callback(n):
            kind = n.kind
            if kind == SyntaxKind.IfStatement:
                self._extract_if_condition(n)
            elif kind == SyntaxKind.CaseStatement:
                self._extract_case_branches(n)
            elif kind == SyntaxKind.ConditionalExpression:
                self._extract_ternary(n)
            return pyslang.VisitAction.Advance
        node.visit(callback)
    
    def _extract_if_condition(self, node):
        if hasattr(node, 'checks') and node.checks:
            for check in node.checks:
                if hasattr(check, 'expr') and check.expr:
                    expr = str(check.expr)
                    self.conditions.append(Condition(expr, 'if', 'condition'))
        
        if hasattr(node, 'statement') and node.statement:
            self._find_conditions(node.statement)
        
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
        return {s: 0 for s in signals[:5]}
    
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


__all__ = ['CoverageStimulusSuggester', 'Condition', 'CoveragePoint', 'Stimulus']
