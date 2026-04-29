"""
SV-Schema - SystemVerilog 分析结果统一格式

统一所有工具的输出格式，便于Agent编排
"""
from typing import Dict, List, Any
import json


class SVSchema:
    """统一Schema格式"""
    
    VERSION = "1.0"
    
    def __init__(self):
        self.data = {
            "schema_version": self.VERSION,
            "source": "",
            "modules": [],
            "classes": [],
            "fsm": [],
            "coverage": {
                "points": [],
                "covergroup": ""
            },
            "constraints": [],
            "parameters": [], "signals": {}, "loads": [], "complexity": [], "clock_domains": {}, "uninitialized": [], "signal_count": 0, "datapath_boundaries": {}, "timing_paths": [], "risks": {"risks": [], "summary": {}},
    "controlflow": {},
    "dataflow": {},
    "design_eval": {},
    "syntax_check": {},
    "code_quality": {}
        }
    
    def set_source(self, source: str):
        """设置源码"""
        self.data["source"] = source
        return self
    
    def add_module(self, module: Dict):
        """添加模块"""
        self.data["modules"].append(module)
        return self
    
    def add_class(self, cls):
        """添加类 - 自动转换非JSON类型"""
        if hasattr(cls, 'to_dict'):
            cls = cls.to_dict()
        # 转换任何dataclass为dict
        if isinstance(cls, dict):
            # 确保所有值都是JSON可序列化的
            clean = {}
            for k, v in cls.items():
                if hasattr(v, 'to_dict'):
                    clean[k] = v.to_dict()
                elif isinstance(v, list):
                    clean[k] = [x.to_dict() if hasattr(x, 'to_dict') else x for x in v]
                else:
                    clean[k] = v
            cls = clean
        self.data["classes"].append(cls)
        return self
    
    def add_fsm(self, fsm: Dict):
        """添加FSM"""
        self.data["fsm"].append(fsm)
        return self
    
    def add_coverage_point(self, point: Dict):
        """添加coverage点"""
        self.data["coverage"]["points"].append(point)
        return self
    
    def set_covergroup(self, cg: str):
        """设置covergroup代码"""
        self.data["coverage"]["covergroup"] = cg
        return self
    
    def add_constraint(self, constraint: Dict):
        """添加约束"""
        self.data["constraints"].append(constraint)
        return self
    
    def add_parameter(self, param: Dict):
        """添加参数"""
        self.data["parameters"].append(param)
        return self
    
    def to_dict(self) -> Dict:
        """转为字典"""
        return self.data
    
    def to_json(self, indent=2) -> str:
        """转为JSON字符串"""
        return json.dumps(self.data, indent=indent)
    
    def save(self, filepath: str):
        """保存到文件"""
        with open(filepath, 'w') as f:
            f.write(self.to_json())




def _create_text_parser(source: str):
    """创建用于从文本提取的 mock parser"""
    import pyslang
    tree = pyslang.SyntaxTree.fromText(source)
    
    class TextParser:
        def __init__(self, tree):
            self.trees = {"input.sv": tree}
            self.compilation = tree
    
    return TextParser(tree)


