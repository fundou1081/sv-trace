"""
SV-Trace 技能发现API
提供统一的技能入口、测试状态和信任度信息

该模块维护 SV-TRACE 项目中所有可用工具的元数据，
包括工具名称、模块路径、功能描述、层级和测试状态。

工具层级定义:
- Tier 1: 核心基础，经过充分测试
- Tier 2: 重要功能，已验证但需更多测试
- Tier 3: 辅助功能，实验性

Example:
    >>> from skills import list_skills, get_skill
    >>> tier1_tools = list_skills(tier=1)
    >>> parser = get_skill("sv_parser")
"""

SKILLS = {
    # ============ PARSE 模块 (基础解析) ============
    "sv_parser": {
        "name": "SVParser",
        "module": "parse",
        "class": "SVParser",
        "desc": "SystemVerilog解析器 - 解析SV代码生成AST",
        "tier": 1,
        "test_status": "verified",
        "test_count": 830,
        "inputs": ["sv_source_code"],
        "outputs": ["syntax_tree", "modules", "classes", "interfaces"],
    },
    "param_resolver": {
        "name": "ParameterResolver",
        "module": "parse.params",
        "class": "ParameterResolver",
        "desc": "参数解析 - 解析模块参数和局部参数",
        "tier": 1,
        "test_status": "verified",
        "inputs": ["sv_parser"],
        "outputs": ["resolved_params", "param_values"],
    },
    "class_extractor": {
        "name": "ClassExtractor",
        "module": "parse.class_utils",
        "class": "ClassExtractor",
        "desc": "Class提取 - 提取class定义、成员和方法",
        "tier": 2,
        "test_status": "verified",
        "inputs": ["sv_parser"],
        "outputs": ["classes", "members", "methods"],
    },
    "constraint_extractor": {
        "name": "ConstraintExtractor",
        "module": "parse.constraint",
        "class": "ConstraintExtractor",
        "desc": "约束提取 - 提取constraint块定义",
        "tier": 2,
        "test_status": "verified",
        "inputs": ["sv_parser", "class_extractor"],
        "outputs": ["constraints"],
    },
    
    # ============ TRACE 模块 (信号追踪) ============
    "driver_tracer": {
        "name": "DriverTracer",
        "module": "trace.driver",
        "class": "DriverCollector",
        "desc": "驱动追踪 - 追踪信号的驱动源",
        "tier": 1,
        "test_status": "verified",
        "test_count": 100,
        "inputs": ["sv_parser"],
        "outputs": ["drivers", "driver_graph", "sources"],
    },
    "load_tracer": {
        "name": "LoadTracer",
        "module": "trace.load",
        "class": "LoadTracer",
        "desc": "负载追踪 - 追踪信号被加载/使用的位置",
        "tier": 1,
        "test_status": "verified",
        "inputs": ["sv_parser"],
        "outputs": ["loads", "load_graph"],
    },
    "connection_tracer": {
        "name": "ConnectionTracer",
        "module": "trace.connection",
        "class": "ConnectionTracer",
        "desc": "连接追踪 - 追踪模块实例化和端口连接",
        "tier": 1,
        "test_status": "verified",
        "inputs": ["sv_parser"],
        "outputs": ["instances", "connections", "port_maps"],
    },
    "vcd_analyzer": {
        "name": "VCDAnalyzer",
        "module": "trace.vcd_analyzer",
        "class": "VCDAnalyzer",
        "desc": "VCD波形分析 - 分析VCD波形文件，测量频率/占空比",
        "tier": 2,
        "test_status": "verified",
        "inputs": ["vcd_file"],
        "outputs": ["waveforms", "transitions", "frequency", "duty_cycle"],
    },
    "flow_analyzer": {
        "name": "FlowAnalyzer",
        "module": "trace.flow_analyzer",
        "class": "SignalFlowAnalyzer",
        "desc": "信号流分析 - 分析信号在设计中的流动路径",
        "tier": 2,
        "test_status": "verified",
        "inputs": ["sv_parser", "driver_tracer", "load_tracer"],
        "outputs": ["flow_graph", "data_paths"],
    },
    "controlflow_tracer": {
        "name": "ControlFlowTracer",
        "module": "trace.controlflow",
        "class": "ControlFlowTracer",
        "desc": "控制流分析 - 分析always/always_ff等块的控制流",
        "tier": 2,
        "test_status": "verified",
        "inputs": ["sv_parser", "driver_tracer", "load_tracer"],
        "outputs": ["control_flow_graph", "paths"],
    },
    "datapath_analyzer": {
        "name": "DataPathAnalyzer",
        "module": "trace.datapath",
        "class": "DataPathAnalyzer",
        "desc": "数据路径分析 - 分析数据在模块间的传输路径",
        "tier": 2,
        "test_status": "verified",
        "inputs": ["sv_parser", "driver_tracer", "load_tracer", "connection_tracer", "controlflow_tracer"],
        "outputs": ["data_paths", "throughput", "bottlenecks"],
    },
    "dependency_analyzer": {
        "name": "ModuleDependencyAnalyzer",
        "module": "trace.dependency",
        "class": "DependencyAnalyzer",
        "desc": "依赖分析 - 分析模块间的依赖关系",
        "tier": 2,
        "test_status": "verified",
        "inputs": ["sv_parser", "connection_tracer"],
        "outputs": ["dependency_graph", "hierarchy"],
    },
    "signal_classifier": {
        "name": "SignalClassifier",
        "module": "trace.signal_classifier",
        "class": "SignalClassifier",
        "desc": "信号分类 - 将信号分类为clock/reset/data/control等",
        "tier": 2,
        "test_status": "verified",
        "inputs": ["sv_parser", "driver_tracer", "load_tracer"],
        "outputs": ["signal_categories"],
    },
    "pipeline_analyzer": {
        "name": "PipelineAnalyzer",
        "module": "trace.pipeline_analyzer",
        "class": "PipelineAnalyzer",
        "desc": "流水线分析 - 分析设计中的流水线结构",
        "tier": 2,
        "test_status": "verified",
        "inputs": ["sv_parser", "controlflow_tracer"],
        "outputs": ["pipeline_stages", "handshake_channels"],
    },
    
    # ============ DEBUG 模块 (调试分析) ============
    "fsm_extractor": {
        "name": "FSMExtractor",
        "module": "debug.fsm",
        "class": "FSMExtractor",
        "desc": "FSM提取 - 提取有限状态机定义",
        "tier": 2,
        "test_status": "verified",
        "inputs": ["sv_parser"],
        "outputs": ["fsm_states", "fsm_transitions", "reset_state"],
    },
    "cdc_analyzer": {
        "name": "CDCAnalyzer",
        "module": "debug.cdc",
        "class": "CDCAnalyzer",
        "desc": "CDC分析 - 检测跨时钟域问题",
        "tier": 3,
        "test_status": "experimental",
        "inputs": ["sv_parser", "signal_classifier", "dependency_analyzer"],
        "outputs": ["cdc_issues", "async_paths"],
    },
    
    # ============ VERIFY 模块 (验证辅助) ============
    "coverage_advisor": {
        "name": "CoverageAdvisor",
        "module": "verify.coverage_advisor",
        "class": "CoverageAdvisor",
        "desc": "覆盖率指导 - 提供覆盖率提升建议",
        "tier": 3,
        "test_status": "verified",
        "inputs": ["sv_parser", "fsm_extractor", "param_resolver"],
        "outputs": ["coverage_points", "coverage_advice"],
    },
    "constraint_check": {
        "name": "ConstraintChecker",
        "module": "verify.constraint_check",
        "class": "ConstraintAnalyzer",
        "desc": "约束检查 - 检查约束的一致性和可达性",
        "tier": 3,
        "test_status": "experimental",
        "inputs": ["sv_parser", "constraint_extractor"],
        "outputs": ["constraint_issues"],
    },
    
    # ============ LINT 模块 (代码检查) ============
    "linter": {
        "name": "Linter",
        "module": "lint.linter",
        "class": "Linter",
        "desc": "代码检查 - 检查代码风格和潜在问题",
        "tier": 3,
        "test_status": "verified",
        "inputs": ["sv_parser"],
        "outputs": ["lint_warnings", "lint_errors", "code_quality_score"],
    },
    "syntax_check": {
        "name": "SyntaxChecker",
        "module": "lint.syntax_check",
        "class": "SyntaxChecker",
        "desc": "语法检查 - 检查SystemVerilog语法错误",
        "tier": 1,
        "test_status": "verified",
        "inputs": ["sv_source_code"],
        "outputs": ["syntax_errors"],
    },
    "code_quality": {
        "name": "CodeQualityScorer",
        "module": "lint.code_quality",
        "class": "CodeQualityScorer",
        "desc": "代码质量评分 - 评估代码质量指标",
        "tier": 2,
        "test_status": "verified",
        "inputs": ["sv_parser"],
        "outputs": ["quality_score", "metrics"],
    },
    
    # ============ 估算模块 (Estimation) ============
    "area_estimator": {
        "name": "AreaEstimator",
        "module": "trace.area_estimator",
        "class": "AreaEstimator",
        "desc": "面积估算 - 估算设计资源占用",
        "tier": 3,
        "test_status": "experimental",
        "inputs": ["sv_parser"],
        "outputs": ["area_estimate", "resource_breakdown"],
    },
    "power_estimator": {
        "name": "PowerEstimator",
        "module": "trace.power_estimation",
        "class": "PowerEstimator",
        "desc": "功耗估算 - 估算设计功耗",
        "tier": 3,
        "test_status": "experimental",
        "inputs": ["sv_parser", "vcd_analyzer"],
        "outputs": ["power_estimate", "power_breakdown"],
    },
    "timing_path_extractor": {
        "name": "TimingPathExtractor",
        "module": "trace.timing_path",
        "class": "TimingPathExtractor",
        "desc": "时序路径提取 - 提取关键时序路径",
        "tier": 2,
        "test_status": "experimental",
        "inputs": ["sv_parser", "driver_tracer", "load_tracer"],
        "outputs": ["timing_paths", "critical_paths"],
    },
    
    # ============ 支持模块 ============
    "parse_warn": {
        "name": "ParseWarningHandler",
        "module": "trace.parse_warn",
        "class": "ParseWarningHandler",
        "desc": "解析警告处理 - 统一警告报告和处理",
        "tier": 1,
        "test_status": "verified",
        "inputs": [],
        "outputs": ["warnings", "error_report"],
    },
}

