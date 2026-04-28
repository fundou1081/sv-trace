"""
SV-Trace 技能发现API
提供统一的技能入口、测试状态和信任度信息
"""

SKILLS = {
    # PARSE 模块
    "sv_parser": {
        "name": "SVParser",
        "module": "parse",
        "class": "SVParser",
        "desc": "SystemVerilog解析器",
        "tier": 1,
        "test_status": "verified",
        "test_count": 830,
    },
    "param_resolver": {
        "name": "ParameterResolver",
        "module": "parse.params",
        "class": "ParameterResolver",
        "desc": "参数解析",
        "tier": 1,
        "test_status": "verified",
    },
    "class_extractor": {
        "name": "ClassExtractor",
        "module": "parse.class_utils",
        "class": "ClassExtractor",
        "desc": "Class/constraint提取",
        "tier": 2,
        "test_status": "verified",
    },
    "constraint_extractor": {
        "name": "ConstraintExtractor",
        "module": "parse.constraint",
        "class": "ConstraintExtractor",
        "desc": "约束提取",
        "tier": 2,
        "test_status": "verified",
    },
    # TRACE 模块
    "driver_tracer": {
        "name": "DriverTracer",
        "module": "trace.driver",
        "class": "DriverTracer",
        "desc": "信号驱动追踪",
        "tier": 1,
        "test_status": "verified",
        "test_count": 100,
    },
    "load_tracer": {
        "name": "LoadTracer",
        "module": "trace.load",
        "class": "LoadTracer",
        "desc": "信号负载追踪",
        "tier": 1,
        "test_status": "verified",
    },
    "connection_tracer": {
        "name": "ConnectionTracer",
        "module": "trace.connection",
        "class": "ConnectionTracer",
        "desc": "模块连接追踪",
        "tier": 1,
        "test_status": "verified",
    },
    "controlflow_tracer": {
        "name": "ControlFlowTracer",
        "module": "trace.controlflow",
        "class": "ControlFlowTracer",
        "desc": "控制流分析",
        "tier": 2,
        "test_status": "verified",
    },
    "datapath_analyzer": {
        "name": "DataPathAnalyzer",
        "module": "trace.datapath",
        "class": "DataPathAnalyzer",
        "desc": "数据路径分析",
        "tier": 2,
        "test_status": "verified",
    },
    "dependency_analyzer": {
        "name": "ModuleDependencyAnalyzer",
        "module": "debug.dependency",
        "class": "ModuleDependencyAnalyzer",
        "desc": "模块依赖分析",
        "tier": 2,
        "test_status": "verified",
    },
    # VERIFY 模块
    "fsm_extractor": {
        "name": "FSMExtractor",
        "module": "debug.fsm",
        "class": "FSMExtractor",
        "desc": "FSM状态机提取",
        "tier": 2,
        "test_status": "verified",
    },
    "coverage_advisor": {
        "name": "CoverageAdvisor",
        "module": "verify.coverage_advisor",
        "class": "CoverageAdvisor",
        "desc": "覆盖率指导",
        "tier": 3,
        "test_status": "experimental",
    },
    # LINT 模块
    "linter": {
        "name": "Linter",
        "module": "lint.linter",
        "class": "Linter",
        "desc": "代码风格检查",
        "tier": 3,
        "test_status": "verified",
    },
}

TIER_INFO = {
    1: {"name": "核心", "color": "G", "desc": "经过充分测试验证"},
    2: {"name": "重要", "color": "Y", "desc": "已验证但需更多测试"},
    3: {"name": "辅助", "color": "O", "desc": "实验性功能"},
    4: {"name": "探索", "color": "R", "desc": "探索性功能"},
}

STATUS_INFO = {
    "verified": {"name": "已验证", "color": "V"},
    "experimental": {"name": "实验性", "color": "E"},
    "needs_fix": {"name": "需修复", "color": "X"},
}


def list_skills(tier=None, status=None):
    result = []
    for key, info in SKILLS.items():
        if tier and info.get("tier") != tier:
            continue
        if status and info.get("test_status") != status:
            continue
        result.append({**info, "id": key})
    return result


def get_skill(skill_id):
    return SKILLS.get(skill_id)


def get_skill_tree():
    tree = {}
    for key, info in SKILLS.items():
        module = info["module"].split(".")[0]
        if module not in tree:
            tree[module] = []
        tree[module].append({**info, "id": key})
    return tree
