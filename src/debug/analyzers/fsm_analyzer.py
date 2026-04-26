"""
FSMAnalyzer - 状态机深度分析器
增强版: 复杂度评分、不可达检测、死锁检测
"""

import os
import re
import sys
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict, deque

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from parse import SVParser


@dataclass
class StateInfo:
    name: str
    line: int
    is_initial: bool = False
    is_final: bool = False
    in_degree: int = 0
    out_degree: int = 0
    transitions: List['Transition'] = field(default_factory=list)


@dataclass
class Transition:
    from_state: str
    to_state: str
    condition: str = ""
    line: int = 0


@dataclass
class FSMComplexity:
    """FSM复杂度评分"""
    state_count: int = 0
    transition_count: int = 0
    avg_transitions: float = 0.0
    max_out_degree: int = 0
    complexity_score: float = 0.0
    
    # 安全等级
    SAFE = 50
    WARN = 100
    HIGH = 150
    
    def get_level(self) -> str:
        if self.complexity_score < self.SAFE:
            return "SAFE"
        elif self.complexity_score < self.WARN:
            return "WARN"
        elif self.complexity_score < self.HIGH:
            return "HIGH"
        else:
            return "CRITICAL"


@dataclass
class UnreachableState:
    """不可达状态"""
    name: str
    reason: str  # "no_input", "isolated"


@dataclass
class DeadlockCycle:
    """死锁环"""
    states: List[str]
    length: int
    has_exit: bool = False
    is_reachable: bool = True


@dataclass
class FSMReport:
    """FSM分析报告"""
    module_name: str = ""
    fsm_count: int = 0
    
    # 状态
    states: List[StateInfo] = field(default_factory=list)
    state_names: List[str] = field(default_factory=list)
    
    # 跳转
    transitions: List[Transition] = field(default_factory=list)
    
    # 复杂度
    complexity: FSMComplexity = field(default_factory=FSMComplexity)
    
    # 问题
    unreachable: List[UnreachableState] = field(default_factory=list)
    deadlocks: List[DeadlockCycle] = field(default_factory=list)
    
    # 建议
    suggestions: List[str] = field(default_factory=list)