TIER_INFO = {
    1: {"name": "核心", "color": "G", "desc": "经过充分测试验证，稳定可靠"},
    2: {"name": "重要", "color": "Y", "desc": "已验证但需更多测试"},
    3: {"name": "辅助", "color": "O", "desc": "实验性功能，可能不稳定"},
    4: {"name": "探索", "color": "R", "desc": "探索性功能，待评估"},
}

STATUS_INFO = {
    "verified": {"name": "已验证", "color": "V"},
    "experimental": {"name": "实验性", "color": "E"},
    "needs_fix": {"name": "需修复", "color": "X"},
    "deprecated": {"name": "已废弃", "color": "D"},
}


def list_skills(tier=None, status=None):
    """列出工具
    
    Args:
        tier: 按层级过滤 (1/2/3/4)
        status: 按状态过滤 (verified/experimental/needs_fix/deprecated)
        
    Returns:
        List[Dict]: 工具信息列表
    """
    result = []
    for key, info in SKILLS.items():
        if tier and info.get("tier") != tier:
            continue
        if status and info.get("test_status") != status:
            continue
        result.append({**info, "id": key})
    return result


def get_skill(skill_id):
    """获取指定工具的信息
    
    Args:
        skill_id: 工具ID
        
    Returns:
        Dict: 工具信息，不存在则返回 None
    """
    return SKILLS.get(skill_id)


