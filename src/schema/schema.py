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
            "parameters": [], "signals": {}, "loads": []
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
        dc = DriverCollector.extract_from_text(source)
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
        lt = LoadTracer.extract_from_text(source)
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
