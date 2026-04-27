"""TB Complexity Analyzer - Comprehensive metrics for testbench quality"""

import re
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field


@dataclass
class TBMetrics:
    """TB complexity metrics - comprehensive"""
    # Line counts
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    
    # Parameter usage
    parameter_count: int = 0
    localparam_count: int = 0
    param_usage_ratio: float = 0.0
    
    # Class metrics
    class_count: int = 0
    class_hierarchy_depth: int = 0
    class_names: List[str] = field(default_factory=list)
    
    # Inheritance
    extends_count: int = 0
    implements_count: int = 0
    parent_classes: List[str] = field(default_factory=list)
    
    # Class references (non-inheritance)
    class_refs: Dict[str, List[str]] = field(default_factory=dict)
    class_instance_map: Dict[str, List[str]] = field(default_factory=dict)
    class_graph_edges: List[Tuple[str, str]] = field(default_factory=list)
    class_graph_nodes: List[str] = field(default_factory=list)
    
    # Random variables
    rand_count: int = 0
    randc_count: int = 0
    rand_vars: List[str] = field(default_factory=list)
    rand_var_types: Dict[str, str] = field(default_factory=dict)
    
    # Random variable relationships
    rand_constraint_map: Dict[str, List[str]] = field(default_factory=dict)
    constraint_rand_map: Dict[str, str] = field(default_factory=dict)
    rand_relations: List[Tuple[str, str]] = field(default_factory=list)
    
    # Nesting
    max_nesting: int = 0
    avg_nesting: float = 0.0
    
    # UVM Components - detailed
    agent_count: int = 0
    driver_count: int = 0
    monitor_count: int = 0
    sequencer_count: int = 0
    scoreboard_count: int = 0
    reference_model_count: int = 0
    subscriber_count: int = 0
    constraint_count: int = 0
    assertion_count: int = 0
    assertion_lines: int = 0
    force_count: int = 0
    covergroup_count: int = 0
    sequence_count: int = 0
    virtual_seq_count: int = 0
    config_db_get: int = 0
    config_db_set: int = 0
    
    # Macro definitions
    define_count: int = 0
    define_names: List[str] = field(default_factory=list)
    ifdef_count: int = 0
    
    # Assertion types
    assert_property_count: int = 0
    assert_sequence_count: int = 0
    assert_static_count: int = 0
    
    # Sequence hierarchy
    sequence_body_lines: int = 0
    sequence_items: int = 0
    sequence_hierarchy_depth: int = 0
    nested_sequence_count: int = 0
    sequence_macro_count: int = 0
    fork_join_count: int = 0
    send_port_count: int = 0
    get_try_count: int = 0
    wait_count: int = 0
    
    # Factory
    factory_create_count: int = 0
    uvm_object_utils_count: int = 0
    uvm_component_utils_count: int = 0
    
    # Imports
    import_count: int = 0
    include_count: int = 0
    
    # Complexity
    complexity_score: float = 0.0
    complexity_grade: str = "A"
    
    # Issues
    issues: List[str] = field(default_factory=list)
    # Packages
    package_count: int = 0
    package_names: List[str] = field(default_factory=list)
    package_imports: Dict[str, List[str]] = field(default_factory=dict)
    
    # Functions/Tasks
    function_count: int = 0
    task_count: int = 0
    
    # Randomization
    randomize_count: int = 0
    
    # Transactions
    deep_copy_count: int = 0
    clone_count: int = 0
    
    # Interfaces/Ports
    interface_count: int = 0
    port_count: int = 0
    
    # Memory/Arrays
    memory_array_count: int = 0
    memory_size_sum: int = 0
    
    # FSM
    fsm_state_count: int = 0



