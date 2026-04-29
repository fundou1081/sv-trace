"""
数据流分析应用 - 支持多文件和层级追踪
"""
import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from parse import SVParser
from trace import DriverTracer, LoadTracer
from trace.connection import ConnectionTracer
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class SignalSource:
    signal: str
    module: str
    driver_type: str
    expression: str
    file: str = ""


@dataclass
class FlowPath:
    """数据流路径"""
    path: List[str]
    drivers: List[str]


class HierarchicalDataFlowAnalyzer:
    """层级数据流分析器"""
    
    def __init__(self):
        self.parsers: Dict[str, SVParser] = {}
        self.driver_tracers: Dict[str, DriverTracer] = {}
        self.load_tracers: Dict[str, LoadTracer] = {}
        self.connection_tracers: Dict[str, ConnectionTracer] = {}
        self.module_files: Dict[str, str] = {}
        self.module_signals: Dict[str, Dict[str, str]] = {}  # module -> {port_name -> signal}
    
    def load_file(self, filepath: str):
        """加载文件"""
        code = self._read_file(filepath)
        
        parser = SVParser()
        parser.parse_text(code)
        
        # 追踪器
        driver_tracer = DriverTracer(parser)
        load_tracer = LoadTracer(parser)
        connection_tracer = ConnectionTracer(parser)
        
        filename = os.path.basename(filepath)
        self.parsers[filename] = parser
        self.driver_tracers[filename] = driver_tracer
        self.load_tracers[filename] = load_tracer
        self.connection_tracers[filename] = connection_tracer
        
        # 记录模块和端口映射
        for key, tree in parser.trees.items():
            if tree and hasattr(tree, 'root') and tree.root:
                root = tree.root
                if hasattr(root, 'header') and root.header:
                    mod_name = root.header.name.value if root.header.name else ""
                    self.module_files[mod_name] = filename
                    
                    # 记录端口
                    ports = {}
                    if hasattr(root.header, 'ports') and root.header.ports:
                        for port in root.header.ports.ports:
                            port_str = str(port)
                            # input clk -> (clk, input)
                            # output [7:0] data -> (data, output)
                            m = re.search(r'(input|output)\s+(?:\[.*?\]\s*)?(\w+)', port_str)
                            if m:
                                direction, name = m.groups()
                                ports[name] = direction
                    self.module_signals[mod_name] = ports
        
        print(f"Loaded: {filename}")
        print(f"  Modules: {list(self.module_files.keys())}")
    
    def _read_file(self, filepath: str) -> str:
        with open(filepath, 'r') as f:
            return f.read()
    
    def analyze_signal(self, signal_name: str, module_name: str = "top"):
        """分析信号"""
        print(f"\n{'='*60}")
        print(f"分析信号: {signal_name} (模块: {module_name})")
        print(f"{'='*60}")
        
        sources = self._find_sources(signal_name, module_name)
        
        print(f"\n驱动源:")
        for src in sources:
            print(f"  {src.driver_type}: {src.expression}")
        
        return sources
    
    def _find_sources(self, signal_name: str, module_name: str = None) -> List[SignalSource]:
        sources = []
        
        for filename, tracer in self.driver_tracers.items():
            drivers = tracer.find_driver(signal_name, module_name)
            for d in drivers:
                src = SignalSource(
                    signal=signal_name,
                    module=module_name or "top",
                    driver_type=str(d),
                    expression=str(d),
                    file=filename
                )
                sources.append(src)
        
        return sources
    
    def trace_hierarchical(self, signal_name: str, top_module: str = "top", max_depth: int = 10):
        """层级追踪"""
        print(f"\n{'='*60}")
        print(f"层级追踪: {signal_name}")
        print(f"{'='*60}")
        
        current_signal = signal_name
        current_module = top_module
        visited = set()
        
        depth = 0
        while depth < max_depth:
            key = f"{current_module}.{current_signal}"
            if key in visited:
                print(f"{'  '*depth}[{current_module}] {current_signal} (已访问)")
                break
            visited.add(key)
            
            # 找驱动
            sources = self._find_sources(current_signal, current_module)
            
            if not sources:
                print(f"{'  '*depth}[{current_module}] {current_signal} (源头)")
                break
            
            src = sources[0]
            print(f"{'  '*depth}[{current_module}] {current_signal}")
            print(f"{'  '*depth}  <- {src.driver_type}: {src.expression}")
            
            # 检查是否连接到子模块
            next_info = self._find_connection(current_signal, current_module)
            
            if next_info:
                sub_module, sub_port, parent_signal = next_info
                print(f"{'  '*depth}  -> 子模块 {sub_module}.{sub_port} <- {parent_signal}")
                current_module = sub_module
                current_signal = sub_port
            else:
                # 提取表达式中的信号
                deps = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', src.expression)
                # 过滤掉当前信号和数字
                deps = [d for d in deps if d != current_signal and not d.isdigit()]
                
                if deps:
                    current_signal = deps[0]
                    # 检查是否是端口
                    if current_module in self.module_signals:
                        if current_signal not in self.module_signals[current_module]:
                            print(f"{'  '*depth}  (内部信号, 停止)")
                            break
                else:
                    break
            
            depth += 1
    
    def _find_connection(self, signal_name: str, module_name: str) -> Optional[Tuple[str, str, str]]:
        """查找信号是否连接到子模块"""
        for filename, conn_tracer in self.connection_tracers.items():
            for inst_name, inst in conn_tracer.instances.items():
                for conn in inst.connections:
                    if conn.signal == signal_name:
                        # 找到连接
                        return (inst.module_type, inst_name, conn.dest)
        return None


def demo():
    """演示"""
    import tempfile
    import shutil
    
    tmpdir = tempfile.mkdtemp()
    
    # top.sv
    top_code = '''
module top (
    input clk,
    input [7:0] data_in,
    output [7:0] data_out
);
    
    logic [7:0] mid;
    
    sub u_sub (
        .clk(clk),
        .din(data_in),
        .dout(mid)
    );
    
    assign data_out = mid;
endmodule
'''
    
    # sub.sv
    sub_code = '''
module sub (
    input clk,
    input [7:0] din,
    output [7:0] dout
);
    
    logic [7:0] reg_data;
    
    always_ff @(posedge clk) begin
        reg_data <= din;
    end
    
    assign dout = reg_data;
endmodule
'''
    
    top_path = os.path.join(tmpdir, "top.sv")
    sub_path = os.path.join(tmpdir, "sub.sv")
    
    with open(top_path, 'w') as f:
        f.write(top_code)
    with open(sub_path, 'w') as f:
        f.write(sub_code)
    
    # 分析
    analyzer = HierarchicalDataFlowAnalyzer()
    analyzer.load_file(top_path)
    analyzer.load_file(sub_path)
    
    # 分析 data_out
    analyzer.analyze_signal("data_out")
    
    # 层级追踪
    analyzer.trace_hierarchical("data_out", "top")
    
    shutil.rmtree(tmpdir)


if __name__ == "__main__":
    demo()


def analyze_dataflow(source: str):
    """分析数据流"""
    import re
    # 提取 assign 语句
    assigns = re.findall(r'assign\s+(\w+)\s*=\s*([^;]+);', source)
    return {"assigns": [{"signal": a[0], "expr": a[1].strip()[:30]} for a in assigns], "count": len(assigns)}
