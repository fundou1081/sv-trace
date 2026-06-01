"""Constraint AST parser for SystemVerilog using pyslang.

Provides accurate parsing of constraint structures with:
- ConstraintBlock declarations
- Multiple constraint types (simple, implication, conditional, loop, dist, unique, solve_before)
- Soft constraints, Cross-class constraint references
- Constraint dependencies, Complex nested structures
- Visualization with Graphviz, Conflict detection with z3
"""

import pyslang
import graphviz
import re
import z3
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field


@dataclass
class ConstraintVariable:
    """A variable reference in a constraint."""
    name: str
    is_rand: bool = False
    line_number: int = 0


@dataclass
class ConstraintDetail:
    """Detailed constraint information."""
    name: str
    class_name: str
    constraint_type: str = "simple"
    variables: List[ConstraintVariable] = field(default_factory=list)
    line_number: int = 0
    is_soft: bool = False
    is_extern: bool = False
    parent_class: Optional[str] = None
    condition: str = ""
    then_expr: str = ""
    else_expr: str = ""
    nested_conditions: List[str] = field(default_factory=list)
    loop_var: str = ""
    loop_iterable: str = ""
    dist_items: List[str] = field(default_factory=list)
    antecedent: str = ""
    consequent: str = ""
    unique_vars: List[str] = field(default_factory=list)
    before_vars: List[str] = field(default_factory=list)
    after_vars: List[str] = field(default_factory=list)
    raw_expression: str = ""
    external_refs: List[str] = field(default_factory=list)


@dataclass
class ConstraintDependency:
    """Represents a dependency between constraints."""
    from_constraint: str
    to_constraint: str
    via_variable: str
    dependency_type: str


@dataclass
class Conflict:
    """Represents a conflict between constraints."""
    const1: str
    const2: str
    conflict_type: str  # unsatisfiable, redundant, cyclic
    description: str
    variables: List[str]



