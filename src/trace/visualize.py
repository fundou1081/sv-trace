"""
可视化模块 - 生成流程图 (Graphviz DOT)
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict, Set


@dataclass
class GraphNode:
    id: str
    label: str
    shape: str = "box"  # box, oval, diamond, parallelogram
    style: str = ""    # filled, bold
    color: str = ""     # 用于区分类型
    fillcolor: str = ""


class GraphVisualizer:
    """流程图生成器"""
    
    def __init__(self):
        self.nodes: List[GraphNode] = []
        self.edges: List[tuple] = []  # (from, to, label)
    
    def add_node(self, node: GraphNode):
        self.nodes.append(node)
    
    def add_edge(self, from_id: str, to_id: str, label: str = ""):
        self.edges.append((from_id, to_id, label))
    
    def to_dot(self, name: str = "dataflow") -> str:
        """生成 DOT 格式"""
        lines = [
            f"digraph {name} {{",
            '  rankdir=LR;',
            '  node [fontname="Arial"];',
            '  edge [fontname="Arial"];',
            '',
        ]
        
        # 节点定义
        for node in self.nodes:
            attrs = []
            if node.shape:
                attrs.append(f'shape={node.shape}')
            if node.style:
                attrs.append(f'style={node.style}')
            if node.fillcolor:
                attrs.append(f'fillcolor={node.fillcolor}')
            if node.color:
                attrs.append(f'color={node.color}')
            
            attrs_str = f"[{', '.join(attrs)}]" if attrs else ""
            lines.append(f'  {node.id} [label="{node.label}"{attrs_str}];')
        
        lines.append("")
        
        # 边定义
        for from_id, to_id, label in self.edges:
            if label:
                lines.append(f'  {from_id} -> {to_id} [label="{label}"];')
            else:
                lines.append(f'  {from_id} -> {to_id};')
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def save(self, filepath: str):
        """保存为 .dot 文件"""
        with open(filepath, 'w') as f:
            f.write(self.to_dot())
        print(f"Saved to: {filepath}")
    
    def render_image(self, output_path: str, format: str = "png"):
        """尝试渲染图片（需要 graphviz）"""
        import subprocess
        import tempfile
        
        # 生成临时 dot 文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
            f.write(self.to_dot())
            dot_file = f.name
        
        try:
            result = subprocess.run(
                ['dot', '-T', format, '-o', output_path, dot_file],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"Image saved to: {output_path}")
            else:
                print(f"Graphviz not available: {result.stderr}")
        finally:
            os.unlink(dot_file)


def visualize_datapath(parser, signal: str, output: str = None) -> str:
    """可视化数据流"""
    from .datapath import DataPathAnalyzer
    
    analyzer = DataPathAnalyzer(parser)
    dp = analyzer.analyze(signal)
    
    viz = GraphVisualizer()
    
    # 添加节点
    for sig, node in dp.nodes.items():
        # 根据驱动类型选择颜色
        if not node.exprs:
            # 输入信号
            fillcolor = "#e0e0e0"
            shape = "oval"
        elif "ALWAYS_FF" in node.driver_kinds:
            fillcolor = "#90EE90"  # 浅绿 - 寄存器
            shape = "box"
        elif "ALWAYS_COMB" in node.driver_kinds:
            fillcolor = "#87CEEB"  # 浅蓝 - 组合逻辑
            shape = "box"
        elif "ASSIGN" in node.driver_kinds:
            fillcolor = "#FFB6C1"  # 浅红 - assign
            shape = "parallelogram"
        else:
            fillcolor = "#ffffff"
            shape = "box"
        
        # 简化标签
        expr = node.exprs[0][:30] if node.exprs else "[input]"
        
        viz.add_node(GraphNode(
            id=sig,
            label=f"{sig}\n({expr}...)",
            shape=shape,
            style="filled",
            fillcolor=fillcolor
        ))
    
    # 添加边
    for sig, node in dp.nodes.items():
        for driver in node.drivers:
            viz.add_edge(driver, sig, "")
    
    dot = viz.to_dot(f"datapath_{signal}")
    
    if output:
        viz.save(output)
    
    return dot


def visualize_controlflow(parser, signal: str, output: str = None) -> str:
    """可视化控制流"""
    from .controlflow import ControlFlowTracer
    
    tracer = ControlFlowTracer(parser)
    flow = tracer.find_control_dependencies(signal)
    
    viz = GraphVisualizer()
    
    # 添加目标节点
    viz.add_node(GraphNode(
        id=signal,
        label=signal,
        shape="box",
        style="filled",
        fillcolor="#90EE90"
    ))
    
    # 添加控制信号节点
    for ctrl_sig in flow.controlling_signals:
        viz.add_node(GraphNode(
            id=ctrl_sig,
            label=ctrl_sig,
            shape="diamond",
            style="filled",
            fillcolor="#FFD700"  # 金色
        ))
        viz.add_edge(ctrl_sig, signal, "controls")
    
    # 添加条件节点
    for cond in flow.conditions:
        cond_id = f"cond_{cond.line}"
        viz.add_node(GraphNode(
            id=cond_id,
            label=cond.condition_expr[:30] + "...",
            shape="parallelogram",
            style="filled",
            fillcolor="#87CEEB"
        ))
        # 连接条件到目标
        for ctrl in cond.condition_signals:
            if ctrl in [n.id for n in viz.nodes]:
                viz.add_edge(ctrl, cond_id)
        viz.add_edge(cond_id, signal, cond.statement_type)
    
    dot = viz.to_dot(f"controlflow_{signal}")
    
    if output:
        viz.save(output)
    
    return dot