class TBComplexityAnalyzer:
    """Analyze testbench complexity with comprehensive metrics"""
    
    def __init__(self, code: str = None, filepath: str = None):
        self.code = code
        self.filepath = filepath
        self.metrics = TBMetrics()
        
        if code:
            self.analyze(code)
        elif filepath:
            self.analyze_file(filepath)
    
    def analyze(self, code: str) -> TBMetrics:
        """Analyze TB complexity"""
        self.code = code
        
        self._count_lines()
        self._analyze_parameters()
        self._analyze_classes()
        self._analyze_class_refs()
        self._analyze_random_vars()
        self._analyze_random_constraints()
        self._analyze_nesting()
        self._count_components()
        self._analyze_sequence_complexity()
        self._analyze_factory()
        self._analyze_config_db()
        self._analyze_imports()
        self._analyze_packages()
        self._count_functions_tasks()
        self._count_randomization()
        self._count_transactions()
        self._count_interfaces_ports()
        self._count_memory_arrays()
        self._count_fsm()
        self._calculate_score()
        self._check_issues()
        
        return self.metrics
    
    def analyze_file(self, filepath: str) -> TBMetrics:
        """Analyze TB from file"""
        with open(filepath, 'r') as f:
            code = f.read()
        return self.analyze(code)
    
    def _count_lines(self):
        """Count lines of code"""
        lines = self.code.split('\n')
        self.metrics.total_lines = len(lines)
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                self.metrics.blank_lines += 1
            elif stripped.startswith('//') or stripped.startswith('/*'):
                self.metrics.comment_lines += 1
            else:
                self.metrics.code_lines += 1
    
    def _analyze_parameters(self):
        """Analyze parameter usage"""
        self.metrics.parameter_count = len(re.findall(r'parameter\s+', self.code))
        self.metrics.localparam_count = len(re.findall(r'localparam\s+', self.code))
        
        param_refs = len(re.findall(r'\b\w+\s*=\s*\w+', self.code))
        total_params = self.metrics.parameter_count + self.metrics.localparam_count
        if total_params > 0:
            self.metrics.param_usage_ratio = min(1.0, param_refs / (total_params * 2))
    
    def _analyze_classes(self):
        """Analyze class structure"""
        lines = self.code.split('\n')
        class_matches = []
        for line in lines:
            match = re.match(r'\s*class\s+(\w+)(?:\s+extends\s+(\w+))?', line)
            if match:
                class_matches.append((match.group(1), match.group(2)))
        
        self.metrics.class_count = len(class_matches)
        
        for name, parent in class_matches:
            self.metrics.class_names.append(name)
            if parent:
                self.metrics.class_graph_edges.append((name, parent))
                self.metrics.parent_classes.append(parent)
        
        self.metrics.extends_count = len([p for p in self.metrics.parent_classes if p])
        self.metrics.class_graph_nodes = self.metrics.class_names
        self.metrics.class_hierarchy_depth = self._calc_hierarchy_depth()
    
    def _calc_hierarchy_depth(self) -> int:
        """Calculate max class hierarchy depth"""
        if not self.metrics.class_graph_edges:
            return 0
        
        children = {}
        for child, parent in self.metrics.class_graph_edges:
            if parent not in children:
                children[parent] = []
            children[parent].append(child)
        
        def count_depth(node, depth=0):
            if node not in children:
                return depth
            return max(count_depth(c, depth+1) for c in children[node])
        
        all_children = set(c for c, p in self.metrics.class_graph_edges)
        all_parents = set(p for c, p in self.metrics.class_graph_edges)
        roots = all_parents - all_children
        
        if not roots and self.metrics.class_graph_edges:
            roots = {self.metrics.class_graph_edges[0][1]}
        
        return max(count_depth(r) for r in roots) if roots else 0
    
    def _analyze_class_refs(self):
        """Analyze class references (non-inheritance)"""
        inst_pattern = r'(\w+)\s+(\w+)\s*;'
        instances = re.findall(inst_pattern, self.code)
        
        for var_type, var_name in instances:
            if var_type[0].isupper() and var_type not in ['bit', 'byte', 'int', 'logic', 'reg', 'wire']:
                if var_type not in self.metrics.class_instance_map:
                    self.metrics.class_instance_map[var_type] = []
                self.metrics.class_instance_map[var_type].append(var_name)
        
        for class_name in self.metrics.class_names:
            class_pattern = r'class\s+' + class_name + r'.*?(?=class\s+\w+|$)'
            match = re.search(class_pattern, self.code, re.DOTALL)
            if match:
                class_body = match.group(0)
                refs = []
                for other_class in self.metrics.class_names:
                    if other_class != class_name and other_class in class_body:
                        refs.append(other_class)
                if refs:
                    self.metrics.class_refs[class_name] = list(set(refs))
    
    def _analyze_random_vars(self):
        """Analyze random variables"""
        rand_pattern = r'rand\s+(?:bit\s+(?:\[\d+:\d+\]\s+)?|int\s+|byte\s+)?(\w+)'
        rand_matches = re.findall(rand_pattern, self.code)
        randc_pattern = r'randc\s+(?:bit\s+(?:\[\d+:\d+\]\s+)?|int\s+|byte\s+)?(\w+)'
        randc_matches = re.findall(randc_pattern, self.code)
        
        for var_name in rand_matches:
            self.metrics.rand_count += 1
            self.metrics.rand_vars.append(var_name)
            self.metrics.rand_var_types[var_name] = 'bit'
        
        for var_name in randc_matches:
            self.metrics.randc_count += 1
            if var_name not in self.metrics.rand_vars:
                self.metrics.rand_vars.append(var_name)
                self.metrics.rand_var_types[var_name] = 'randc'
        
        bit_width_pattern = r'(rand[cs]?)\s+bit\s*\[(\d+):(\d+)\]\s+(\w+)'
        for modifier, msb, lsb, var_name in re.findall(bit_width_pattern, self.code):
            width = int(msb) - int(lsb) + 1
            self.metrics.rand_var_types[var_name] = 'bit[' + str(width-1) + ':0]'
        
        int_pattern = r'(rand[cs]?)\s+int\s+(\w+)'
        for modifier, var_name in re.findall(int_pattern, self.code):
            self.metrics.rand_var_types[var_name] = 'int'
    
    def _analyze_random_constraints(self):
        """Analyze relationships between random variables and constraints"""
        constraint_blocks = re.findall(
            r'constraint\s+(\w+)\s*\{([^}]*)\}',
            self.code,
            re.DOTALL
        )
        
        for const_name, const_body in constraint_blocks:
            vars_in_const = []
            for var_name in self.metrics.rand_vars:
                if var_name in const_body:
                    vars_in_const.append(var_name)
                    self.metrics.constraint_rand_map[var_name] = const_name
            
            if vars_in_const:
                self.metrics.rand_constraint_map[const_name] = vars_in_const
        
        for const_name, vars_list in self.metrics.rand_constraint_map.items():
            if len(vars_list) > 1:
                for i in range(len(vars_list)):
                    for j in range(i+1, len(vars_list)):
                        self.metrics.rand_relations.append((vars_list[i], vars_list[j]))
    
    def _analyze_nesting(self):
        """Analyze nesting depth"""
        max_depth = 0
        current_depth = 0
        depths = []
        
        for line in self.code.split('\n'):
            stripped = line.strip()
            for c in stripped:
                if c == '{':
                    current_depth += 1
                    max_depth = max(max_depth, current_depth)
                elif c == '}':
                    current_depth = max(0, current_depth - 1)
            if current_depth > 0:
                depths.append(current_depth)
        
        self.metrics.max_nesting = max_depth
        if depths:
            self.metrics.avg_nesting = sum(depths) / len(depths)
    
    def _count_components(self):
        """Count UVM components"""
        patterns = {
            'agent_count': r'class\s+\w+_agent\s+extends\s+uvm_agent',
            'constraint_count': r'constraint\s+\w+\s*\{',
            'covergroup_count': r'covergroup\s+\w+',
            'sequence_count': r'class\s+\w+_seq\s+extends\s+uvm_sequence',
            'virtual_seq_count': r'class\s+\w+_virt_seq\s+extends\s+uvm_sequence',
        }
        
        for key, pattern in patterns.items():
            matches = re.findall(pattern, self.code.lower())
            setattr(self.metrics, key, len(matches))
        
        # Count detailed UVM components
        self.metrics.driver_count = len(re.findall(r'class\s+\w+_driver\s+extends\s+uvm_driver', self.code.lower()))
        self.metrics.monitor_count = len(re.findall(r'class\s+\w+_monitor\s+extends\s+uvm_monitor', self.code.lower()))
        self.metrics.sequencer_count = len(re.findall(r'class\s+\w+_sequencer\s+extends\s+uvm_sequencer', self.code.lower()))
        self.metrics.scoreboard_count = len(re.findall(r'class\s+\w+_scoreboard\s+extends\s+uvm_scoreboard', self.code.lower()))
        self.metrics.reference_model_count = len(re.findall(r'class\s+\w+_refmod(?:el)?\s+extends\s+uvm_component', self.code.lower()))
        self.metrics.subscriber_count = len(re.findall(r'class\s+\w+_subscriber\s+extends\s+uvm_subscriber', self.code.lower()))
        
        # Assertions
        self.metrics.assert_property_count = len(re.findall(r'assert\s+property\s*\(', self.code))
        self.metrics.assert_sequence_count = len(re.findall(r'assert\s+sequence\s*\(', self.code))
        self.metrics.assert_static_count = len(re.findall(r'static\s+assert\s*\(', self.code))
        simple_assert = len(re.findall(r'\b(assert|assume)\s*\(', self.code))
        simple_cover = len(re.findall(r'\bcover\s*\(', self.code))
        total_assert = (self.metrics.assert_property_count + 
                       self.metrics.assert_sequence_count + 
                       self.metrics.assert_static_count + simple_assert)
        self.metrics.assertion_count = total_assert + simple_cover
        self.metrics.assertion_lines = len(re.findall(r'\b(assert|assume|cover)\s*\(', self.code))
        
        # Forces
        self.metrics.force_count = len(re.findall(r'\bforce\s+', self.code))
        
        # Macros
        defines = re.findall(r'`define\s+(\w+)', self.code)
        self.metrics.define_count = len(defines)
        self.metrics.define_names = defines[:20]
        self.metrics.ifdef_count = len(re.findall(r'`ifdef|`ifndef', self.code))
    
    def _analyze_sequence_complexity(self):
        """Analyze sequence body complexity and hierarchy"""
        seq_matches = re.findall(
            r'class\s+\w+_seq\s+extends.*?endclass',
            self.code,
            re.DOTALL
        )
        
        self.metrics.sequence_items = len(seq_matches)
        
        # Calculate sequence hierarchy depth
        seq_hierarchy = self._calc_sequence_hierarchy()
        self.metrics.sequence_hierarchy_depth = seq_hierarchy['max_depth']
        
        for seq in seq_matches:
            self.metrics.sequence_body_lines += seq.count('\n')
            self.metrics.fork_join_count += len(re.findall(r'fork', seq))
            self.metrics.send_port_count += len(re.findall(r'\.(start|put|send)\s*\(', seq))
            self.metrics.get_try_count += len(re.findall(r'\.(get|try_next|peek)\s*\(', seq))
            self.metrics.wait_count += len(re.findall(r'\bwait\s*\(', seq))
            
            # Count nested sequences
            self.metrics.nested_sequence_count += len(re.findall(r'`uvm_do|\.start\(', seq))
        
        # Count sequence macros
        self.metrics.sequence_macro_count = len(re.findall(
            r'`uvm_do|`uvm_do_with|`uvm_create|`uvm_send|`uvm_rand_send',
            self.code
        ))
    
    def _calc_sequence_hierarchy(self) -> Dict:
        """Calculate sequence nesting depth"""
        # Find nested sequence definitions
        seq_defs = re.findall(r'class\s+(\w+_seq)\s+extends.*?endclass', self.code, re.DOTALL)
        
        # Find sequence start points (where sequences are started)
        start_calls = re.findall(r'(\w+_seq)\s*\(\)\s*\.start\(', self.code)
        
        # Build a simple hierarchy based on naming convention
        # e.g., virt_seq starts child_seq
        max_depth = 1
        for virt_match in re.finditer(r'class\s+(\w+_virt_seq)\s+extends.*?begin(.*?)endclass', self.code, re.DOTALL):
            virt_name = virt_match.group(1)
            body = virt_match.group(2)
            # Count how many sequences are started in this virtual sequence
            starts = len(re.findall(r'\.start\s*\(', body))
            if starts > 0:
                max_depth = max(max_depth, 1 + starts)
        
        return {'max_depth': min(max_depth, 10), 'starts': len(start_calls)}
    
    def _analyze_factory(self):
        """Analyze factory usage"""
        self.metrics.factory_create_count = len(re.findall(r'type_id::create\(', self.code))
        self.metrics.uvm_object_utils_count = len(re.findall(r'`uvm_object_utils', self.code))
        self.metrics.uvm_component_utils_count = len(re.findall(r'`uvm_component_utils', self.code))
    
    def _analyze_config_db(self):
        """Analyze config_db usage"""
        self.metrics.config_db_get = len(re.findall(r'uvm_config_db.*::get\(', self.code))
        self.metrics.config_db_set = len(re.findall(r'uvm_config_db.*::set\(', self.code))
    
    def _analyze_imports(self):
        """Analyze imports/includes"""
        self.metrics.import_count = len(re.findall(r'\bimport\s+[\w:]+;', self.code))
        self.metrics.include_count = len(re.findall(r'`include\s+"[^"]+"', self.code))
    

    def _analyze_packages(self):
        pkg = re.findall(r'package\s+(\w+)\s*;', self.code)
        self.metrics.package_count = len(pkg)
        self.metrics.package_names = pkg[:20]
        for p in pkg:
            sec = re.search(r'package\s+' + p + r'\s*;.*?(?=package\s+\w+\s*;|$)', self.code, re.DOTALL)
            if sec:
                imps = re.findall(r'import\s+(\w+)\s*::', sec.group(0))
                if imps:
                    self.metrics.package_imports[p] = list(set(imps))
    
    def _count_functions_tasks(self):
        self.metrics.function_count = len(re.findall(r'\bfunction\s+\w+', self.code))
        self.metrics.task_count = len(re.findall(r'\btask\s+\w+', self.code))
    
    def _count_randomization(self):
        self.metrics.randomize_count = len(re.findall(r'\.randomize\s*\(', self.code))
    
    def _count_transactions(self):
        self.metrics.deep_copy_count = len(re.findall(r'\.deep_copy\s*\(', self.code))
        self.metrics.clone_count = len(re.findall(r'\.clone\s*\(', self.code))
    
    def _count_interfaces_ports(self):
        self.metrics.interface_count = len(re.findall(r'\binterface\s+\w+', self.code))
        self.metrics.port_count = len(re.findall(r'\binput\b|\boutput\b|\binout\b', self.code))
    
    def _count_memory_arrays(self):
        self.metrics.memory_array_count = len(re.findall(r'\w+\s+\w+\s*\[\s*\d+\s*:\s*\d+\s*\]', self.code))
        for msb, lsb in re.findall(r'\[(\d+)\s*:\s*(\d+)\]', self.code):
            self.metrics.memory_size_sum += max(0, int(msb) - int(lsb) + 1)
    
    def _count_fsm(self):
        self.metrics.fsm_state_count = len(re.findall(r'\b\w*state\w*\s*:', self.code.lower()))

    def _calculate_score(self):
        """Calculate complexity score"""
        score = 0.0
        m = self.metrics
        
        score += min(15, m.code_lines / 15)
        score += min(15, m.max_nesting * 1.5)
        score += min(10, m.class_hierarchy_depth * 2)
        score += min(10, len(m.class_refs) * 0.5)
        score += min(10, m.rand_count * 0.3)
        score += min(5, len(m.rand_relations) * 0.5)
        score += min(15, m.sequence_items * 2)
        score += min(5, m.fork_join_count * 0.5)
        
        total_components = (
            m.agent_count * 2 +
            m.constraint_count * 0.3 +
            m.assertion_count * 0.2 +
            m.covergroup_count * 1.0 +
            m.sequence_count * 1.5
        )
        score += min(15, total_components)
        score += min(5, (m.config_db_get + m.config_db_set) * 0.2)
        
        self.metrics.complexity_score = round(score, 2)
        
        if score < 20:
            grade = "A (Simple)"
        elif score < 40:
            grade = "B (Moderate)"
        elif score < 60:
            grade = "C (Complex)"
        elif score < 80:
            grade = "D (Very Complex)"
        else:
            grade = "F (Too Complex)"
        
        self.metrics.complexity_grade = grade
    
    def _check_issues(self):
        """Check for complexity issues"""
        issues = []
        m = self.metrics
        
        if m.max_nesting > 8:
            issues.append(f"Deep nesting: {m.max_nesting} levels")
        if m.code_lines > 5000:
            issues.append(f"Large TB: {m.code_lines} LOC")
        if m.constraint_count > 100:
            issues.append(f"Many constraints: {m.constraint_count}")
        if m.rand_count > 50:
            issues.append(f"Many rand vars: {m.rand_count}")
        if len(m.rand_relations) > 50:
            issues.append(f"Complex var relations: {len(m.rand_relations)}")
        if m.sequence_body_lines > 1000:
            issues.append(f"Long sequences: {m.sequence_body_lines} lines")
        if m.covergroup_count == 0 and m.code_lines > 500:
            issues.append("No covergroups")
        if m.assertion_count == 0 and m.code_lines > 500:
            issues.append("No assertions")
        
        self.metrics.issues = issues
    
    def get_report(self) -> str:
        """Generate analysis report"""
        m = self.metrics
        
        lines = [
            "=" * 70,
            "TB COMPLEXITY ANALYSIS REPORT (Comprehensive)",
            "=" * 70,
            "",
            "[Code Metrics]",
            f"  Total lines:      {m.total_lines:>6}",
            f"  Code lines:       {m.code_lines:>6}",
            f"  Comments:         {m.comment_lines:>6}",
            "",
            "[Parameter Usage]",
            f"  Parameters:       {m.parameter_count:>6}",
            f"  Localparams:      {m.localparam_count:>6}",
            "",
            "[Class Analysis]",
            f"  Class count:      {m.class_count:>6}",
            f"  Hierarchy depth:  {m.class_hierarchy_depth:>6}",
            f"  Class refs:       {len(m.class_refs):>6}",
        ]
        
        if m.class_refs:
            lines.append("  Class references:")
            for cls, refs in list(m.class_refs.items())[:5]:
                lines.append(f"    {cls} -> {', '.join(refs[:3])}")
        
        lines.extend([
            "",
            "[Random Variables]",
            f"  rand count:       {m.rand_count:>6}",
            f"  randc count:      {m.randc_count:>6}",
        ])
        
        if m.rand_vars:
            lines.append(f"  Variables: {', '.join(m.rand_vars[:8])}")
            if len(m.rand_vars) > 8:
                lines.append(f"             ... ({len(m.rand_vars) - 8} more)")
        
        if m.rand_relations:
            lines.extend([
                "",
                "[Random Variable Relations]",
                f"  Total relations: {len(m.rand_relations):>6}",
            ])
            lines.append("  Related pairs:")
            for v1, v2 in m.rand_relations[:10]:
                lines.append(f"    {v1} <-> {v2}")
            if len(m.rand_relations) > 10:
                lines.append(f"    ... ({len(m.rand_relations) - 10} more)")
        
        if m.rand_constraint_map:
            lines.extend(["", "[Constraint Mapping]"])
            for const, vars_list in list(m.rand_constraint_map.items())[:5]:
                lines.append(f"  {const}: {', '.join(vars_list)}")
        
        lines.extend([
            "",
            "[Assertions]",
            f"  Total:             {m.assertion_count:>6}",
            f"  property:         {m.assert_property_count:>6}",
            f"  sequence:         {m.assert_sequence_count:>6}",
            f"  static:           {m.assert_static_count:>6}",
            "",
            "[Force/Release]",
            f"  force:            {m.force_count:>6}",
            "",
            "[Macros]",
            f"  `define:          {m.define_count:>6}",
            f"  `ifdef/`ifndef:   {m.ifdef_count:>6}",
        ])
        
        if m.define_names:
            lines.append(f"  Defined: {', '.join(m.define_names[:8])}")
        
        lines.extend([
            "",
            "[Sequence Hierarchy]",
            f"  Sequences:         {m.sequence_items:>6}",
            f"  Hierarchy depth:  {m.sequence_hierarchy_depth:>6}",
            f"  Nested starts:    {m.nested_sequence_count:>6}",
            f"  Sequence macros:  {m.sequence_macro_count:>6}",
            "",
            "[Sequence Body]",
            f"  Sequence lines:   {m.sequence_body_lines:>6}",
            f"  fork/join:        {m.fork_join_count:>6}",
            f"  send/put:         {m.send_port_count:>6}",
            f"  get/try:          {m.get_try_count:>6}",
            f"  wait:             {m.wait_count:>6}",
            "",
            "[UVM Components]",
            f"  Agents:           {m.agent_count:>6}",
            f"  Drivers:          {m.driver_count:>6}",
            f"  Monitors:         {m.monitor_count:>6}",
            f"  Sequencers:       {m.sequencer_count:>6}",
            f"  Scoreboards:      {m.scoreboard_count:>6}",
            f"  Ref Models:       {m.reference_model_count:>6}",
            f"  Subscribers:      {m.subscriber_count:>6}",
            "",
            "[Constraints/Coverage]",
            f"  Constraints:      {m.constraint_count:>6}",
            f"  Covergroups:      {m.covergroup_count:>6}",
            "",
            "[Factory]",
            f"  factory creates:  {m.factory_create_count:>6}",
            "",
            "[Complexity]",
            f"  Score:            {m.complexity_score:>6.1f}",
            f"  Grade:            {m.complexity_grade}",
        ])
        
        if m.issues:
            lines.extend(["", "[Issues]"])
            for issue in m.issues:
                lines.append(f"  WARNING: {issue}")
        
        return "\n".join(lines)
    
    def get_json(self) -> Dict:
        """Get metrics as JSON-serializable dict"""
        m = self.metrics
        return {
            'code_metrics': {
                'total_lines': m.total_lines,
                'code_lines': m.code_lines,
                'comment_lines': m.comment_lines,
                'blank_lines': m.blank_lines,
            },
            'parameter_usage': {
                'parameter_count': m.parameter_count,
                'localparam_count': m.localparam_count,
            },
            'class_analysis': {
                'class_count': m.class_count,
                'hierarchy_depth': m.class_hierarchy_depth,
                'extends_count': m.extends_count,
                'class_refs': m.class_refs,
                'class_instance_map': m.class_instance_map,
            },
            'class_graph': {
                'nodes': m.class_graph_nodes,
                'edges': [{'from': e[0], 'to': e[1]} for e in m.class_graph_edges],
            },
            'random_variables': {
                'rand_count': m.rand_count,
                'randc_count': m.randc_count,
                'variables': m.rand_vars,
                'var_types': m.rand_var_types,
            },
            'random_relations': {
                'constraint_map': m.rand_constraint_map,
                'constraint_rand_map': m.constraint_rand_map,
                'relations': [{'var1': r[0], 'var2': r[1]} for r in m.rand_relations],
            },
            'assertions': {
                'total': m.assertion_count,
                'property': m.assert_property_count,
                'sequence': m.assert_sequence_count,
                'static': m.assert_static_count,
            },
            'forces': {
                'force_count': m.force_count,
            },
            'macros': {
                'define_count': m.define_count,
                'define_names': m.define_names,
                'ifdef_count': m.ifdef_count,
            },
            'sequence_complexity': {
                'sequence_count': m.sequence_items,
                'body_lines': m.sequence_body_lines,
                'fork_join': m.fork_join_count,
                'send_port': m.send_port_count,
                'get_try': m.get_try_count,
                'wait': m.wait_count,
            },
            'components': {
                'agents': m.agent_count,
                'constraints': m.constraint_count,
                'covergroups': m.covergroup_count,
            },
            'packages': {
                'count': m.package_count,
                'names': m.package_names,
                'imports': m.package_imports,
            },
            'functions_tasks': {
                'functions': m.function_count,
                'tasks': m.task_count,
            },
            'randomization': {
                'randomize_count': m.randomize_count,
            },
            'transactions': {
                'deep_copy': m.deep_copy_count,
                'clone': m.clone_count,
            },
            'interfaces_ports': {
                'interfaces': m.interface_count,
                'ports': m.port_count,
            },
            'memory_arrays': {
                'count': m.memory_array_count,
                'total_bits': m.memory_size_sum,
            },
            'fsm': {
                'state_count': m.fsm_state_count,
            },
            'complexity': {
                'score': m.complexity_score,
                'grade': m.complexity_grade,
            },
            'issues': m.issues,
        }
