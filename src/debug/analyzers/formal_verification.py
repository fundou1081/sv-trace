"""
FormalVerification - 形式验证接口
生成形式验证属性和自动验证脚本
"""
import os
import sys
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


@dataclass
class PropertySpec:
    """属性规范"""
    name: str
    kind: str  # "assert", "assume", "cover"
    category: str  # "safety", "liveness", "assertion"
    description: str
    body: str
    clock: str = "clk"
    reset: str = "rst_n"
    logic: str = ""  # 额外的逻辑描述


@dataclass
class ModuleProperties:
    """模块属性集合"""
    module_name: str
    properties: List[PropertySpec] = field(default_factory=list)


@dataclass
class FormalVerificationReport:
    """形式验证报告"""
    module_properties: List[ModuleProperties] = field(default_factory=list)
    total_properties: int = 0
    safety_properties: int = 0
    liveness_properties: int = 0
    assertions: int = 0


class FormalVerificationGenerator:
    """形式验证属性生成器"""
    
    def __init__(self, parser):
        self.parser = parser
        self._properties: List[PropertySpec] = []
    
    def analyze(self) -> FormalVerificationReport:
        """分析并生成形式验证属性"""
        
        # 1. 分析FSM相关属性
        self._generate_fsm_properties()
        
        # 2. 分析接口协议属性
        self._generate_protocol_properties()
        
        # 3. 分析CDC属性
        self._generate_cdc_properties()
        
        # 4. 分析复位属性
        self._generate_reset_properties()
        
        return self._generate_report()
    
    def _generate_fsm_properties(self):
        """生成FSM相关属性"""
        from .fsm_analyzer import FSMAnalyzer
        
        analyzer = FSMAnalyzer(self.parser)
        report = analyzer.analyze()
        
        # 1. 状态有效属性
        if report.state_names:
            states_str = ', '.join(report.state_names)
            self._properties.append(PropertySpec(
                name="fsm_state_valid",
                kind="assert",
                category="safety",
                description="FSM状态始终有效",
                body=f"state inside {{{states_str}}}",
                logic="检查状态寄存器值始终在合法状态列表中"
            ))
        
        # 2. 无死锁属性
        self._properties.append(PropertySpec(
            name="fsm_no_deadlock",
            kind="assert",
            category="safety",
            description="FSM不会死锁",
            body="not (stable(state) throughout (state != state[*1:$]))",
            logic="如果状态持续不变超过1个周期，则断言失败"
        ))
        
        # 3. 最终到达目标状态属性
        if any('IDLE' in s or 'DONE' in s for s in report.state_names):
            self._properties.append(PropertySpec(
                name="fsm_progress",
                kind="assert",
                category="liveness",
                description="FSM最终会到达完成状态",
                body="eventually (state == IDLE or state == DONE)",
                logic="每个复位周期内，状态机最终应该到达结束状态"
            ))
        
        # 4. 跳转覆盖属性
        for trans in report.transitions[:5]:
            self._properties.append(PropertySpec(
                name=f"trans_{trans.from_state}_to_{trans.to_state}",
                kind="cover",
                category="assertion",
                description=f"覆盖 {trans.from_state} -> {trans.to_state}",
                body=f"(state == {trans.from_state} ##1 state == {trans.to_state})",
                logic="验证这条跳转路径被覆盖"
            ))
    
    def _generate_protocol_properties(self):
        """生成接口协议属性"""
        # AXI-like 协议检查
        self._properties.append(PropertySpec(
            name="axi_valid_implies_ready",
            kind="assume",
            category="safety",
            description="valid为高时，ready不应死锁",
            body="valid && !ready |-> ready[*1:$]",
            logic="如果valid为高，最终ready必须为高（无死锁）"
        ))
        
        # 握手指谈
        self._properties.append(PropertySpec(
            name="handshake_complete",
            kind="assert",
            category="safety",
            description="握手指谈必须完成",
            body="req |-> strong(##[1:$] ack)",
            logic="req信号最终必须被ack响应"
        ))
        
        # 数据有效
        self._properties.append(PropertySpec(
            name="data_valid_once",
            kind="assert",
            category="safety",
            description="数据有效后至少保持一拍",
            body="data_valid |-> data_valid[*1:$]",
            logic="数据有效信号一旦拉高，不应立即拉低"
        ))
    
    def _generate_cdc_properties(self):
        """生成CDC相关属性"""
        # 同步器属性
        self._properties.append(PropertySpec(
            name="cdc_synchronizer",
            kind="assert",
            category="safety",
            description="CDC同步器输出稳定",
            body="not (sync_sig && !sync_sig[*2])",
            logic="同步后的信号不应出现glitch"
        ))
        
        # 跨时钟域边界
        self._properties.append(PropertySpec(
            name="cdc_boundary_stable",
            kind="assert",
            category="safety",
            description="CDC边界信号稳定",
            body="cross_domain_sig |-> cross_domain_sig[*2:$]",
            logic="跨时钟域采样的信号应该稳定"
        ))
        
        # Gray码属性
        self._properties.append(PropertySpec(
            name="gray_code_stable",
            kind="assert",
            category="safety",
            description="Gray码相邻状态只变化一位",
            body="$countones(gray_reg ^ $past(gray_reg)) <= 1",
            logic="Gray编码每次只变化1位"
        ))
    
    def _generate_reset_properties(self):
        """生成复位相关属性"""
        # 复位后状态正确
        self._properties.append(PropertySpec(
            name="reset_state_correct",
            kind="assert",
            category="safety",
            description="复位释放后进入初始状态",
            body="!rst_n |=> state == IDLE",
            logic="复位后下一个周期状态应该是IDLE"
        ))
        
        # 复位期间输出稳定
        self._properties.append(PropertySpec(
            name="reset_output_stable",
            kind="assert",
            category="safety",
            description="复位期间输出保持复位值",
            body="!rst_n |-> $stable(output)",
            logic="复位期间输出不应该变化"
        ))
        
        # 复位释放顺序
        self._properties.append(PropertySpec(
            name="reset_release_order",
            kind="assume",
            category="safety",
            description="多个复位按正确顺序释放",
            body="!rst_n || !rst2_n |-> ##1 !rst_n && !rst2_n",
            logic="如果有多级复位，它们应该同时释放"
        ))
    
    def _generate_report(self) -> FormalVerificationReport:
        """生成报告"""
        report = FormalVerificationReport()
        
        props = ModuleProperties(module_name="top")
        props.properties = self._properties
        
        report.module_properties.append(props)
        report.total_properties = len(self._properties)
        report.assertions = sum(1 for p in self._properties if p.kind == "assert")
        
        for p in self._properties:
            if p.category == "safety":
                report.safety_properties += 1
            elif p.category == "liveness":
                report.liveness_properties += 1
        
        return report
    
    def export_to_sby(self, filename: str):
        """导出为Symbiyosys脚本"""
        content = f"""[options]
mode bmc
depth 100
append <

[engines]
smtbmc

"""
        
        # 生成property块
        content += "[properties]\n"
        for prop in self._properties:
            if prop.kind == "assert":
                content += f"  {prop.name}\n"
        
        content += "\n[sources]\n"
        content += "  // Add your design sources here\n\n"
        
        with open(filename, 'w') as f:
            f.write(content)
        
        return filename
    
    def export_to_sv_property(self, filename: str):
        """导出为SystemVerilog Property格式"""
        content = f"""// Formal Properties - Auto-generated by SV-Trace
// Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

module formal_properties (
    input clk,
    input rst_n
);

"""
        
        for prop in self._properties:
            content += f"""
// {prop.description}
property {prop.name};
    @{prop.clock} {prop.body};
endproperty

{'_' * 60}
"""
        
        content += "\nendmodule\n"
        
        with open(filename, 'w') as f:
            f.write(content)
        
        return filename
    
    def export_to_psl(self, filename: str):
        """导出为PSL格式"""
        content = f"""-- PSL Properties - Auto-generated by SV-Trace
-- Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
        
        for prop in self._properties:
            content += f"""-- {prop.description}