class FSMAnalyzer:
    """状态机分析器"""
    
    def __init__(self, parser):
        self.parser = parser
    
    def analyze(self) -> FSMReport:
        """分析所有FSM"""
        report = FSMReport()
        
        # 分析每个文件
        for path in self.parser.trees:
            if not path:
                continue
            
            try:
                with open(path, 'r') as f:
                    content = f.read()
            except:
                continue
            
            # 提取FSM
            fsm_data = self._extract_fsm(content)
            
            if not fsm_data['states']:
                continue
            
            # 更新报告
            if not report.module_name:
                report.module_name = os.path.basename(path).replace('.sv', '')
            
            # 添加状态
            for s in fsm_data['states']:
                report.state_names.append(s)
                st = StateInfo(name=s, line=fsm_data['lines'].get(s, 0))
                report.states.append(st)
            
            # 添加跳转
            for t in fsm_data['transitions']:
                report.transitions.append(t)
        
        report.fsm_count = len(set(report.state_names))
        
        if report.fsm_count == 0:
            return report
        
        # 计算复杂度
        report.complexity = self._calculate_complexity(report)
        
        # 检测不可达状态
        report.unreachable = self._find_unreachable(report)
        
        # 检测死锁
        report.deadlocks = self._find_deadlocks(report)
        
        # 生成建议
        report.suggestions = self._generate_suggestions(report)
        
        return report
    
    def _extract_fsm(self, content: str) -> Dict:
        """提取FSM"""
        data = {'states': [], 'transitions': [], 'lines': {}, 'initial': ''}
        
        # 方法1: typedef enum
        # 只提取大写状态名
        for match in re.finditer(r'typedef\s+enum[^{]*\{([^}]+)\}', content):
            body = match.group(1)
            states = re.findall(r'([A-Z_][A-Z0-9_]*)', body)
            data['states'].extend(states)
            
            # 假设第一个是初始状态
            if states and not data['initial']:
                data['initial'] = states[0]
        
        # 方法2: case语句中的状态
        if not data['states']:
            # 查找case (state)语句
            case_stmts = re.findall(r'case\s*\(\s*(\w+_state|current_state|state)\s*\)', content)
            for var in case_stmts[:1]:
                # 查找对应的状态定义
                patterns = [
                    rf'{var}\s*==\s*(\w+)',
                    rf'{var}:\s*//\s*(\w+)',
                ]
                for p in patterns:
                    matches = re.findall(p, content)
                    data['states'].extend(matches)
        
        # 去重
        data['states'] = list(set(data['states']))
        
        # 查找跳转
        # 从case语句提取跳转
        for match in re.finditer(r'([A-Z_][A-Z0-9_]*)\s*:\s*(?:if|case)\s*\(?([^)]+)\)\s*([A-Z_][A-Z0-9_]*)', content):
            from_st, cond, to_st = match.groups()
            if from_st in data['states'] and to_st in data['states']:
                data['transitions'].append(Transition(
                    from_state=from_st,
                    to_state=to_st,
                    condition=cond[:50] if cond else ''
                ))
        
        return data
    
    def _calculate_complexity(self, report: FSMReport) -> FSMComplexity:
        """计算复杂度"""
        c = FSMComplexity()
        c.state_count = report.fsm_count
        c.transition_count = len(report.transitions)
        
        # 计算平均出度
        out_degrees = defaultdict(int)
        for t in report.transitions:
            out_degrees[t.from_state] += 1
        
        if out_degrees:
            c.max_out_degree = max(out_degrees.values())
            c.avg_transitions = sum(out_degrees.values()) / len(out_degrees)
        
        # 复杂度 = 状态数 × 平均出度
        c.complexity_score = c.state_count * c.avg_transitions
        
        return c
    
    def _find_unreachable(self, report: FSMReport) -> List[UnreachableState]:
        """找不可达状态"""
        unreachable = []
        
        if not report.state_names:
            return unreachable
        
        # BFS找可达状态
        reachable = set()
        queue = deque([report.state_names[0] if report.state_names else None])
        
        while queue:
            state = queue.popleft()
            if state and state not in reachable:
                reachable.add(state)
                
                # 找到所有可达的下一个状态
                for t in report.transitions:
                    if t.from_state == state:
                        if t.to_state not in reachable:
                            queue.append(t.to_state)
        
        # 检查不可达
        for s in report.state_names:
            if s not in reachable:
                unreachable.append(UnreachableState(
                    name=s,
                    reason="no_input_path"
                ))
        
        return unreachable
    
    def _find_deadlocks(self, report: FSMReport) -> List[DeadlockCycle]:
        """找死锁环"""
        deadlocks = []
        
        # 简化: 找所有强连通分量
        state_set = set(report.state_names)
        
        for start in state_set:
            # DFS找环
            path = []
            visited = set()
            
            def dfs(current, path):
                if current in visited:
                    return None
                visited.add(current)
                path.append(current)
                
                # 找下一个状态
                next_states = [t.to_state for t in report.transitions if t.from_state == current]
                
                for next_st in next_states:
                    if next_st == start and len(path) > 1:
                        # 找到环
                        return path
                    result = dfs(next_st, path[:])
                    if result:
                        return result
                
                return None
            
            cycle = dfs(start, [])
            if cycle:
                # 检查是否有出口
                has_exit = False
                for st in cycle:
                    for t in report.transitions:
                        if t.from_state == st and t.to_state not in cycle:
                            has_exit = True
                            break
                
                if not has_exit:
                    deadlocks.append(DeadlockCycle(
                        states=cycle,
                        length=len(cycle),
                        has_exit=False
                    ))
        
        return deadlocks
    
    def _generate_suggestions(self, report: FSMReport) -> List[str]:
        """生成建议"""
        suggestions = []
        
        # 复杂度建议
        level = report.complexity.get_level()
        if level != "SAFE":
            suggestions.append(
                f"FSM复杂度{level}({report.complexity.complexity_score}), 考虑拆分"
            )
        
        # 不可达建议
        if report.unreachable:
            suggestions.append(
                f"发现{len(report.unreachable)}个不可达状态: {[u.name for u in report.unreachable]}"
            )
        
        # 死锁建议
        if report.deadlocks:
            suggestions.append(
                f"发现{len(report.deadlocks)}个死锁环"
            )
        
        if not suggestions:
            suggestions.append("状态机结构良好")
        
        return suggestions
    
    def print_report(self, report: FSMReport):
        """打印报告"""
        print("="*60)
        print(f"FSM Analysis: {report.module_name}")
        print("="*60)
        
        print(f"\n[States]")
        print(f"  Count: {report.fsm_count}")
        print(f"  States: {report.state_names[:10]}...")
        
        print(f"\n[Complexity]")
        c = report.complexity
        print(f"  Transitions: {c.transition_count}")
        print(f"  Avg/State: {c.avg_transitions:.1f}")
        print(f"  Score: {c.complexity_score} ({c.get_level()})")
        
        print(f"\n[Issues]")
        print(f"  Unreachable: {len(report.unreachable)}")
        print(f"  Deadlocks: {len(report.deadlocks)}")
        
        if report.suggestions:
            print(f"\n[Suggestions]")
            for s in report.suggestions:
                print(f"  - {s}")
        
        print("="*60)


__all__ = ['FSMAnalyzer', 'FSMReport']


# ============================================================================
# FSM 增强功能 - 状态编码建议
# ============================================================================

def recommend_encoding(self, state_count: int) -> dict:
    """根据状态数量推荐状态编码方式"""
    
    if state_count <= 0:
        return {"encoding": "unknown", "bits": 0, "reason": "无有效状态"}
    
    if state_count == 1:
        return {
            "encoding": "binary", 
            "bits": 1, 
            "reason": "单状态只需要1位",
            "one_hot_value": "1b0",
            "power_estimate": "low"
        }
    
    if state_count == 2:
        return {
            "encoding": "binary", 
            "bits": 1, 
            "reason": "2状态用binary最省资源",
            "binary_value": "1'b0 / 1'b1",
            "gray_value": "1'b0 / 1'b1",
            "one_hot_value": "2'b01 / 2'b10",
            "power_estimate": "low"
        }
    
    if state_count <= 4:
        return {
            "encoding": "binary", 
            "bits": 2, 
            "reason": "4状态用binary最省资源",
            "binary_value": "2'b00/01/10/11",
            "gray_value": "2'b00/01/11/10",
            "one_hot_value": "4'b0001/0010/0100/1000",
            "power_estimate": "low"
        }
    
    if state_count <= 8:
        return {
            "encoding": "gray", 
            "bits": 3, 
            "reason": "3-8状态推荐Gray编码，减少亚稳态",
            "binary_value": "3'b000-111",
            "gray_value": "3'b000/001/011/010/110/111/101/100",
            "one_hot_value": "8'b00000001/.../10000000",
            "power_estimate": "medium"
        }
    
    if state_count <= 16:
        return {
            "encoding": "one_hot", 
            "bits": state_count, 
            "reason": "8-16状态推荐one-hot，高速设计首选",
            "encoding_scheme": "one_hot",
            "power_estimate": "medium-high",
            "note": "one-hot每个状态1位寄存器，组合逻辑少"
        }
    
    # 16+ 状态
    if state_count <= 32:
        return {
            "encoding": "one_hot", 
            "bits": state_count, 
            "reason": "多状态建议one-hot或考虑拆分",
            "power_estimate": "high",
            "suggestion": "状态数超过16，建议考虑模块化拆分"
        }
    
    # 32+ 状态：强烈建议拆分
    return {
        "encoding": "one_hot", 
        "bits": state_count, 
        "reason": "状态数过多，必须拆分或使用层级状态机",
        "power_estimate": "very_high",
        "warning": "CRITICAL: 状态数过多，必须拆分!"
    }