def get_skill_tree():
    """获取按模块组织的工具树
    
    Returns:
        Dict: {module_name: [tool_info_list]}
    """
    tree = {}
    for key, info in SKILLS.items():
        module = info["module"].split(".")[0]
        if module not in tree:
            tree[module] = []
        tree[module].append({**info, "id": key})
    return tree


def get_tool_dependencies(tool_id):
    """获取工具的依赖关系
    
    Args:
        tool_id: 工具ID
        
    Returns:
        Dict: 包含 depends_on 和 feeds_into 的字典
    """
    if tool_id not in SKILLS:
        return None
    
    tool = SKILLS[tool_id]
    return {
        "depends_on": tool.get("inputs", []),
        "feeds_into": [],  # 需要手动维护或从 SKILLS 反向推导
    }


def get_tool_graph():
    """获取工具依赖图
    
    Returns:
        Dict: {tool_id: {"upstream": [...], "downstream": [...]}}
    """
    graph = {}
    
    # 初始化
    for tool_id in SKILLS:
        graph[tool_id] = {"upstream": [], "downstream": []}
    
    # 构建图
    for tool_id, info in SKILLS.items():
        for input_tool in info.get("inputs", []):
            if input_tool in graph:
                graph[tool_id]["upstream"].append(input_tool)
                graph[input_tool]["downstream"].append(tool_id)
    
    return graph