-- {prop.kind}: {prop.name}
vunit {prop.name}_vunit ({prop.name}) {{
    default clock = rising_edge(clk);
    {prop.kind} {prop.body};
}}
"""
        
        with open(filename, 'w') as f:
            f.write(content)
        
        return filename
    
    def export_to_property_list(self, filename: str):
        """导出为属性清单(CSV)"""
        import csv
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Name', 'Kind', 'Category', 'Description', 'Body', 'Clock', 'Reset'])
            
            for prop in self._properties:
                writer.writerow([
                    prop.name,
                    prop.kind,
                    prop.category,
                    prop.description,
                    prop.body,
                    prop.clock,
                    prop.reset
                ])
        
        return filename
    
    def generate_formal_testplan(self, filename: str):
        """生成形式验证测试计划"""
        content = f"""# Formal Verification Test Plan
Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

| Metric | Count |
|--------|-------|
| Total Properties | {len(self._properties)} |
| Safety Properties | {self._properties.count(lambda p: p.category == 'safety')} |
| Liveness Properties | {self._properties.count(lambda p: p.category == 'liveness')} |
| Assertions | {self._properties.count(lambda p: p.kind == 'assert')} |

## Properties

"""
        
        for prop in self._properties:
            content += f"""
### {prop.name}

- **Kind**: {prop.kind}
- **Category**: {prop.category}
- **Description**: {prop.description}
- **Body**: `{prop.body}`
- **Logic**: {prop.logic}

"""
        
        with open(filename, 'w') as f:
            f.write(content)
        
        return filename
    
    def print_report(self, report: FormalVerificationReport):
        """打印报告"""
        print("\n" + "="*60)
        print("Formal Verification Report")
        print("="*60)
        
        print(f"\n[Summary]")
        print(f"  Total Properties: {report.total_properties}")
        print(f"  Safety: {report.safety_properties}")
        print(f"  Liveness: {report.liveness_properties}")
        print(f"  Assertions: {report.assertions}")
        
        print(f"\n[Properties]")
        for prop in self._properties[:10]:
            print(f"  [{prop.kind}] {prop.name} ({prop.category})")
        
        print("\n" + "="*60)


def generate_formal_properties(parser) -> FormalVerificationReport:
    """便捷函数"""
    generator = FormalVerificationGenerator(parser)
    return generator.analyze()


__all__ = [
    'FormalVerificationGenerator',
    'FormalVerificationReport',
    'PropertySpec',
    'ModuleProperties',
    'generate_formal_properties',
]