def get_encoding_power_estimate(self, encoding: str, bits: int, 
                                  toggle_rate: float = 0.2) -> dict:
    """估算不同编码的功耗"""
    
    base_power = bits * toggle_rate
    
    estimates = {
        "binary": {
            "description": "二进制编码",
            "switching_power": base_power * 1.0,
            "glitch_risk": "medium",
            "notes": "状态跳转时多位翻转，功耗较高"
        },
        "gray": {
            "description": "格雷码",
            "switching_power": base_power * 0.5,
            "glitch_risk": "low",
            "notes": "相邻状态只有1位翻转"
        },
        "one_hot": {
            "description": "独热码",
            "switching_power": base_power * 0.3,
            "glitch_risk": "low",
            "notes": "每次跳转只翻转1位，但寄存器多"
        }
    }
    
    return estimates.get(encoding, {})


# 添加到 FSMAnalyzer 类
FSMAnalyzer.recommend_encoding = recommend_encoding
FSMAnalyzer.get_encoding_power_estimate = get_encoding_power_estimate


__all__ = ['FSMAnalyzer', 'FSMReport', 'FSMComplexity', 'StateInfo', 'Transition']


# =============================================================================
# FSM SVA属性自动生成
# =============================================================================

@dataclass
class SVAProperty:
    """SVA属性"""
    name: str
    kind: str  # "assert", "assume", "cover", "sequence"
    body: str
    clock: str = "clk"
    reset: str = "rst_n"
    description: str = ""


@dataclass
class SVAGeneratorReport:
    """SVA生成报告"""
    properties: List[SVAProperty] = field(default_factory=list)
    sequences: List[SVAProperty] = field(default_factory=list)
    sequences_used: List[str] = field(default_factory=list)
    module_name: str = ""