class ConstraintParserV2:
    """Parse constraint AST using pyslang for accurate parsing."""
    
    KEYWORDS = {
        'size', 'num', 'length', 'empty', 'delete', 'pop_back', 'pop_front',
        'push_back', 'push_front', 'insert', 'at', 'get', 'put', 'write', 'read',
        'reverse', 'sort', 'rsort', 'shuffle', 'find', 'find_index',
        'exists', 'max', 'min', 'sum', 'product', 'and', 'or', 'xor',
        'unique', 'clog2', 'inside', 'dist', 'weight', 'true', 'false',
        'solve', 'before', 'foreach', 'with', 'soft', 'if', 'else', 'new', 'null',
        'this', 'super', 'constraint', 'endconstraint', 'class', 'endclass',
        'extends', 'virtual', 'pure', 'static', 'function', 'endfunction',
        'task', 'endtask', 'typedef', 'enum', 'struct', 'bit', 'logic',
        'reg', 'wire', 'integer', 'int', 'byte', 'shortint', 'longint', 'void',
    }
    
    def __init__(self, parser):
        self.parser = parser
        self.classes: Dict[str, Dict] = {}
        self.constraints: Dict[str, ConstraintDetail] = {}
        self.dependencies: List[ConstraintDependency] = []
        self._parse()
    
    def _parse(self):
        self._extract_classes()
        self._extract_constraints()
        self._analyze_dependencies()
    
    def _extract_classes(self):
        from .class_extractor import ClassExtractor
        extractor = ClassExtractor(self.parser)
        for class_name, cls in extractor.classes.items():
            properties = {p.name: p for p in cls.properties}
            self.classes[class_name] = {
                'properties': properties,
                'extends': cls.extends,
                'info': cls
            }
    
    def _extract_constraints(self):
        for fname, tree in self.parser.trees.items():
            if not tree or not tree.root:
                continue
            source_code = str(tree.root) if tree.root else ""
            root = tree.root
            root_type = type(root).__name__
            
            if 'ClassDeclaration' in root_type:
                class_name = str(root.name).strip() if hasattr(root, 'name') and root.name else ""
                if class_name and class_name in self.classes:
                    property_names = set(self.classes[class_name]['properties'].keys())
                    extends = self.classes[class_name].get('extends')
                    if hasattr(root, 'items') and root.items:
                        for item in root.items:
                            if hasattr(item, 'kind') and str(item.kind) == 'SyntaxKind.ConstraintDeclaration':
                                self._parse_constraint_declaration(item, class_name, property_names, extends, source_code)
            elif 'CompilationUnit' in root_type:
                self._find_constraints_in_tree(root, fname, source_code)
    
    def _find_constraints_in_tree(self, node, filename, source_code=None):
        if 'ClassDeclaration' in type(node).__name__:
            self._extract_class_constraints(node, filename, source_code)
        if hasattr(node, 'members') and node.members:
            try:
                for child in node.members:
                    if hasattr(child, 'kind'):
                        self._find_constraints_in_tree(child, filename, source_code)
            except: pass
        if hasattr(node, 'items') and node.items:
            for child in node.items:
                if hasattr(child, 'kind'):
                    self._find_constraints_in_tree(child, filename, source_code)
    
    def _extract_class_constraints(self, class_node, filename, source_code=None):
        class_name = str(class_node.name).strip() if hasattr(class_node, 'name') and class_node.name else ""
        if not class_name or class_name not in self.classes:
            return
        property_names = set(self.classes[class_name]['properties'].keys())
        extends = self.classes[class_name].get('extends')
        if hasattr(class_node, 'items') and class_node.items:
            for item in class_node.items:
                if hasattr(item, 'kind') and str(item.kind) == 'SyntaxKind.ConstraintDeclaration':
                    self._parse_constraint_declaration(item, class_name, property_names, extends, source_code)
    
    def _parse_constraint_declaration(self, const_node, class_name, property_names, parent_class, source_code=None):
        const_name = str(const_node.name).strip() if hasattr(const_node, 'name') and const_node.name else ""
        if not const_name:
            return
        is_extern = False
        if hasattr(const_node, 'qualifiers') and const_node.qualifiers:
            if 'extern' in str(const_node.qualifiers).lower():
                is_extern = True
        line_number = 0
        if hasattr(const_node, 'sourceRange') and const_node.sourceRange and source_code:
            offset = const_node.sourceRange.start.offset
            line_number = source_code[:offset].count('\n') + 1
        
        detail = ConstraintDetail(
            name=const_name, class_name=class_name, constraint_type="simple",
            line_number=line_number, is_extern=is_extern, parent_class=parent_class
        )
        
        if hasattr(const_node, 'block') and const_node.block:
            if hasattr(const_node.block, 'items') and const_node.block.items:
                for block_item in const_node.block.items:
                    self._parse_constraint_item(block_item, detail, property_names)
        
        self.constraints[f"{class_name}.{const_name}"] = detail
    
    def _parse_constraint_item(self, item, detail, property_names):
        item_type = type(item).__name__
        raw = str(item).strip()
        detail.raw_expression = raw
        
        if 'ExpressionConstraint' in item_type:
            self._parse_expression_constraint(item, detail, property_names)
        elif 'ConditionalConstraint' in item_type:
            self._parse_conditional_constraint(item, detail, property_names)
        elif 'ImplicationConstraint' in item_type:
            self._parse_implication_constraint(item, detail, property_names)
        elif 'LoopConstraint' in item_type:
            self._parse_loop_constraint(item, detail, property_names)
        elif 'UniquenessConstraint' in item_type:
            self._parse_uniqueness_constraint(item, detail, property_names)
        elif 'SolveBeforeConstraint' in item_type:
            self._parse_solve_before_constraint(item, detail, property_names)
        else:
            detail.constraint_type = "simple"
            self._extract_variables(raw, detail, property_names)
    
    def _parse_expression_constraint(self, item, detail, property_names):
        raw = str(item)
        if 'soft' in raw.lower():
            detail.is_soft = True
            detail.constraint_type = "soft"
        expr = str(item.expr).strip() if hasattr(item, 'expr') else ""
        if hasattr(item, 'expression'):
            expr = str(item.expression).strip()
        detail.raw_expression = expr
        if 'dist' in expr.lower():
            detail.constraint_type = "dist"
            pattern = r'(\[.*?\]|\d+)\s*(:=|:/)\s*(\d+)'
            for m in re.findall(pattern, expr):
                detail.dist_items.append(f"{m[0]} :{m[1]} {m[2]}")
        if expr:
            self._extract_variables(expr, detail, property_names)
    
    def _parse_conditional_constraint(self, item, detail, property_names):
        detail.constraint_type = "conditional"
        if hasattr(item, 'condition') and item.condition:
            detail.condition = str(item.condition).strip()
        if hasattr(item, 'constraints') and item.constraints:
            detail.then_expr = str(item.constraints).strip()
            self._extract_variables(detail.then_expr, detail, property_names)
        if hasattr(item, 'elseClause') and item.elseClause:
            else_raw = str(item.elseClause).strip()
            detail.else_expr = else_raw[5:].strip() if else_raw.lower().startswith('else ') else else_raw
            self._extract_variables(detail.else_expr, detail, property_names)
    
    def _parse_implication_constraint(self, item, detail, property_names):
        detail.constraint_type = "implication"
        if hasattr(item, 'left') and item.left:
            detail.antecedent = str(item.left).strip()
        if hasattr(item, 'constraints') and item.constraints:
            detail.consequent = str(item.constraints).strip()
        self._extract_variables(detail.antecedent, detail, property_names)
        self._extract_variables(detail.consequent, detail, property_names)
    
    def _parse_loop_constraint(self, item, detail, property_names):
        detail.constraint_type = "loop"
        raw = str(item).strip()
        match = re.search(r'foreach\s*\(\s*(\w+)\s*\[\s*(\w+)\s*\]\s*\)', raw, re.IGNORECASE)
        if match:
            detail.loop_iterable = match.group(1)
            detail.loop_var = match.group(2)
        self._extract_variables(raw, detail, property_names)
    
    def _parse_uniqueness_constraint(self, item, detail, property_names):
        detail.constraint_type = "unique"
        raw = str(item).strip()
        match = re.search(r'unique\s*\{([^}]+)\}', raw)
        if match:
            for var in match.group(1).split(','):
                var = var.strip()
                if var and var in property_names:
                    detail.unique_vars.append(var)
        self._extract_variables(raw, detail, property_names)
    
    def _parse_solve_before_constraint(self, item, detail, property_names):
        detail.constraint_type = "solve_before"
        if hasattr(item, 'beforeExpr') and item.beforeExpr:
            detail.before_vars = [str(item.beforeExpr).strip()]
        if hasattr(item, 'afterExpr') and item.afterExpr:
            detail.after_vars = [str(item.afterExpr).strip()]
        for var in detail.before_vars + detail.after_vars:
            if var in property_names:
                detail.variables.append(ConstraintVariable(name=var, is_rand=False))
    
    def _extract_variables(self, expr, detail, property_names):
        pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
        matches = re.findall(pattern, expr)
        added = set()
        for var_name in matches:
            if var_name in added or var_name.lower() in self.KEYWORDS or var_name.isdigit():
                continue
            if var_name in property_names:
                added.add(var_name)
                is_rand = False
                if var_name in self.classes.get(detail.class_name, {}).get('properties', {}):
                    prop = self.classes[detail.class_name]['properties'][var_name]
                    is_rand = prop.rand_mode in ('rand', 'randc')
                detail.variables.append(ConstraintVariable(name=var_name, is_rand=is_rand))
            elif var_name in self._get_all_external_properties():
                detail.external_refs.append(var_name)
    
    def _get_all_external_properties(self):
        external = set()
        for class_info in self.classes.values():
            external.update(class_info['properties'].keys())
        return external
    
    def _analyze_dependencies(self):
        # Variable-based
        var_to_constraints: Dict[str, List[str]] = {}
        for key, const in self.constraints.items():
            for var in const.variables:
                if var.name not in var_to_constraints:
                    var_to_constraints[var.name] = []
                var_to_constraints[var.name].append(key)
        for var_name, const_keys in var_to_constraints.items():
            for i in range(len(const_keys)):
                for j in range(i+1, len(const_keys)):
                    self.dependencies.append(ConstraintDependency(
                        from_constraint=const_keys[i],
                        to_constraint=const_keys[j],
                        via_variable=var_name,
                        dependency_type="variable"
                    ))
        # Inheritance-based
        for key, const in self.constraints.items():
            if const.parent_class:
                parent_key = f"{const.parent_class}.{const.name}"
                if parent_key in self.constraints:
                    self.dependencies.append(ConstraintDependency(
                        from_constraint=key,
                        to_constraint=parent_key,
                        via_variable="",
                        dependency_type="override"
                    ))
    
    # ===== Query Methods =====
    
    def get_constraint(self, class_name: str, const_name: str):
        return self.constraints.get(f"{class_name}.{const_name}")
    
    def get_class_constraints(self, class_name: str) -> List[ConstraintDetail]:
        return [c for key, c in self.constraints.items() if c.class_name == class_name]
    
    def get_all_constraints(self) -> Dict[str, ConstraintDetail]:
        return self.constraints
    
    def find_overridden_constraints(self) -> List[ConstraintDetail]:
        return [c for c in self.constraints.values() if c.parent_class]
    
    def find_variable_in_constraints(self, var_name: str) -> List[ConstraintDetail]:
        return [c for c in self.constraints.values() if any(v.name == var_name for v in c.variables)]
    
    def get_constraint_type_summary(self) -> Dict[str, int]:
        summary = {}
        for const in self.constraints.values():
            ctype = const.constraint_type
            summary[ctype] = summary.get(ctype, 0) + 1
        return summary
    
    def get_inheritance_chain(self, class_name: str) -> List[str]:
        chain = [class_name]
        current = class_name
        while current in self.classes:
            extends = self.classes[current].get('extends')
            if extends:
                chain.append(extends)
                current = extends
            else:
                break
        return chain
    
    def get_cross_class_references(self, class_name: str) -> Dict[str, List[str]]:
        result = {}
        for const in self.get_class_constraints(class_name):
            if const.external_refs:
                for ref in const.external_refs:
                    for cls_name, cls_info in self.classes.items():
                        if ref in cls_info['properties']:
                            if cls_name not in result:
                                result[cls_name] = []
                            result[cls_name].append(ref)
        return result
    

    # ===== Visualization =====
    
    def visualize_relationships(self, filename="constraint_rel", format="png"):
        dot = graphviz.Graph(comment="Constraint Relationships", format=format)
        dot.attr(rankdir='TB', nodesep='0.5', ranksep='0.8')
        
        for class_name in sorted(self.classes.keys()):
            consts = self.get_class_constraints(class_name)
            if not consts:
                continue
            with dot.subgraph(name=f'cluster_{class_name}') as sub:
                sub.attr(label=f'Class: {class_name}', style='filled', color='#f0f0f0')
                class_props = self.classes[class_name]['properties']
                for prop_name in sorted(class_props.keys()):
                    prop = class_props[prop_name]
                    is_rand = "rand" in prop.rand_mode
                    shape = 'oval' if is_rand else 'box'
                    fillcolor = '#90EE90' if is_rand else '#FFB6C1'
                    sub.node(prop_name, prop_name, shape=shape, style='filled', fillcolor=fillcolor)
                for const in consts:
                    const_id = f"{class_name}.{const.name}"
                    fillcolor = {'soft': '#FFFF99', 'conditional': '#ADD8E6', 'implication': '#DDA0DD', 
                               'dist': '#FFA07A', 'loop': '#98FB98', 'unique': '#F0E68C'}.get(const.constraint_type, '#FFFFFF')
                    sub.node(const_id, const.name, shape='record', style='filled', fillcolor=fillcolor)
                for const in consts:
                    const_id = f"{class_name}.{const.name}"
                    for var in const.variables:
                        if var.name in class_props:
                            dot.edge(const_id, var.name, style='solid', color='#333333')
        return dot
    
    def visualize_dependency_graph(self, filename="dependency_graph", format="png"):
        dot = graphviz.Digraph(comment="Dependencies", format=format)
        dot.attr(rankdir='LR', nodesep='0.5')
        
        for key, const in self.constraints.items():
            fillcolor = {'soft': '#FFFF99', 'conditional': '#ADD8E6', 'implication': '#DDA0DD',
                       'dist': '#FFA07A', 'loop': '#98FB98', 'unique': '#F0E68C'}.get(const.constraint_type, '#FFFFFF')
            var_count = len(const.variables)
            label = f"{const.name}\\n({var_count} vars)"
            dot.node(key, label, shape='box', style='filled', fillcolor=fillcolor)
        
        for dep in self.dependencies:
            color = {'variable': '#333333', 'override': '#FF0000'}.get(dep.dependency_type, '#888888')
            dot.edge(dep.from_constraint, dep.to_constraint, label=dep.via_variable or dep.dependency_type, color=color)
        return dot
    
    def visualize_constraint_interaction(self, filename="interaction", format="png"):
        dot = graphviz.Digraph(comment="Interactions", format=format)
        dot.attr(rankdir='LR')
        
        var_to_constraints: Dict[str, List[str]] = {}
        for key, const in self.constraints.items():
            for var in const.variables:
                if var.name not in var_to_constraints:
                    var_to_constraints[var.name] = []
                var_to_constraints[var.name].append(key)
        
        for key, const in self.constraints.items():
            dot.node(key, const.name, shape='box', style='filled', fillcolor='#90EE90')
        
        for var_name, const_keys in var_to_constraints.items():
            if len(const_keys) > 1:
                dot.node(var_name, var_name, shape='ellipse', style='filled', fillcolor='#FFD700')
                for const_key in const_keys:
                    dot.edge(var_name, const_key, style='dashed')
        return dot


    
    def get_report(self) -> str:
        lines = ["=" * 70, "CONSTRAINT ANALYSIS REPORT (V2 - Enhanced)", "=" * 70]
        
        lines.append("\n[Constraint Types Summary]")
        for ctype, count in sorted(self.get_constraint_type_summary().items()):
            lines.append(f"  {ctype}: {count}")
        
        lines.append("\n[Constraints by Class]")
        for class_name in sorted(self.classes.keys()):
            consts = self.get_class_constraints(class_name)
            if consts:
                chain = self.get_inheritance_chain(class_name)
                chain_str = f" (extends: {' -> '.join(chain)})" if len(chain) > 1 else ""
                lines.append(f"\n  {class_name}{chain_str} ({len(consts)} constraints):")
                for const in consts:
                    var_names = [v.name for v in const.variables]
                    rand_vars = [v.name for v in const.variables if v.is_rand]
                    extra = []
                    if const.is_soft: extra.append("soft")
                    if const.is_extern: extra.append("extern")
                    if const.parent_class: extra.append(f"override:{const.parent_class}")
                    extra_str = f" [{', '.join(extra)}]" if extra else ""
                    lines.append(f"    {const.name}: [{const.constraint_type}]{extra_str}")
                    if var_names:
                        lines.append(f"      vars: {', '.join(var_names)}")
        
        lines.append("\n[Constraint Dependencies]")
        if self.dependencies:
            for dep in self.dependencies[:10]:
                lines.append(f"  {dep.from_constraint} -> {dep.to_constraint} ({dep.dependency_type})")
        else:
            lines.append("\n  (none)")
        
        return "\n".join(lines)


