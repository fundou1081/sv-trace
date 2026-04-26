"""
CoverageModel - 覆盖模型生成器
基于RTL分析自动生成覆盖点和功能覆盖模型
"""
import os
from typing import List, Dict, Set
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from parse import SVParser
from trace.driver import DriverCollector

@dataclass
class CoverageItem:
    """覆盖项"""
    name: str
    type: str  # state/transition/condition/toggle
    kind: str  # FSM/constraint/interface/error
    description: str = ""
    binned_values: List = field(default_factory=list)

@dataclass
class CoverGroup:
    """覆盖组"""
    name: str
    items: List[CoverageItem] = field(default_factory=list)
    module: str = ""
    description: str = ""

class CoverageModelGenerator:
    """覆盖模型生成器"""
    
    def __init__(self, parser: SVParser = None):
        self.parser = parser
        self.dc = DriverCollector(parser) if parser else None
    
    def generate_fsm_coverage(self, parser: SVParser = None) -> CoverGroup:
        """生成FSM覆盖"""
        if parser is None:
            parser = self.parser
        
        items = []
        
        # 解析状态机
        for fname, tree in parser.trees.items():
            if not tree or not tree.root:
                continue
            
            # 简单识别状态变量
            for sig, drivers in (self.dc.drivers.items() if self.dc else {}):
                sig_lower = sig.lower()
                if any(k in sig_lower for k in ['state', 'mode', 'fsm']):
                    items.append(CoverageItem(
                        name=f"state_{sig}",
                        type="state",
                        kind="FSM",
                        description=f"FSM state coverage for {sig}",
                        binned_values=[f"state_{i}" for i in range(16)]  # 假设最多16状态
                    ))
                    
                    items.append(CoverageItem(
                        name=f"transition_{sig}",
                        type="transition",
                        kind="FSM",
                        description=f"FSM transition coverage for {sig}"
                    ))
        
        return CoverGroup(
            name="fsm_coverage",
            items=items,
            description="FSM状态和转移覆盖"
        )
    
    def generate_constraint_coverage(self, parser: SVParser = None) -> CoverGroup:
        """生成约束覆盖"""
        if parser is None:
            parser = self.parser
        
        items = []
        
        # 分析约束条件
        for fname, tree in parser.trees.items():
            if not tree or not tree.root:
                continue
            
            content = ""
            if hasattr(tree, 'source') and tree.source:
                content = tree.source
            elif hasattr(tree, 'text'):
                content = tree.text
            
            # 识别条件表达式
            import re
            conditions = re.findall(r'if\s*\(([^)]+)\)', content)
            
            for i, cond in enumerate(conditions[:20]):  # 限制数量
                items.append(CoverageItem(
                    name=f"condition_{i}",
                    type="condition",
                    kind="constraint",
                    description=f"Constraint condition: {cond[:50]}",
                    binned_values=["true", "false"]
                ))
        
        return CoverGroup(
            name="constraint_coverage",
            items=items,
            description="约束条件覆盖"
        )
    
    def generate_interface_coverage(self, parser: SVParser = None) -> CoverGroup:
        """生成接口覆盖"""
        if parser is None:
            parser = self.parser
        
        items = []
        
        # 分析端口
        for fname, tree in parser.trees.items():
            if not tree or not tree.root:
                continue
            
            # 获取端口信息
            for sig, drivers in (self.dc.drivers.items() if self.dc else {}):
                if drivers and hasattr(drivers[0], 'port_direction'):
                    direction = str(drivers[0].port_direction).lower()
                    
                    items.append(CoverageItem(
                        name=f"toggle_{sig}",
                        type="toggle",
                        kind="interface",
                        description=f"Signal toggle coverage: {sig} ({direction})",
                        binned_values=["0->1", "1->0", "no_toggle"]
                    ))
        
        return CoverGroup(
            name="interface_coverage",
            items=items,
            description="接口信号toggle覆盖"
        )
    
    def generate_error_coverage(self, parser: SVParser = None) -> CoverGroup:
        """生成错误场景覆盖"""
        if parser is None:
            parser = self.parser
        
        items = []
        
        # 常见错误场景
        error_scenarios = [
            ("fifo_full", "FIFO满时继续写入"),
            ("fifo_empty", "FIFO空时继续读出"),
            ("overflow", "数据溢出"),
            ("underflow", "数据下溢"),
            ("parity_err", "校验错误"),
            ("framing_err", "帧错误"),
            ("break_err", "Break条件"),
            ("timeout", "超时"),
            ("reset_during_transfer", "传输中复位")
        ]
        
        for name, desc in error_scenarios:
            items.append(CoverageItem(
                name=f"error_{name}",
                type="state",
                kind="error",
                description=desc,
                binned_values=["triggered", "not_triggered"]
            ))
        
        return CoverGroup(
            name="error_coverage",
            items=items,
            description="错误场景覆盖"
        )
    
    def generate_cross_coverage(self) -> List[Dict]:
        """生成交叉覆盖"""
        crosses = [
            {
                "name": "uart_baud_data",
                "coverpoints": ["baud_rate", "data_bits"],
                "description": "波特率与数据位组合"
            },
            {
                "name": "fifo_status_operation",
                "coverpoints": ["fifo_level", "operation"],
                "description": "FIFO状态与操作组合"
            }
        ]
        return crosses
    
    def generate_covergroup_code(self, groups: List[CoverGroup]) -> str:
        """生成SystemVerilog Covergroup代码"""
        lines = []
        lines.append("// 自动生成的覆盖模型")
        lines.append("// 生成时间: 2026-04-27")
        lines.append("")
        
        for group in groups:
            lines.append(f"// Covergroup: {group.name}")
            lines.append(f"// 描述: {group.description}")
            lines.append("")
            lines.append(f"covergroup {group.name} @ (posedge clk or negedge rst_n);")
            lines.append("")
            
            for item in group.items:
                lines.append(f"    // {item.description}")
                lines.append(f"    {item.name}: coverpoint {self._get_cov_expr(item)}")
                lines.append(f"        {{ // type: {item.type}, kind: {item.kind}}")
                
                if item.binned_values:
                    bins = [f"bins {v} = {{{v}}}" for v in item.binned_values[:10]]
                    lines.append(f"        {{ {', '.join(bins)} }}")
                
                lines.append("    ;")
                lines.append("")
            
            # 交叉覆盖
            crosses = self.generate_cross_coverage()
            for cross in crosses:
                if group.name in cross["name"]:
                    lines.append(f"    {cross['name']}: cross {', '.join(cross['coverpoints'])};")
            
            lines.append("endgroup : " + group.name)
            lines.append("")
            lines.append(f"{group.name} {group.name}_inst = new();")
            lines.append("")
            lines.append("//" * 60)
            lines.append("")
        
        return '\n'.join(lines)
    
    def _get_cov_expr(self, item: CoverageItem) -> str:
        """获取覆盖表达式"""
        if item.kind == "FSM":
            return f"{item.name.replace('state_', '').replace('transition_', '')}"
        elif item.kind == "interface":
            return item.name.replace("toggle_", "")
        else:
            return item.name
    
    def generate_report(self, groups: List[CoverGroup]) -> str:
        """生成覆盖模型报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("覆盖模型生成报告")
        lines.append("=" * 60)
        lines.append("")
        
        total_items = sum(len(g.items) for g in groups)
        lines.append(f"总覆盖组: {len(groups)}")
        lines.append(f"总覆盖点: {total_items}")
        lines.append("")
        
        for group in groups:
            lines.append(f"\n## {group.name}")
            lines.append(f"描述: {group.description}")
            lines.append(f"覆盖点: {len(group.items)}")
            
            by_type = {}
            for item in group.items:
                by_type.setdefault(item.type, []).append(item.name)
            
            lines.append("按类型:")
            for t, items in by_type.items():
                lines.append(f"  {t}: {len(items)}")
        
        lines.append("")
        lines.append("=" * 60)
        
        return '\n'.join(lines)