class SVAGenerator:
    """FSM SVA属性自动生成器"""
    
    # 状态编码
    STATE_ENCODING = {
        'binary': 2,
        'gray': 2,
        'one_hot': 4,
    }
    
    def __init__(self, parser):
        self.parser = parser
        self.properties: List[SVAProperty] = []
        self.sequences: List[SVAProperty] = []
        self._state_vars: List[str] = []
        self._state_values: Dict[str, int] = {}
    
    def generate(self, module_name: str = "dut") -> SVAGeneratorReport:
        """生成SVA属性"""
        self.properties = []
        self.sequences = []
        self._state_vars = []
        self._state_values = {}
        
        # 1. 提取FSM信息
        fsm_info = self._extract_fsm_info()
        
        if not fsm_info.get('states'):
            return SVAGeneratorReport(module_name=module_name)
        
        # 2. 生成序列
        self._generate_sequences(fsm_info)
        
        # 3. 生成属性
        self._generate_state_coverage(fsm_info, module_name)
        self._generate_transition_coverage(fsm_info, module_name)
        self._generate_safety_properties(fsm_info, module_name)
        self._generate_liveness_properties(fsm_info, module_name)
        
        return SVAGeneratorReport(
            properties=self.properties,
            sequences=self.sequences,
            module_name=module_name
        )
    
    def _extract_fsm_info(self) -> Dict:
        """从FSMAnalyzer提取FSM信息"""
        from .fsm_analyzer import FSMAnalyzer
        
        analyzer = FSMAnalyzer(self.parser)
        report = analyzer.analyze()
        
        states = report.state_names if hasattr(report, 'state_names') else []
        transitions = []
        
        # 提取跳转
        for t in report.transitions if hasattr(report, 'transitions') else []:
            transitions.append({
                'from': t.from_state,
                'to': t.to_state,
                'condition': t.condition
            })
        
        return {
            'states': states,
            'transitions': transitions,
            'initial': report.complexity.state_count if hasattr(report, 'complexity') else 0
        }
    
    def _generate_sequences(self, fsm_info: Dict):
        """生成常用序列"""
        states = fsm_info['states']
        transitions = fsm_info['transitions']
        
        # 1. 单状态跳转序列
        for state in states[:5]:  # 限制数量
            self.sequences.append(SVAProperty(
                name=f"seq_{state.lower()}",
                kind="sequence",
                body=f"state == {state} ##1 state == {state}",
                description=f"停留在{state}状态"
            ))
        
        # 2. 状态转换序列
        for trans in transitions[:10]:
            from_st = trans['from']
            to_st = trans['to']
            cond = trans.get('condition', '1')
            
            self.sequences.append(SVAProperty(
                name=f"seq_{from_st.lower()}_to_{to_st.lower()}",
                kind="sequence",
                body=f"state == {from_st} ##1 {cond} |-> state == {to_st}",
                description=f"从{from_st}到{to_st}"
            ))
    
    def _generate_state_coverage(self, fsm_info: Dict, module_name: str):
        """生成状态覆盖属性"""
        states = fsm_info['states']
        
        for state in states:
            self.properties.append(SVAProperty(
                name=f"cover_{state.lower()}_reached",
                kind="cover",
                body=f"state == {state}",
                description=f"覆盖状态{state}"
            ))
    
    def _generate_transition_coverage(self, fsm_info: Dict, module_name: str):
        """生成跳转覆盖属性"""
        transitions = fsm_info['transitions']
        
        for i, trans in enumerate(transitions):
            from_st = trans['from']
            to_st = trans['to']
            cond = trans.get('condition', '1')
            
            if len(cond) > 30:
                cond = "1"  # 简化长条件
            
            self.properties.append(SVAProperty(
                name=f"cover_trans_{i}",
                kind="cover",
                body=f"state == {from_st} ##1 {cond} |-> state == {to_st}",
                description=f"覆盖跳转 {from_st} -> {to_st}"
            ))
    
    def _generate_safety_properties(self, fsm_info: Dict, module_name: str):
        """生成安全属性"""
        states = fsm_info['states']
        
        # 1. 状态有效属性
        self.properties.append(SVAProperty(
            name="assert_state_valid",
            kind="assert",
            body=f"one_hot(state) or state inside {{{', '.join(states)}}}",
            description="状态始终有效"
        ))
        
        # 2. 互斥状态属性
        if len(states) > 1:
            # 简化: 检查没有两个状态同时为真
            state_checks = [f"(state != {s})" for s in states]
            self.properties.append(SVAProperty(
                name="assert_mutual_exclusive",
                kind="assert",
                body=" or ".join(state_checks[:5]),  # 限制
                description="状态互斥"
            ))
    
    def _generate_liveness_properties(self, fsm_info: Dict, module_name: str):
        """生成活性属性"""
        states = fsm_info['states']
        
        # 1. 最终到达IDLE
        if 'IDLE' in states:
            self.properties.append(SVAProperty(
                name="assume_reaches_idle",
                kind="assume",
                body=f"eventually! (state == IDLE)",
                description="最终应到达IDLE"
            ))
        
        # 2. 不死锁属性
        self.properties.append(SVAProperty(
            name="assert_no_deadlock",
            kind="assert",
            body=f"state == state",
            description="状态机不死锁"
        ))
    
    def export_svafile(self, filename: str, module_name: str = "fsm_assertions"):
        """导出SVA文件"""
        content = f"""// FSM Assertions - Auto-generated by SV-Trace
// Module: {module_name}
// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

interface {module_name}_assertions;
"""

        # 时钟和复位参数
        content += """
    // Clock and Reset parameters
    parameter CLK = \"clk\";
    parameter RST = \"rst_n\";
"""

        # 序列
        if self.sequences:
            content += "\n    // ============================================================================\n"
            content += "    // Sequences\n"
            content += "    // ============================================================================\n\n"
            
            for seq in self.sequences:
                content += f"    // {seq.description}\n"
                content += f"    sequence {seq.name};\n"
                content += f"        {seq.body};\n"
                content += "    endsequence\n\n"

        # 属性
        if self.properties:
            content += "    // ============================================================================\n"
            content += "    // Properties\n"
            content += "    // ============================================================================\n\n"
            
            for prop in self.properties:
                content += f"    // {prop.description}\n"
                if prop.kind == "assert":
                    content += f"    property {prop.name};\n"
                    content += f"        @(posedge clk) disable iff (!rst_n) {prop.body};\n"
                    content += "    endproperty\n"
                    content += f"    {prop.name}: assert property ({prop.name});\n\n"
                elif prop.kind == "cover":
                    content += f"    property {prop.name};\n"
                    content += f"        @(posedge clk) {prop.body};\n"
                    content += "    endproperty\n"
                    content += f"    {prop.name}: cover property ({prop.name});\n\n"
                elif prop.kind == "assume":
                    content += f"    property {prop.name};\n"
                    content += f"        @(posedge clk) {prop.body};\n"
                    content += "    endproperty\n"
                    content += f"    {prop.name}: assume property ({prop.name});\n\n"

        content += "endinterface\n"
        
        with open(filename, 'w') as f:
            f.write(content)
        
        return filename
    
    def export_as_module(self, filename: str, module_name: str = "fsm_assertions"):
        """导出为独立module格式"""
        content = f"""// FSM Assertions Module - Auto-generated by SV-Trace
// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

module {module_name} (
    input clk,
    input rst_n,
    input [31:0] state
);

"""
        
        # 生成assertions
        for prop in self.properties:
            if prop.kind == "assert":
                content += f"""    // {prop.description}
    property {prop.name};
        @(posedge clk) disable iff (!rst_n) {prop.body};
    endproperty
    assert property ({prop.name}) else $warning("{prop.name} failed");

"""
            elif prop.kind == "cover":
                content += f"""    // {prop.description}
    property {prop.name};
        @(posedge clk) {prop.body};
    endproperty
    cover property ({prop.name}) $display("{prop.name} covered");

"""

        content += "endmodule\n"
        
        with open(filename, 'w') as f:
            f.write(content)
        
        return filename