def to_schema(parser, source: str = "") -> SVSchema:
    """从parser自动提取所有信息生成schema"""
    schema = SVSchema()
    schema.set_source(source)
    
    # 1. 提取模块信息
    try:
        from parse.module_io import ModuleIOExtractor
        extractor = ModuleIOExtractor()
        modules = extractor.extract_from_text(source)
        for m in modules:
            schema.add_module(m.to_dict())
    except Exception as e:
        print(f"Module extraction error: {e}")
    
    # 2. 提取类信息
    try:
        from parse.class_utils import ClassExtractor
        extractor = ClassExtractor()
        extractor.extract_from_text(source)
        for cls_name, cls_info in extractor.classes.items():
            schema.add_class(cls_info)
    except Exception as e:
        print(f"Class extraction error: {e}")
    
    # 3. 提取FSM
    try:
        from debug.fsm import FSMExtractor
        extractor = FSMExtractor(None)
        fsm_list = extractor.extract_from_text(source)
        for fsm in fsm_list:
            schema.add_fsm({
                "module": fsm.name,
                "states": [s.name for s in fsm.states],
                "state_var": fsm.state_var,
                "reset_state": fsm.reset_state,
                "transitions": [
                    {"from": s.name, "to": t[1], "cond": t[0]}
                    for s in fsm.states for t in s.transitions
                ]
            })
    except Exception as e:
        print(f"FSM extraction error: {e}")
    
    # 4. 生成Coverage
    try:
        from verify.coverage_guide.stimulus_suggester import CoverageStimulusSuggester
        suggester = CoverageStimulusSuggester()
        suggester.extract_from_text(source)
        cg = suggester.generate_covergroup("design")
        schema.set_covergroup(cg)
        
        for point in suggester.get_coverage_points():
            schema.add_coverage_point({
                "id": point.id,
                "condition": point.condition,
                "type": point.type,
                "suggestions": point.suggestions,
                "kind": getattr(point, 'kind', 'condition')
            })
    except Exception as e:
        print(f"Coverage generation error: {e}")
    

    # 5. 提取 constraints
    try:
        constraints = _extract_constraints(source)
        for c in constraints:
            schema.add_constraint(c)
    except Exception as e:
        print(f"Constraint extraction error: {e}")
    
    # 6. 提取 parameters
    try:
        params = _extract_parameters(source)
        for p in params:
            schema.add_parameter(p)
    except Exception as e:
        print(f"Parameter extraction error: {e}")
    

    # 7. 提取 drivers (信号驱动信息)
    try:
        from trace.driver import DriverCollector
        dc = DriverCollector(_create_text_parser(source))
        if dc:
            for sig, drvs in dc.drivers.items():
                drivers_list = []
                for d in drvs:
                    drivers_list.append({
                        'signal': d.signal,
                        'kind': d.kind.name if hasattr(d.kind, 'name') else str(d.kind),
                        'sources': d.sources,
                        'clock': d.clock,
                        'line': d.lines[0] if d.lines else 0
                    })
                schema.data['signals'][sig] = drivers_list
    except Exception as e:
        print(f"Driver extraction error: {e}")

    # 8. 提取 loads (信号加载点)
    try:
        from trace.load import LoadTracer
        lt = LoadTracer(_create_text_parser(source))
        if lt and lt._loads:
            loads_list = []
            for load in lt._loads:
                loads_list.append({
                    'signal': load.signal,
                    'kind': getattr(load, 'kind', 'load'),
                    'context': getattr(load, 'context', '')
                })
            schema.data['loads'] = loads_list
    except Exception as e:
        print(f"Load extraction error: {e}")


    # 9. 复杂度分析
    try:
        from debug.complexity import CyclomaticComplexityAnalyzer
        ca = CyclomaticComplexityAnalyzer(_create_text_parser(source))
        results = ca.analyze()
        complexity_list = []
        for mod_name, result in results.items():
            complexity_list.append({
                'module': mod_name,
                'total_complexity': result.total_complexity,
                'grade': result.grade,
                'procedures': [
                    {'name': p.name, 'complexity': p.complexity, 'line': p.line}
                    for p in result.procedures
                ]
            })
        schema.data['complexity'] = complexity_list
    except Exception as e:
        print(f"Complexity analysis error: {e}")

    # 10. 时钟域分析
    try:
        from debug.analyzers.clock_domain import ClockDomainAnalyzer
        cda = ClockDomainAnalyzer(_create_text_parser(source))
        clock_domains = {}
        for clk, regs in cda._clock_domains.items():
            clock_domains[clk] = list(regs)
        schema.data['clock_domains'] = clock_domains
    except Exception as e:
        print(f"Clock domain analysis error: {e}")

    # 11. 未初始化检测
    try:
        from debug.analyzers.uninitialized import UninitializedDetector
        ud = UninitializedDetector(_create_text_parser(source))
        uninit_list = []
        all_issues = ud.detect_all()
        for sig, issues in all_issues.items():
            for issue in issues:
                uninit_list.append({
                    'signal': issue.signal,
                'type': issue.issue_type,
                'severity': issue.severity
            })
        schema.data['uninitialized'] = uninit_list
    except Exception as e:
        print(f"Uninitialized detection error: {e}")


    # 12. 信号查询
    try:
        from query.signal import query_signals
        sq = query_signals(source)
        # 列出所有信号
        all_signals = sq.list_all_signals()
        schema.data['signal_count'] = len(all_signals)
    except Exception as e:
        print(f"Signal query error: {e}")

    # 13. DataPath 边界分析
    try:
        from query.datapath_boundary_analyzer import DataPathBoundaryAnalyzer
        dpa = DataPathBoundaryAnalyzer(_create_text_parser(source))
        # 获取所有信号的边界
        boundaries = {}
        for sig in dpa.get_all_signals():
            result = dpa.analyze(sig)
            if result and result.bins:
                boundaries[sig] = [
                    {'name': b.name, 'value': b.value}
                    for b in result.bins
                ]
        schema.data['datapath_boundaries'] = boundaries
    except Exception as e:
        print(f"DataPath error: {e}")

    # 14. Timing Path
    try:
        from trace.timing_path import TimingPathExtractor
        tpe = TimingPathExtractor(_create_text_parser(source))
        timing_paths = []
        for info in tpe.analyze():
            timing_paths.append({
                'module': info.module,
                'paths': [
                    {'start': p.start, 'end': p.end, 'depth': p.depth}
                    for p in info.paths[:5]  # 限制5条
                ],
                'max_depth': info.max_depth
            })
        schema.data['timing_paths'] = timing_paths
    except Exception as e:
        print(f"Timing path error: {e}")



    # 15. Risk evaluation
    try:
        from verify.risk_evaluator import extract_risks
        risks = extract_risks(source)
        schema.data['risks'] = risks
    except Exception as e:
        print(f"Risk evaluation error: {e}")

    # 16. Constraint generation
    try:
        from verify.constraint_generator import extract_constraints
        constrs = extract_constraints(source)
        # 已经提取过了，如果为空则添加空列表
        if not schema.data['constraints']:
            schema.data['constraints'] = constrs
    except Exception as e:
        print(f"Constraint gen error: {e}")


    # 17. Apps - Control flow analysis
    try:
        from apps.controlflow import analyze_controlflow
        cf = analyze_controlflow(source)
        schema.data['controlflow'] = cf
    except Exception as e:
        print(f"Controlflow error: {e}")

    # 18. Apps - Data flow analysis
    try:
        from apps.dataflow import analyze_dataflow
        df = analyze_dataflow(source)
        schema.data['dataflow'] = df
    except Exception as e:
        print(f"Dataflow error: {e}")

    # 19. Apps - Design evaluation
    try:
        from apps.evaluate import evaluate_design
        ev = evaluate_design(source)
        schema.data['design_eval'] = ev
    except Exception as e:
        print(f"Evaluate error: {e}")

    # 20. Lint - Syntax check
    try:
        from lint.syntax_check import check_syntax
        syn = check_syntax(source)
        schema.data['syntax_check'] = syn
    except Exception as e:
        print(f"Syntax check error: {e}")

    # 21. Lint - Code quality
    try:
        from lint.code_quality import check_quality
        cq = check_quality(source)
        schema.data['code_quality'] = cq
    except Exception as e:
        print(f"Code quality error: {e}")

    return schema


