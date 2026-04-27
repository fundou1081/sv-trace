"""TB Complexity Analyzer

Analyzes UVM testbench complexity with objective metrics.
"""

import re
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field


@dataclass
class TBMetrics:
    """TB complexity metrics - objective data"""
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
    
    # Nesting
    max_nesting: int = 0
    avg_nesting: float = 0.0
    
    # UVM Components
    agent_count: int = 0
    constraint_count: int = 0
    assertion_count: int = 0
    covergroup_count: int = 0
    sequence_count: int = 0
    virtual_seq_count: int = 0
    config_db_get: int = 0
    config_db_set: int = 0
    
    # Factory
    factory_create_count: int = 0
    uvm_object_utils_count: int = 0
    uvm_component_utils_count: int = 0
    
    # Imports
    import_count: int = 0
    include_count: int = 0
    
    # Class relationship graph data
    class_graph_nodes: List[str] = field(default_factory=list)
    class_graph_edges: List[Tuple[str, str]] = field(default_factory=list)
    
    # Complexity
    complexity_score: float = 0.0
    complexity_grade: str = "A"
    
    # Issues
    issues: List[str] = field(default_factory=list)


class TBComplexityAnalyzer:
    """Analyze testbench complexity with objective metrics"""
    
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
        
        # All analysis methods
        self._count_lines()
        self._analyze_parameters()
        self._analyze_classes()
        self._analyze_nesting()
        self._count_components()
        self._analyze_factory()
        self._analyze_config_db()
        self._analyze_imports()
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
        
        # Parameter usage in expressions
        param_refs = len(re.findall(r'\b\w+\s*=\s*\w+', self.code))
        total_params = self.metrics.parameter_count + self.metrics.localparam_count
        if total_params > 0:
            self.metrics.param_usage_ratio = min(1.0, param_refs / (total_params * 2))
    
    def _analyze_classes(self):
        """Analyze class structure"""
        class_matches = re.findall(r'class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w,\s]+))?', self.code)
        self.metrics.class_count = len(class_matches)
        
        for name, parent, impl in class_matches:
            self.metrics.class_names.append(name)
            if parent:
                self.metrics.class_graph_edges.append((name, parent))
                self.metrics.parent_classes.append(parent)
            if impl:
                self.metrics.implements_count += len(impl.split(','))
        
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
        
        all_nodes = set(c for c, p in self.metrics.class_graph_edges)
        roots = all_nodes - set(p for c, p in self.metrics.class_graph_edges)
        if not roots and self.metrics.class_graph_edges:
            roots = {self.metrics.class_graph_edges[0][1]}
        
        return max(count_depth(r) for r in roots) if roots else 0
    
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
            'assertion_count': r'\b(assert|assume|cover)\s*\(',
            'covergroup_count': r'covergroup\s+\w+',
            'sequence_count': r'class\s+\w+_seq\s+extends\s+uvm_sequence',
            'virtual_seq_count': r'class\s+\w+_virt_seq\s+extends\s+uvm_sequence',
        }
        
        for key, pattern in patterns.items():
            matches = re.findall(pattern, self.code.lower())
            setattr(self.metrics, key, len(matches))
    
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
    
    def _calculate_score(self):
        """Calculate complexity score"""
        score = 0.0
        m = self.metrics
        
        # Lines factor (max 15)
        score += min(15, m.code_lines / 15)
        
        # Nesting factor (max 20)
        score += min(20, m.max_nesting * 2)
        
        # Class hierarchy factor (max 15)
        score += min(15, m.class_hierarchy_depth * 3)
        score += min(10, m.class_count * 0.5)
        
        # Components factor (max 20)
        total_components = (
            m.agent_count * 2 +
            m.constraint_count * 0.3 +
            m.assertion_count * 0.2 +
            m.covergroup_count * 1.0 +
            m.sequence_count * 0.5
        )
        score += min(20, total_components)
        
        # Config complexity (max 10)
        score += min(10, (m.config_db_get + m.config_db_set) * 0.3)
        
        # Factory usage (max 10)
        score += min(10, m.factory_create_count * 0.5)
        
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
        if m.class_hierarchy_depth > 5:
            issues.append(f"Deep hierarchy: {m.class_hierarchy_depth} levels")
        if m.config_db_get > 50:
            issues.append(f"Many config_db::get: {m.config_db_get}")
        if m.factory_create_count > 100:
            issues.append(f"Many factory creates: {m.factory_create_count}")
        if m.covergroup_count == 0 and m.code_lines > 500:
            issues.append("No covergroups defined")
        if m.assertion_count == 0 and m.code_lines > 500:
            issues.append("No assertions defined")
        
        self.metrics.issues = issues
    
    def get_report(self) -> str:
        """Generate analysis report"""
        m = self.metrics
        
        lines = [
            "=" * 65,
            "TB COMPLEXITY ANALYSIS REPORT (Enhanced)",
            "=" * 65,
            "",
            "[Code Metrics]",
            f"  Total lines:      {m.total_lines:>6}",
            f"  Code lines:       {m.code_lines:>6}",
            f"  Comments:         {m.comment_lines:>6}",
            f"  Blanks:           {m.blank_lines:>6}",
            "",
            "[Parameter Usage]",
            f"  Parameters:       {m.parameter_count:>6}",
            f"  Localparams:      {m.localparam_count:>6}",
            f"  Usage ratio:      {m.param_usage_ratio*100:>5.1f}%",
            "",
            "[Class Analysis]",
            f"  Class count:      {m.class_count:>6}",
            f"  Hierarchy depth:  {m.class_hierarchy_depth:>6}",
            f"  Extends count:    {m.extends_count:>6}",
            f"  Implements:       {m.implements_count:>6}",
            "",
            "[Class Graph Data]",
            f"  Nodes: {len(m.class_graph_nodes)}",
        ]
        
        if m.class_graph_edges:
            lines.append("  Edges (child -> parent):")
            for child, parent in m.class_graph_edges[:10]:
                lines.append(f"    {child} -> {parent}")
            if len(m.class_graph_edges) > 10:
                lines.append(f"    ... ({len(m.class_graph_edges) - 10} more)")
        
        lines.extend([
            "",
            "[Nesting]",
            f"  Max depth:        {m.max_nesting:>6}",
            f"  Avg depth:        {m.avg_nesting:>6.1f}",
            "",
            "[Components]",
            f"  Agents:           {m.agent_count:>6}",
            f"  Constraints:      {m.constraint_count:>6}",
            f"  Assertions:       {m.assertion_count:>6}",
            f"  Covergroups:      {m.covergroup_count:>6}",
            f"  Sequences:        {m.sequence_count:>6}",
            f"  Virtual seqs:     {m.virtual_seq_count:>6}",
            "",
            "[Config DB]",
            f"  config_db::get:   {m.config_db_get:>6}",
            f"  config_db::set:   {m.config_db_set:>6}",
            "",
            "[Factory]",
            f"  factory creates:  {m.factory_create_count:>6}",
            f"  `uvm_object_utils:   {m.uvm_object_utils_count:>5}",
            f"  `uvm_component_utils: {m.uvm_component_utils_count:>4}",
            "",
            "[Imports/Includes]",
            f"  import:           {m.import_count:>6}",
            f"  `include:         {m.include_count:>6}",
            "",
            "[Complexity]",
            f"  Score:            {m.complexity_score:>6.1f}",
            f"  Grade:            {m.complexity_grade}",
        ])
        
        if m.issues:
            lines.extend(["", "[Issues]"])
            for issue in m.issues:
                lines.append(f"  ⚠️  {issue}")
        
        return "\n".join(lines)

    def get_json(self) -> Dict:
        """Get metrics as JSON-serializable dict"""
        import json
        return {
            'code_metrics': {
                'total_lines': self.metrics.total_lines,
                'code_lines': self.metrics.code_lines,
                'comment_lines': self.metrics.comment_lines,
                'blank_lines': self.metrics.blank_lines,
            },
            'parameter_usage': {
                'parameter_count': self.metrics.parameter_count,
                'localparam_count': self.metrics.localparam_count,
                'param_usage_ratio': self.metrics.param_usage_ratio,
            },
            'class_analysis': {
                'class_count': self.metrics.class_count,
                'hierarchy_depth': self.metrics.class_hierarchy_depth,
                'extends_count': self.metrics.extends_count,
                'implements_count': self.metrics.implements_count,
                'class_names': self.metrics.class_names,
            },
            'class_graph': {
                'nodes': self.metrics.class_graph_nodes,
                'edges': [{'from': e[0], 'to': e[1]} for e in self.metrics.class_graph_edges],
            },
            'nesting': {
                'max_depth': self.metrics.max_nesting,
                'avg_depth': self.metrics.avg_nesting,
            },
            'components': {
                'agents': self.metrics.agent_count,
                'constraints': self.metrics.constraint_count,
                'assertions': self.metrics.assertion_count,
                'covergroups': self.metrics.covergroup_count,
                'sequences': self.metrics.sequence_count,
                'virtual_sequences': self.metrics.virtual_seq_count,
            },
            'config_db': {
                'get_count': self.metrics.config_db_get,
                'set_count': self.metrics.config_db_set,
            },
            'factory': {
                'create_count': self.metrics.factory_create_count,
                'uvm_object_utils': self.metrics.uvm_object_utils_count,
                'uvm_component_utils': self.metrics.uvm_component_utils_count,
            },
            'imports': {
                'import_count': self.metrics.import_count,
                'include_count': self.metrics.include_count,
            },
            'complexity': {
                'score': self.metrics.complexity_score,
                'grade': self.metrics.complexity_grade,
            },
            'issues': self.metrics.issues,
        }