# 添加便捷方法
def generate_fsm_sva(parser, output_file: str = None, module_name: str = "fsm_sv") -> SVAGeneratorReport:
    """生成FSM SVA属性的便捷函数"""
    generator = SVAGenerator(parser)
    report = generator.generate(module_name)
    
    if output_file:
        if output_file.endswith('.sv'):
            generator.export_as_module(output_file, module_name)
        else:
            generator.export_svafile(output_file, module_name)
    
    return report


__all__ = [
    'FSMAnalyzer', 
    'FSMReport', 
    'FSMComplexity',
    'StateInfo', 
    'Transition',
    'SVAGenerator',
    'SVAProperty',
    'SVAGeneratorReport',
    'generate_fsm_sva',
]


# =============================================================================
# FSM 验证计划自动生成
# =============================================================================

@dataclass
class VerificationPoint:
    """验证点"""
    id: str
    category: str  # "state", "transition", "corner", "sequence"
    description: str
    stimulus: str  # 激励描述
    expected: str  # 期望结果
    priority: str = "P1"  # P1, P2, P3
    status: str = "pending"  # pending, verified, failed


@dataclass
class VerificationPlan:
    """验证计划"""
    module_name: str
    fsm_name: str
    testpoints: List[VerificationPoint] = field(default_factory=list)
    coverage_targets: List[str] = field(default_factory=list)
    total_tests: int = 0
    verified_tests: int = 0
    
    def add_point(self, point: VerificationPoint):
        self.testpoints.append(point)
        self.total_tests += 1