# 标准Schema格式说明
SCHEMA_DOC = """
# SV-Schema JSON 格式说明

## 顶层结构
{
  "schema_version": "1.0",      # Schema版本
  "source": "...",               # 原始代码(可选)
  
  "modules": [...],              # 模块列表
  "classes": [...],              # 类列表
  "fsm": [...],                 # 状态机列表
  "coverage": {...},             # Coverage信息
  "constraints": [...],          # 约束列表
  "parameters": [...]            # 参数列表
}

## modules[i]
{
  "module": "uart",              # 模块名
  "ports": [                     # 端口列表
    {"Name": "tx", "direction": "output", "width": 1},
    {"Name": "data", "direction": "input", "width": 8}
  ]
}

## classes[i]
{
  "name": "Packet",
  "members": [{"name": "data", "type": "bit", "width": 8, "rand": "rand"}],
  "methods": [{"name": "new", "kind": "function", "return_type": ""}],
  "constraints": [{"name": "c_data", "expr": "..."}]
}

## fsm[i]
{
  "module": "uart_ctrl",
  "states": ["IDLE", "TX", "DONE"],
  "transitions": [["IDLE", "TX"], ["TX", "DONE"]]
}

## coverage
{
  "points": [
    {"id": "cp_0", "condition": "tx_en", "type": "if"}
  ],
  "covergroup": "covergroup cg_design..."
}

## constraints[i]
{
  "name": "c_data",
  "class": "Packet",
  "expr": "data inside {[0:100]}"
}

## parameters[i]
{
  "name": "BAUD",
  "value": "9600"
}
"""


if __name__ == "__main__":
    print(SCHEMA_DOC)


def _extract_constraints(source: str) -> List[Dict]:
    """从源码提取 constraints（支持嵌套的 {}）"""
    import re
    constraints = []
    
    pos = 0
    while pos < len(source):
        m = re.search(r'constraint\s+(\w+)\s*\{', source[pos:])
        if not m:
            break
        
        name = m.group(1)
        start = pos + m.end() - 1
        
        # 找对应的 closing brace（处理嵌套）
        depth = 1
        i = start + 1
        while i < len(source) and depth > 0:
            if source[i] == '{':
                depth += 1
            elif source[i] == '}':
                depth -= 1
            i += 1
        
        expr = source[start+1:i-1].strip()
        
        # 找所属的 class
        class_match = re.search(r'class\s+(\w+)[^{]*\{', source[:start])
        class_name = class_match.group(1) if class_match else ''
        
        constraints.append({'name': name, 'class': class_name, 'expr': expr})
        pos = i
    
    return constraints


def _extract_parameters(source: str) -> List[Dict]:
    """从源码提取 parameters"""
    import re
    params = []
    
    # 首先找 #(...) 中的参数
    param_list_match = re.search(r'#\s*\(([^)]+)\)', source)
    if param_list_match:
        param_list = param_list_match.group(1)
        for m in re.finditer(r'(\w+)\s*[=:]\s*([^,]+)', param_list):
            params.append({
                'type': 'parameter',
                'name': m.group(1).strip(),
                'value': m.group(2).strip()
            })
    
    return params