# ===== Conflict Detection with z3 =====
    
    def detect_conflicts(self):
        """Detect conflicts using z3 solver."""
        return ConflictDetector(self)



    # ===== Low Probability Analysis =====
    
    def analyze_low_probability(self) -> dict:
        """Analyze variables to find low-probability combinations."""
        return LowProbabilityAnalyzer(self).analyze()


class LowProbabilityAnalyzer:
    """Analyze constraint to find low-probability and dead zones."""
    
    def __init__(self, parser_v2):
        self.cp = parser_v2
        self.results = {}
    
    def analyze(self) -> dict:
        """Main analysis entry point."""
        for class_name in self.cp.classes:
            self.results[class_name] = self._analyze_class(class_name)
        return self.results
    
    def _analyze_class(self, class_name: str) -> dict:
        """Analyze a single class for low probability combinations."""
        import z3
        
        consts = self.cp.get_class_constraints(class_name)
        if not consts:
            return {}
        
        var_map = self._create_var_map(class_name)
        
        results = {
            'variables': {},
            'dead_zones': [],
            'tight_constraints': [],
            'combinations': [],
        }
        
        # Analyze each variable
        for var_name, z3_var in var_map.items():
            var_result = self._analyze_variable(var_name, z3_var, consts, var_map)
            results['variables'][var_name] = var_result
        
        # Find dead zones (values that can never be generated)
        results['dead_zones'] = self._find_dead_zones(class_name, consts, var_map)
        
        # Find tight constraints (that severely limit solutions)
        results['tight_constraints'] = self._find_tight_constraints(class_name, consts, var_map)
        
        # Find rare combinations
        results['combinations'] = self._find_rare_combinations(class_name, consts, var_map)
        
        return results
    
    def _create_var_map(self, class_name: str) -> dict:
        import z3
        var_map = {}
        if class_name in self.cp.classes:
            props = self.cp.classes[class_name]['properties']
            for prop_name, prop in props.items():
                width = prop.width if hasattr(prop, 'width') and prop.width else 8
                if width > 1:
                    var_map[prop_name] = z3.BitVec(prop_name, width)
                else:
                    var_map[prop_name] = z3.Int(prop_name)
        return var_map
    
    def _analyze_variable(self, var_name: str, z3_var, consts, var_map):
        """Analyze one variable in constraints."""
        import z3
        
        # Get constraints involving this variable
        relevant = [c for c in consts if any(v.name == var_name for v in c.variables)]
        
        if not relevant:
            return {'status': 'unconstrained', 'constraints': []}
        
        # Find min/max possible values
        solver = z3.Optimize()
        solver.add(z3.Bool('dummy'))
        
        # Add all relevant constraints
        for c in relevant:
            for const in relevant:
                constraints = self.cp.constraints
                for key, cd in constraints.items():
                    if cd.class_name == self.cp.get_class_constraints.__self__.classes.get(list(self.cp.classes.keys())[0], {}).get('class_name', ''):
                        pass
        
        # Try to find min/max
        min_solver = z3.Solver()
        max_solver = z3.Solver()
        
        for c in relevant:
            expr = self._expr_to_z3(c.raw_expression, var_map)
            if expr:
                min_solver.add(expr)
                max_solver.add(expr)
        
        min_val, max_val = None, None
        
        try:
            min_solver.add(z3_var <= 255)  # Assume 8 bit max
            if min_solver.check() == z3.sat:
                min_val = min_solver.model()[z3_var].as_long()
        except:
            pass
        
        try:
            max_solver.add(z3_var >= 0)
            if max_solver.check() == z3.sat:
                max_val = max_solver.model()[z3_var].as_long()
        except:
            pass
        
        return {
            'status': 'constrained',
            'constraints': [c.name for c in relevant],
            'min_value': min_val,
            'max_value': max_val,
            'range': (max_val - min_val) if min_val and max_val else None,
        }
    
    def _expr_to_z3(self, expr, var_map):
        import z3
        import re
        expr = expr.strip().rstrip(';')
        
        try:
            # Handle inside
            inside_match = re.search(r'(\w+)\s+inside\s+\{([^}]+)\}', expr)
            if inside_match:
                var = inside_match.group(1)
                ranges = inside_match.group(2)
                clauses = []
                for r in ranges.split(','):
                    r = r.strip()
                    if '[' in r:
                        m = re.search(r'\[(\d+):(\d+)\]', r)
                        if m and var in var_map:
                            clauses.append(z3.And(var_map[var] >= int(m.group(1)), 
                                             var_map[var] <= int(m.group(2))))
                    else:
                        try:
                            if var in var_map:
                                clauses.append(var_map[var] == int(r))
                        except:
                            pass
                if clauses:
                    return z3.Or(*clauses)
            
            if '>' in expr and '>=' not in expr:
                parts = expr.split('>')
                if len(parts) == 2 and parts[0].strip() in var_map:
                    return var_map[parts[0].strip()] > int(parts[1].strip())
            
            if '<' in expr and '<=' not in expr:
                parts = expr.split('<')
                if len(parts) == 2 and parts[0].strip() in var_map:
                    return var_map[parts[0].strip()] < int(parts[1].strip())
            
            return z3.Bool(expr)
        except:
            return z3.Bool(expr)
    
    def _find_dead_zones(self, class_name, consts, var_map):
        """Find values that can never be generated."""
        import z3
        
        dead_zones = []
        
        # For each variable, check each value in total range
        for var_name, z3_var in var_map.items():
            # Get total range (default 0-255 for 8-bit)
            max_range = 255  # Default for 8-bit
            if hasattr(z3_var, 'sort') and str(z3_var.sort()) == 'BitVec(8)':
                max_range = 255  # Default for 8-bit
            else:
                max_range = 255  # Default for 8-bit
            
            # Check some sample values
            samples = [0, 1, 2, max_range//2, max_range-1, max_range]
            
            for val in samples:
                solver = z3.Solver()
                
                # Add all constraints
                for const in consts:
                    expr = self._expr_to_z3(const.raw_expression, var_map)
                    if expr:
                        solver.add(expr)
                
                # Force this value
                solver.add(z3_var == val)
                
                if solver.check() == z3.unsat:
                    dead_zones.append({var_name: val})
        
        return dead_zones[:5]  # Return first 5 dead zones
    
    def _find_tight_constraints(self, class_name, consts, var_map):
        """Find constraints that severely limit solution space."""
        import z3
        
        tight = []
        
        for const in consts:
            solver = z3.Solver()
            
            # Check with this constraint
            expr = self._expr_to_z3(const.raw_expression, var_map)
            if expr:
                solver.add(expr)
                
                # Count solutions (sample)
                solutions = []
                for _ in range(1000):
                    if solver.check() == z3.sat:
                        model = solver.model()
                        solutions.append(model)
                        # Block this solution
                        block = z3.Or([var_map[v] == model[var_map[v]] for v in var_map if var_map[v] in model])
                        solver.add(block)
                    else:
                        break
                
                if len(solutions) < 10:
                    tight.append({
                        'constraint': const.name,
                        'possible_values': len(solutions),
                    })
        
        return tight
    
    def _find_rare_combinations(self, class_name, consts, var_map):
        """Find variable combinations that rarely appear together."""
        import z3
        
        # Get variable pairs used in constraints
        var_used = {}
        for const in consts:
            for var in const.variables:
                if var.name not in var_used:
                    var_used[var.name] = []
                var_used[var.name].append(const.name)
        
        # Find rare pairs
        rare = []
        for v1_name, v1_z3 in list(var_map.items())[:3]:
            for v2_name, v2_z3 in list(var_map.items())[1:]:
                if v1_name != v2_name:
                    solver = z3.Solver()
                    
                    # Add constraints involving both
                    for const in consts:
                        expr = self._expr_to_z3(const.raw_expression, var_map)
                        if expr:
                            solver.add(expr)
                    
                    # Count solutions
                    solutions = 0
                    for _ in range(100):
                        if solver.check() == z3.sat:
                            solutions += 1
                            model = solver.model()
                            block = z3.Or([var_map[v] == model[var_map[v]] for v in var_map if v in model])
                            solver.add(block)
                        else:
                            break
                    
                    if solutions < 10:
                        rare.append({
                            'vars': (v1_name, v2_name),
                            'solutions_found': solutions,
                        })
        
        return rare



class ConflictDetector:
    """Detect conflicts using z3 SMT solver."""
    
    def __init__(self, parser_v2):
        self.cp = parser_v2
        self.conflicts: List[Conflict] = []
        self._detect_conflicts()
    
    def _detect_conflicts(self):
        self._detect_unsatisfiable()
        self._detect_cyclic()
    

    def _expr_to_z3(self, expr: str, var_map: dict) -> Any:
        """Convert a constraint expression to z3 expression."""
        import z3
        
        expr = expr.strip().rstrip(';')
        
        try:
            # Handle inside { [min:max] } - convert to Or with And
            inside_match = re.search(r'(\w+)\s+inside\s+\{([^}]+)\}', expr)
            if inside_match:
                var = inside_match.group(1)
                ranges = inside_match.group(2)
                clauses = []
                for r in ranges.split(','):
                    r = r.strip()
                    if '[' in r:  # Range like [1:10]
                        match = re.search(r'\[(\d+):(\d+)\]', r)
                        if match:
                            lo, hi = int(match.group(1)), int(match.group(2))
                            if var in var_map:
                                clauses.append(z3.And(var_map[var] >= lo, var_map[var] <= hi))
                    else:  # Single value
                        try:
                            val = int(r)
                            if var in var_map:
                                clauses.append(var_map[var] == val)
                        except:
                            pass
                if clauses:
                    return z3.Or(*clauses)
            
            # Handle != (not equal)
            if ' != ' in expr:
                parts = expr.split(' != ')
                if len(parts) == 2 and parts[0] in var_map and parts[1] in var_map:
                    return var_map[parts[0]] != var_map[parts[1]]
                if len(parts) == 2 and parts[0] in var_map:
                    try:
                        val = int(parts[1].strip())
                        return var_map[parts[0].strip()] != val
                    except:
                        pass
            
            # Handle == (equal)
            if ' == ' in expr:
                parts = expr.split(' == ')
                if len(parts) == 2:
                    try:
                        left, right = parts[0].strip(), parts[1].strip()
                        if left in var_map:
                            try:
                                return var_map[left] == int(right)
                            except:
                                return var_map[left] == var_map[right]
                    except:
                        pass
            
            # Handle >= 
            if ' >= ' in expr:
                parts = expr.split(' >= ')
                if len(parts) == 2:
                    try:
                        left, right = parts[0].strip(), int(parts[1].strip())
                        if left in var_map:
                            return var_map[left] >= right
                    except:
                        pass
            
            # Handle <= 
            if ' <= ' in expr:
                parts = expr.split(' <= ')
                if len(parts) == 2:
                    try:
                        left, right = parts[0].strip(), int(parts[1].strip())
                        if left in var_map:
                            return var_map[left] <= right
                    except:
                        pass
            
            # Handle > 
            if ' > ' in expr and ' >= ' not in expr and ' -> ' not in expr:
                parts = expr.split(' > ')
                if len(parts) == 2:
                    try:
                        left, right = parts[0].strip(), int(parts[1].strip())
                        if left in var_map:
                            return var_map[left] > right
                    except:
                        pass
            
            # Handle < 
            if ' < ' in expr and ' <= ' not in expr and ' <- ' not in expr:
                parts = expr.split(' < ')
                if len(parts) == 2:
                    try:
                        left, right = parts[0].strip(), int(parts[1].strip())
                        if left in var_map:
                            return var_map[left] < right
                    except:
                        pass
            
            # Default - return as boolean
            return z3.Bool(expr)
        except Exception as e:
            return z3.Bool(expr)
    
    def _create_var_map(self, class_name: str) -> dict:
        """Create z3 variables for a class."""
        import z3
        
        var_map = {}
        if class_name in self.cp.classes:
            props = self.cp.classes[class_name]['properties']
            for prop_name, prop in props.items():
                # Determine sort based on data type
                dtype = prop.data_type.lower() if hasattr(prop, 'data_type') else 'int'
                width = prop.width
                
                if 'bit' in dtype or 'logic' in dtype:
                    if width and width > 1:
                        var_map[prop_name] = z3.BitVec(prop_name, width)
                    else:
                        var_map[prop_name] = z3.Bool(prop_name) if width == 1 else z3.Int(prop_name)
                elif 'int' in dtype or 'byte' in dtype or 'short' in dtype:
                    var_map[prop_name] = z3.Int(prop_name)
                else:
                    var_map[prop_name] = z3.Int(prop_name)
        
        return var_map

    def _detect_unsatisfiable(self):
        for class_name in self.cp.classes:
            consts = self.cp.get_class_constraints(class_name)
            if len(consts) < 1:
                continue
            
            # Create z3 variables for this class
            var_map = self._create_var_map(class_name)
            
            # Check all constraints together
            solver = z3.Solver()
            for const in consts:
                if const.raw_expression:
                    z3_expr = self._expr_to_z3(const.raw_expression, var_map)
                    if z3_expr is not None:
                        solver.add(z3_expr)
            
            result = solver.check()
            if result == z3.unsat:
                # Try to find which constraint is the problem (core)
                unsat_core = solver.unsat_core() if hasattr(solver, 'unsat_core') else []
                self.conflicts.append(Conflict(
                    const1=class_name,
                    const2="all",
                    conflict_type="unsatisfiable",
                    description=f"Class {class_name} has unsatisfiable constraints",
                    variables=[v.name for v in consts[0].variables]
                ))
            
            # Check pairwise
            for i in range(len(consts)):
                for j in range(i+1, len(consts)):
                    pair_solver = z3.Solver()
                    expr_i = self._expr_to_z3(consts[i].raw_expression, var_map)
                    expr_j = self._expr_to_z3(consts[j].raw_expression, var_map)
                    
                    if expr_i is not None and expr_j is not None:
                        pair_solver.add(expr_i)
                        pair_solver.add(expr_j)
                        
                        if pair_solver.check() == z3.unsat:
                            self.conflicts.append(Conflict(
                                const1=f"{class_name}.{consts[i].name}",
                                const2=f"{class_name}.{consts[j].name}",
                                conflict_type="unsatisfiable",
                                description=f"Cannot satisfy both: {consts[i].raw_expression[:30]} vs {consts[j].raw_expression[:30]}",
                                variables=list(set([v.name for v in consts[i].variables + consts[j].variables]))
                            ))
    
    def _detect_cyclic(self):
        graph: Dict[str, List[str]] = {}
        for dep in self.cp.dependencies:
            if dep.dependency_type == "variable":
                if dep.from_constraint not in graph:
                    graph[dep.from_constraint] = []
                graph[dep.from_constraint].append(dep.to_constraint)
        
        visited = set()
        rec_stack = set()
        
        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path = path + [node]
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    self.conflicts.append(Conflict(
                        const1=path[0],
                        const2=neighbor,
                        conflict_type="cyclic",
                        description="Cycle detected",
                        variables=[]
                    ))
                    return True
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
    
    def get_conflicts(self) -> List[Conflict]:
        return self.conflicts
    
    def get_report(self) -> str:
        lines = ["=" * 60, "CONSTRAINT CONFLICT ANALYSIS (z3-based)", "=" * 60]
        
        if not self.conflicts:
            lines.append("\nNo conflicts detected!")
            return "\n".join(lines)
        
        by_type = {}
        for c in self.conflicts:
            if c.conflict_type not in by_type:
                by_type[c.conflict_type] = []
            by_type[c.conflict_type].append(c)
        
        for ctype, clist in sorted(by_type.items()):
            lines.append(f"\n[{ctype.upper()} - {len(clist)}]:")
            for c in clist:
                lines.append(f"  {c.const1} <-> {c.const2}")
                lines.append(f"    {c.description}")
        
        return "\n".join(lines)


    # ===== Report =====
    
    def get_report(self) -> str:
        lines = ["=" * 70, "CONSTRAINT ANALYSIS REPORT (V2 - Enhanced)", "=" * 70]
        
        lines.append("\n[Constraint Types Summary]")
        for ctype, count in sorted(self.get_constraint_type_summary().items()):
            lines.append(f"  {ctype}: {count}")
        
        lines.append("\n[Constraints by Class]")
        for class_name in sorted(self.classes.keys()):
            consts = self.get_class_constraints(class_name)
            if consts:
                chain = self.get_inheritance_chain(class_name)
                chain_str = f" (extends: {' -> '.join(chain)})" if len(chain) > 1 else ""
                lines.append(f"\n  {class_name}{chain_str} ({len(consts)} constraints):")
                for const in consts:
                    var_names = [v.name for v in const.variables]
                    rand_vars = [v.name for v in const.variables if v.is_rand]
                    extra = []
                    if const.is_soft: extra.append("soft")
                    if const.is_extern: extra.append("extern")
                    if const.parent_class: extra.append(f"override:{const.parent_class}")
                    if const.condition: extra.append(f"if:{const.condition[:20]}")
                    extra_str = f" [{', '.join(extra)}]" if extra else ""
                    lines.append(f"    {const.name}: [{const.constraint_type}]{extra_str}")
                    if var_names:
                        lines.append(f"      vars: {', '.join(var_names)}")
        
        lines.append("\n[Constraint Dependencies]")
        if self.dependencies:
            by_type = {}
            for dep in self.dependencies:
                if dep.dependency_type not in by_type:
                    by_type[dep.dependency_type] = []
                by_type[dep.dependency_type].append(dep)
            for dtype, dlist in sorted(by_type.items()):
                lines.append(f"\n  {dtype} ({len(dlist)}):")
                for d in dlist[:10]:
                    lines.append(f"    {d.from_constraint} -> {d.to_constraint}")
        else:
            lines.append("\n  (none)")
        
        return "\n".join(lines)


    def graph_analysis(self) -> dict:
        """Analyze constraints using graph theory."""
        import collections
        
        results = {'scc': [], 'critical': [], 'influence': {}, 'communities': []}
        if not self.constraints:
            return results
        
        # Build adjacency
        adj = collections.defaultdict(list)
        radj = collections.defaultdict(list)
        for dep in self.dependencies:
            adj[dep.from_constraint].append(dep.to_constraint)
            radj[dep.to_constraint].append(dep.from_constraint)
        
        # Find SCCs
        results['scc'] = self._find_scc(adj)
        results['influence'] = self._calculate_influence(adj, radj)
        for node, score in sorted(results['influence'].items(), key=lambda x: -x[1])[:3]:
            results['critical'].append({'constraint': node, 'score': score})
        return results
    
    def _find_scc(self, adj):
        """Find strongly connected components."""
        visited, stack, indices = set(), [], {}
        low, index_counter = {}, [0]
        sccs = []
        
        def dfs(v):
            indices[v] = low[v] = index_counter[0]
            index_counter[0] += 1
            stack.append(v)
            visited.add(v)
            for w in adj.get(v, []):
                if w not in indices:
                    dfs(w)
                    low[v] = min(low[v], low[w])
                elif w in stack:
                    low[v] = min(low[v], indices[w])
            if low[v] == indices[v]:
                scc = []
                while True:
                    w = stack.pop()
                    scc.append(w)
                    if w == v:
                        break
                if len(scc) > 1:
                    sccs.append(scc)
        
        for node in adj:
            if node not in visited:
                dfs(node)
        return sccs
    
    def _calculate_influence(self, adj, radj):
        """Calculate influence scores."""
        all_nodes = set(adj.keys()) | set(radj.keys())
        scores = {n: 1.0 for n in all_nodes}
        
        for _ in range(20):
            new_scores = {}
            for node in all_nodes:
                incoming = radj.get(node, [])
                new_scores[node] = sum(scores.get(n, 0) for n in incoming) / max(len(incoming), 1)
            scores = new_scores
        return {k: round(v, 2) for k, v in scores.items() if v != 1.0}
    

def parse_constraints(parser):
    return ConstraintParserV2(parser)