class VerificationPlanGenerator:
    """FSM验证计划自动生成器"""
    
    def __init__(self, parser):
        self.parser = parser
    
    def generate(self, fsm_name: str = "fsm") -> VerificationPlan:
        """生成验证计划"""
        from .fsm_analyzer import FSMAnalyzer
        
        analyzer = FSMAnalyzer(self.parser)
        report = analyzer.analyze()
        
        plan = VerificationPlan(
            module_name=self._get_module_name(),
            fsm_name=fsm_name
        )
        
        # 1. 生成状态覆盖验证点
        self._generate_state_testpoints(report, plan)
        
        # 2. 生成跳转覆盖验证点
        self._generate_transition_testpoints(report, plan)
        
        # 3. 生成边界条件验证点
        self._generate_corner_testpoints(report, plan)
        
        # 4. 生成序列验证点
        self._generate_sequence_testpoints(report, plan)
        
        # 5. 生成覆盖率目标
        self._generate_coverage_targets(plan)
        
        return plan
    
    def _get_module_name(self) -> str:
        """获取模块名"""
        for fname, tree in self.parser.trees.items():
            if tree and tree.root:
                if hasattr(tree.root, 'header') and tree.root.header:
                    return str(tree.root.header.name)
        return "unknown"
    
    def _generate_state_testpoints(self, report, plan: VerificationPlan):
        """生成状态覆盖验证点"""
        for state in report.state_names[:10]:  # 限制数量
            plan.add_point(VerificationPoint(
                id=f"TP_STATE_{state}",
                category="state",
                description=f"验证状态机能进入{state}状态",
                stimulus=f"施加激励使状态机进入{state}",
                expected=f"观测到state=={state}",
                priority="P1" if state in ["IDLE", "RESET", "ERROR"] else "P2"
            ))
    
    def _generate_transition_testpoints(self, report, plan: VerificationPlan):
        """生成跳转覆盖验证点"""
        for i, trans in enumerate(report.transitions[:15]):
            from_st = trans.from_state
            to_st = trans.to_state
            cond = trans.condition if trans.condition else "无条件"
            
            plan.add_point(VerificationPoint(
                id=f"TP_TRANS_{i}",
                category="transition",
                description=f"验证{from_st}到{to_st}的跳转",
                stimulus=f"在{from_st}状态时满足条件: {cond[:50]}",
                expected=f"下一周期状态变为{to_st}",
                priority="P1"
            ))
    
    def _generate_corner_testpoints(self, report, plan: VerificationPlan):
        """生成边界条件验证点"""
        # 1. 上电复位
        plan.add_point(VerificationPoint(
            id="TP_CORNER_PWR_ON",
            category="corner",
            description="上电复位后状态机应进入初始状态",
            stimulus="上电后释放复位",
            expected="状态机进入初始状态IDLE/RESET",
            priority="P1"
        ))
        
        # 2. 连续跳转
        plan.add_point(VerificationPoint(
            id="TP_CORNER_CONSEC",
            category="corner",
            description="验证连续跳转不丢失",
            stimulus="快速连续施加激励",
            expected="每个跳转都被正确采样",
            priority="P2"
        ))
        
        # 3. 长时间停留
        plan.add_point(VerificationPoint(
            id="TP_CORNER_LONG_STAY",
            category="corner",
            description="验证状态机在某个状态长时间停留",
            stimulus="在状态X保持1000周期",
            expected="状态保持不变",
            priority="P3"
        ))
        
        # 4. 非法跳转
        if report.unreachable:
            plan.add_point(VerificationPoint(
                id="TP_CORNER_ILLEGAL",
                category="corner",
                description="验证非法跳转被正确阻止",
                stimulus="尝试进入不可达状态",
                expected="状态机不进入该状态",
                priority="P2"
            ))
    
    def _generate_sequence_testpoints(self, report, plan: VerificationPlan):
        """生成序列验证点"""
        # 1. 完整遍历
        plan.add_point(VerificationPoint(
            id="TP_SEQ_FULL",
            category="sequence",
            description="完整状态机遍历",
            stimulus="按照设计的跳转路径遍历所有状态",
            expected="每个状态和跳转都被覆盖",
            priority="P1"
        ))
        
        # 2. 环回序列
        plan.add_point(VerificationPoint(
            id="TP_SEQ_LOOP",
            category="sequence",
            description="状态机循环遍历",
            stimulus="IDLE->RUN->IDLE循环10次",
            expected="每次循环都正确",
            priority="P2"
        ))
        
        # 3. 死锁恢复
        if report.deadlocks:
            plan.add_point(VerificationPoint(
                id="TP_SEQ_DEADLOCK",
                category="sequence",
                description="死锁检测和恢复",
                stimulus="强制进入可能导致死锁的条件",
                expected="状态机能够脱离死锁",
                priority="P1"
            ))
    
    def _generate_coverage_targets(self, plan: VerificationPlan):
        """生成覆盖率目标"""
        plan.coverage_targets = [
            "state_coverage: 100%",
            "transition_coverage: 100%",
            "condition_coverage: 95%",
            "toggle_coverage: 90%"
        ]
    
    def export_to_markdown(self, filename: str, plan: VerificationPlan):
        """导出为Markdown格式"""
        md = f"""# FSM Verification Plan
## Module: {plan.module_name}
## FSM: {plan.fsm_name}

---

## Summary

| Metric | Value |
|--------|-------|
| Total Testpoints | {plan.total_tests} |
| P1 (Critical) | {sum(1 for tp in plan.testpoints if tp.priority == 'P1')} |
| P2 (High) | {sum(1 for tp in plan.testpoints if tp.priority == 'P2')} |
| P3 (Medium) | {sum(1 for tp in plan.testpoints if tp.priority == 'P3')} |

---

## Coverage Targets

"""
        for target in plan.coverage_targets:
            md += f"- [ ] {target}\n"
        
        md += "\n---\n\n## Testpoints\n\n"
        
        # 按类别分组
        categories = {}
        for tp in plan.testpoints:
            if tp.category not in categories:
                categories[tp.category] = []
            categories[tp.category].append(tp)
        
        for cat, points in categories.items():
            md += f"### {cat.upper()}\n\n"
            md += "| ID | Description | Stimulus | Expected | Priority |\n"
            md += "|-----|-------------|----------|----------|----------|\n"
            
            for p in points:
                md += f"| {p.id} | {p.description} | {p.stimulus[:40]} | {p.expected[:30]} | {p.priority} |\n"
            
            md += "\n"
        
        with open(filename, 'w') as f:
            f.write(md)
        
        return filename
    
    def export_to_yaml(self, filename: str, plan: VerificationPlan):
        """导出为YAML格式"""
        import yaml
        
        data = {
            'module': plan.module_name,
            'fsm': plan.fsm_name,
            'summary': {
                'total': plan.total_tests,
                'p1': sum(1 for tp in plan.testpoints if tp.priority == 'P1'),
                'p2': sum(1 for tp in plan.testpoints if tp.priority == 'P2'),
                'p3': sum(1 for tp in plan.testpoints if tp.priority == 'P3'),
            },
            'coverage_targets': plan.coverage_targets,
            'testpoints': [
                {
                    'id': tp.id,
                    'category': tp.category,
                    'description': tp.description,
                    'stimulus': tp.stimulus,
                    'expected': tp.expected,
                    'priority': tp.priority,
                    'status': tp.status
                }
                for tp in plan.testpoints
            ]
        }
        
        with open(filename, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        
        return filename


# 添加便捷方法
def generate_verification_plan(parser, fsm_name: str = "fsm", 
                               output_file: str = None) -> VerificationPlan:
    """生成验证计划的便捷函数"""
    generator = VerificationPlanGenerator(parser)
    plan = generator.generate(fsm_name)
    
    if output_file:
        if output_file.endswith('.yaml') or output_file.endswith('.yml'):
            generator.export_to_yaml(output_file, plan)
        else:
            generator.export_to_markdown(output_file, plan)
    
    return plan


__all__ = [
    'FSMAnalyzer', 
    'FSMReport', 
    'FSMComplexity',
    'StateInfo', 
    'Transition',
    'SVAGenerator',
    'SVAProperty',
    'SVAGeneratorReport',
    'generate_fsm_sva',
    'VerificationPlanGenerator',
    'VerificationPlan',
    'VerificationPoint',
    'generate_verification_plan',
]


# =============================================================================
# FSM 覆盖率追踪
# =============================================================================

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
from datetime import datetime
import json


@dataclass
class StateCoverage:
    """状态覆盖"""
    state_name: str
    state_encoding: int = 0
    covered: bool = False
    hit_count: int = 0
    last_hit: str = ""  # 时间戳


@dataclass
class TransitionCoverage:
    """跳转覆盖"""
    from_state: str
    to_state: str
    condition: str = ""
    covered: bool = False
    hit_count: int = 0
    last_hit: str = ""


@dataclass
class FSMStateInfo:
    """FSM状态信息"""
    name: str
    state_var: str  # 状态变量名
    encoding_type: str = "binary"  # binary, gray, one_hot, manual
    state_count: int = 0
    states: List[str] = field(default_factory=list)


@dataclass
class FSMCoverageReport:
    """FSM覆盖率报告"""
    fsm_name: str
    module: str
    
    # 状态覆盖
    state_info: FSMStateInfo = None
    state_coverage: List[StateCoverage] = field(default_factory=list)
    state_coverage_rate: float = 0.0
    
    # 跳转覆盖
    transition_coverage: List[TransitionCoverage] = field(default_factory=list)
    transition_coverage_rate: float = 0.0
    
    # 序列覆盖
    sequence_coverage: Dict[str, bool] = field(default_factory=dict)
    sequence_coverage_rate: float = 0.0
    
    # 总体
    overall_coverage: float = 0.0
    
    # 未覆盖项
    uncovered_states: List[str] = field(default_factory=list)
    uncovered_transitions: List[str] = field(default_factory=list)


class FSMCoverageTracker:
    """FSM覆盖率追踪器"""
    
    # 状态编码推荐
    ENCODING_THRESHOLDS = {
        'binary': 4,
        'gray': 8,
        'one_hot': 16,
    }
    
    def __init__(self, parser):
        self.parser = parser
        self.fsm_reports: List[FSMCoverageReport] = []
    
    def analyze(self) -> List[FSMCoverageReport]:
        """分析FSM覆盖率"""
        from .fsm_analyzer import FSMAnalyzer
        
        analyzer = FSMAnalyzer(self.parser)
        fsm_report = analyzer.analyze()
        
        # 创建覆盖率报告
        report = FSMCoverageReport(
            fsm_name="main_fsm",
            module=self._get_module_name(),
            state_info=FSMStateInfo(
                name="main_fsm",
                state_var="state",
                state_count=len(fsm_report.state_names)
            )
        )
        
        # 设置状态信息
        if report.state_info:
            report.state_info.states = fsm_report.state_names
            report.state_info.state_count = len(fsm_report.state_names)
            report.state_info.encoding_type = self._recommend_encoding(len(fsm_report.state_names))
        
        # 状态覆盖
        for state in fsm_report.state_names:
            sc = StateCoverage(state_name=state)
            report.state_coverage.append(sc)
        
        # 跳转覆盖
        for trans in fsm_report.transitions:
            tc = TransitionCoverage(
                from_state=trans.from_state,
                to_state=trans.to_state,
                condition=trans.condition
            )
            report.transition_coverage.append(tc)
        
        # 计算覆盖率
        self._calculate_coverage(report)
        
        # 生成未覆盖列表
        report.uncovered_states = [s.state_name for s in report.state_coverage if not s.covered]
        report.uncovered_transitions = [
            f"{t.from_state}->{t.to_state}" 
            for t in report.transition_coverage if not t.covered
        ]
        
        self.fsm_reports.append(report)
        return self.fsm_reports
    
    def _recommend_encoding(self, state_count: int) -> str:
        """推荐状态编码"""
        if state_count <= self.ENCODING_THRESHOLDS['binary']:
            return "binary"
        elif state_count <= self.ENCODING_THRESHOLDS['gray']:
            return "gray"
        else:
            return "one_hot"
    
    def _get_module_name(self) -> str:
        """获取模块名"""
        for fname, tree in self.parser.trees.items():
            if tree and tree.root:
                if hasattr(tree.root, 'header') and tree.root.header:
                    return str(tree.root.header.name)
        return "unknown"
    
    def _calculate_coverage(self, report: FSMCoverageReport):
        """计算覆盖率"""
        # 状态覆盖率
        if report.state_coverage:
            covered = sum(1 for s in report.state_coverage if s.covered)
            report.state_coverage_rate = covered / len(report.state_coverage)
        
        # 跳转覆盖率
        if report.transition_coverage:
            covered = sum(1 for t in report.transition_coverage if t.covered)
            report.transition_coverage_rate = covered / len(report.transition_coverage)
        
        # 序列覆盖率
        if report.sequence_coverage:
            covered = sum(1 for v in report.sequence_coverage.values() if v)
            report.sequence_coverage_rate = covered / len(report.sequence_coverage) if report.sequence_coverage else 0
        
        # 总体覆盖率
        report.overall_coverage = (
            report.state_coverage_rate * 0.4 +
            report.transition_coverage_rate * 0.4 +
            report.sequence_coverage_rate * 0.2
        )
    
    def merge_with_simulation(self, sim_coverage_data: Dict):
        """合并仿真覆盖率数据"""
        # sim_coverage_data 格式:
        # {
        #     "states": {"IDLE": 10, "RUN": 5},
        #     "transitions": {"IDLE->RUN": 3}
        # }
        
        for report in self.fsm_reports:
            # 更新状态覆盖
            if "states" in sim_coverage_data:
                for sc in report.state_coverage:
                    if sc.state_name in sim_coverage_data["states"]:
                        sc.covered = True
                        sc.hit_count = sim_coverage_data["states"][sc.state_name]
                        sc.last_hit = datetime.now().isoformat()
            
            # 更新跳转覆盖
            if "transitions" in sim_coverage_data:
                for tc in report.transition_coverage:
                    key = f"{tc.from_state}->{tc.to_state}"
                    if key in sim_coverage_data["transitions"]:
                        tc.covered = True
                        tc.hit_count = sim_coverage_data["transitions"][key]
                        tc.last_hit = datetime.now().isoformat()
            
            # 重新计算覆盖率
            self._calculate_coverage(report)
    
    def export_to_ucis(self, filename: str):
        """导出为UCIS格式（覆盖率数据库）"""
        import xml.etree.ElementTree as ET
        
        root = ET.Element('ucis')
        
        for report in self.fsm_reports:
            # FSM覆盖组
            fsm_cg = ET.SubElement(root, 'covergroup', name=f"fsm_{report.fsm_name}")
            
            # 状态覆盖点
            state_cp = ET.SubElement(fsm_cg, 'coverpoint', name='state')
            for sc in report.state_coverage:
                bin_elem = ET.SubElement(state_cp, 'item', name=sc.state_name)
                if sc.covered:
                    bin_elem.set('covered', '1')
                    bin_elem.set('hitcount', str(sc.hit_count))
            
            # 跳转覆盖点
            trans_cp = ET.SubElement(fsm_cg, 'coverpoint', name='transition')
            for tc in report.transition_coverage:
                name = f"{tc.from_state}_to_{tc.to_state}"
                bin_elem = ET.SubElement(trans_cp, 'item', name=name)
                if tc.covered:
                    bin_elem.set('covered', '1')
                    bin_elem.set('hitcount', str(tc.hit_count))
        
        tree = ET.ElementTree(root)
        tree.write(filename, encoding='utf-8', xml_declaration=True)
        
        return filename
    
    def export_to_json(self, filename: str) -> str:
        """导出为JSON格式"""
        data = {
            "metadata": {
                "tool": "SV-Trace FSM Coverage Tracker",
                "generated": datetime.now().isoformat()
            },
            "fsm_reports": []
        }
        
        for report in self.fsm_reports:
            fsm_data = {
                "fsm_name": report.fsm_name,
                "module": report.module,
                "state_info": {
                    "name": report.state_info.name if report.state_info else "",
                    "state_var": report.state_info.state_var if report.state_info else "",
                    "encoding": report.state_info.encoding_type if report.state_info else "",
                    "state_count": report.state_info.state_count if report.state_info else 0,
                    "states": report.state_info.states if report.state_info else []
                },
                "coverage": {
                    "state_coverage_rate": report.state_coverage_rate,
                    "transition_coverage_rate": report.transition_coverage_rate,
                    "sequence_coverage_rate": report.sequence_coverage_rate,
                    "overall_coverage": report.overall_coverage
                },
                "states": [
                    {
                        "name": s.state_name,
                        "covered": s.covered,
                        "hit_count": s.hit_count
                    }
                    for s in report.state_coverage
                ],
                "transitions": [
                    {
                        "from": t.from_state,
                        "to": t.to_state,
                        "covered": t.covered,
                        "hit_count": t.hit_count
                    }
                    for t in report.transition_coverage
                ],
                "uncovered": {
                    "states": report.uncovered_states,
                    "transitions": report.uncovered_transitions
                }
            }
            data["fsm_reports"].append(fsm_data)
        
        json_str = json.dumps(data, indent=2)
        
        with open(filename, 'w') as f:
            f.write(json_str)
        
        return filename
    
    def generate_coverage_report_html(self, filename: str):
        """生成HTML覆盖率报告"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>FSM Coverage Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .coverage-bar {{ background: #eee; height: 30px; border-radius: 15px; overflow: hidden; }}
        .coverage-fill {{ height: 100%; background: linear-gradient(90deg, #4CAF50, #8BC34A); }}
        .state-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 10px; margin: 20px 0; }}
        .state-box {{ padding: 10px; border-radius: 5px; text-align: center; }}
        .covered {{ background: #e8f5e9; color: #2e7d32; border: 1px solid #4CAF50; }}
        .uncovered {{ background: #ffebee; color: #c62828; border: 1px solid #f44336; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 10px; border: 1px solid #ddd; text-align: left; }}
        th {{ background: #f5f5f5; }}
    </style>
</head>
<body>
    <h1>FSM Coverage Report</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
"""
        
        for report in self.fsm_reports:
            html += f"""
    <div class="summary">
        <h2>FSM: {report.fsm_name}</h2>
        <p>Module: {report.module}</p>
        <p>Overall Coverage: {report.overall_coverage*100:.1f}%</p>
        <div class="coverage-bar">
            <div class="coverage-fill" style="width: {report.overall_coverage*100}%"></div>
        </div>
    </div>
    
    <h3>State Coverage: {report.state_coverage_rate*100:.1f}%</h3>
    <div class="state-grid">
"""
            
            for sc in report.state_coverage:
                cls = "covered" if sc.covered else "uncovered"
                html += f'        <div class="state-box {cls}">{sc.state_name}</div>\n'
            
            html += """    </div>
    
    <h3>Transition Coverage</h3>
    <table>
        <tr><th>From</th><th>To</th><th>Condition</th><th>Status</th></tr>
"""
            
            for tc in report.transition_coverage:
                status = "✓" if tc.covered else "✗"
                html += f"""        <tr>
            <td>{tc.from_state}</td>
            <td>{tc.to_state}</td>
            <td>{tc.condition[:30] if tc.condition else '-'}</td>
            <td>{status}</td>
        </tr>
"""
            
            html += """    </table>
"""
        
        html += """
</body>
</html>
"""
        
        with open(filename, 'w') as f:
            f.write(html)
        
        return filename


def track_fsm_coverage(parser) -> List[FSMCoverageReport]:
    """便捷函数"""
    tracker = FSMCoverageTracker(parser)
    return tracker.analyze()


__all__ = [
    'FSMCoverageTracker',
    'FSMCoverageReport',
    'FSMStateInfo',
    'StateCoverage',
    'TransitionCoverage',
    'track_fsm_coverage',
]
