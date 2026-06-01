"""signal_tracer_app - 应用层：组合 tracer 和 port_resolver 实现跨模块追踪

Architecture:
- tracer.py: 模块内信号追踪 (使用语义 AST)
- port_resolver.py: 端口连接解析 (使用语法树)
- signal_tracer_app.py: 应用层，组合两者实现完整跨模块追踪
"""

from typing import Dict, List, Optional
from dataclasses import dataclass

from signal_tracer.models import TraceResult, TraceSummary, DriverTrace, LoadTrace
from signal_tracer.port_resolver import PortResolver, PortConnection


@dataclass
class CrossModuleResult:
    """跨模块追踪结果"""
    signal_name: str
    hierarchical_path: str = ""
    is_port: bool = False
    port_direction: str = ""
    # 跨模块追踪新增的上下文
    port_connection: Optional[PortConnection] = None  # 连接的端口信息


class SignalTracerApp:
    """信号追踪应用层 - 组合 tracer 和 port_resolver
    
    给定信号，返回：
    1. 模块内驱动/负载 (tracer.py)
    2. 跨模块驱动/负载 (通过 port_resolver.py 追踪端口连接)
    """
    
    def __init__(self, sv_code: str, file_path: str = ""):
        self._sv_code = sv_code
        self._file_path = file_path
        
        # Lazy initialization
        self._tracer = None
        self._port_resolver = None
        self._built = False
    
    def build(self):
        """构建索引"""
        if self._built:
            return self
        
        # Import here to avoid circular dependency issues
        from signal_tracer.tracer import SignalTracer
        
        # Build tracer (模块内追踪)
        self._tracer = SignalTracer(self._sv_code, self._file_path)
        self._tracer.build()
        
        # Build port resolver (端口连接解析)
        self._port_resolver = PortResolver(self._sv_code)
        self._port_resolver.build()
        
        self._built = True
        return self
    
    def trace(self, signal_name: str) -> TraceSummary:
        """追踪信号的所有驱动和负载 (支持跨模块追踪)"""
        if not self._built:
            self.build()
        
        # 1. 模块内追踪
        result = self._tracer.trace(signal_name)
        
        # 2. 跨模块端口追踪 - 查找外部信号通过端口连接到内部信号的情况
        cross_drivers = self._cross_module_drivers(signal_name)
        result.drivers.extend(cross_drivers)
        
        # 3. 跨模块端口追踪 - 查找内部信号通过端口连接到外部信号的情况
        cross_loads = self._cross_module_loads(signal_name)
        result.loads.extend(cross_loads)
        
        return result
    
    def _cross_module_drivers(self, signal_name: str) -> List[DriverTrace]:
        """通过端口连接查找信号的外部驱动
        
        例如: sig_in (top) -> u_dut.data_in (端口) -> u_dut.data_out (内部驱动)
        追踪 sig_in 时，需要找到 u_dut.data_out 作为其驱动
        
        Args:
            signal_name: 要追踪的信号名
            
        Returns:
            跨模块驱动列表
        """
        if not self._port_resolver:
            return []
        
        result = []
        
        # 1. 查找所有端口连接 where signal_name is connected
        #    e.g., sig_in -> u_dut.data_in
        port_conns = self._port_resolver.get_signal_connections(signal_name)
        
        for conn in port_conns:
            # conn = PortConnection(instance='u_dut', port='data_in', connected='sig_in')
            # data_in is an input port of dut, so sig_in drives data_in
            # Find what drives data_in inside the dut module
            internal_drivers = self._find_drivers_inside_instance(
                conn.instance_path, conn.port_name
            )
            
            for drv in internal_drivers:
                # Convert to DriverTrace
                trace = DriverTrace(
                    signal_name=drv.signal_name,
                    trace_type=drv.trace_type,
                    hierarchical_path=drv.hierarchical_path,
                    line_number=drv.line_number,
                    source_snippet=drv.source_snippet,
                    scope_name=drv.scope_name,
                    is_port=drv.is_port,
                    port_direction=drv.port_direction,
                )
                result.append(trace)
        
        return result
    
    def _cross_module_loads(self, signal_name: str) -> List[LoadTrace]:
        """通过端口连接查找信号的外部负载
        
        例如: sig_out (top) -> u_dut.data_out (端口)
        如果 sig_out 连接到 data_out，而 data_out 是输出端口
        那么 sig_out 是 data_out 的负载
        
        Args:
            signal_name: 要追踪的信号名
            
        Returns:
            跨模块负载列表
        """
        if not self._port_resolver:
            return []
        
        result = []
        
        # 查找所有实例
        for inst in self._port_resolver.instances:
            # 检查 instance 的每个端口连接
            for conn in inst.connections:
                if conn.connected_signal == signal_name:
                    # signal_name 连接到 inst.port_name
                    # 如果 port_name 是输出端口，那么 signal_name 是其负载
                    
                    # 检查端口方向
                    port_dir = self._get_port_direction(inst.instance_path, conn.port_name)
                    if port_dir == 'out':
                        # 这是输出端口连接，signal 是其负载
                        internal_loads = self._find_loads_inside_instance(
                            inst.instance_path, conn.port_name
                        )
                        
                        for load in internal_loads:
                            trace = LoadTrace(
                                signal_name=load.signal_name,
                                trace_type=load.trace_type,
                                hierarchical_path=load.hierarchical_path,
                                line_number=load.line_number,
                                source_snippet=load.source_snippet,
                                scope_name=load.scope_name,
                                is_port=load.is_port,
                                port_direction=load.port_direction,
                            )
                            result.append(trace)
        
        return result
    
    def _find_drivers_inside_instance(self, instance_path: str, signal_name: str) -> List[TraceResult]:
        """在实例内部查找信号的驱动
        
        Args:
            instance_path: 实例路径 (如 'top.u_dut')
            signal_name: 信号名 (在实例内部)
            
        Returns:
            实例内部该信号的驱动列表
        """
        if not self._tracer:
            return []
        
        # 在 tracer 的 _drivers 中查找
        # 注意：tracer 的 signal key 可能包含 hierarchical_path
        drivers = self._tracer._drivers.get(signal_name, [])
        
        # 也检查带路径的版本
        if instance_path:
            full_path = f"{instance_path}.{signal_name}"
            drivers.extend(self._tracer._drivers.get(full_path, []))
        
        return drivers
    
    def _find_loads_inside_instance(self, instance_path: str, signal_name: str) -> List[TraceResult]:
        """在实例内部查找信号的负载
        
        Args:
            instance_path: 实例路径
            signal_name: 信号名 (在实例内部)
            
        Returns:
            实例内部该信号的负载列表
        """
        if not self._tracer:
            return []
        
        loads = self._tracer._loads.get(signal_name, [])
        
        # 也检查带路径的版本
        if instance_path:
            full_path = f"{instance_path}.{signal_name}"
            loads.extend(self._tracer._loads.get(full_path, []))
        
        return loads
    
    def _get_port_direction(self, instance_path: str, port_name: str) -> str:
        """获取端口方向"""
        if not self._tracer:
            return ""
        
        full_path = f"{instance_path}.{port_name}"
        return self._tracer._port_info.get(full_path, "")
    
    def trace_drivers(self, signal_name: str) -> List[DriverTrace]:
        """只追踪驱动"""
        result = self.trace(signal_name)
        return result.drivers
    
    def trace_loads(self, signal_name: str) -> List[LoadTrace]:
        """只追踪负载"""
        result = self.trace(signal_name)
        return result.loads


def trace_signal(signal_name: str, sv_code: str, file_path: str = "") -> TraceSummary:
    """追踪信号 (便捷函数) - 支持跨模块"""
    tracer = SignalTracerApp(sv_code, file_path)
    return tracer.trace(signal_name)


def trace_signal_from_file(signal_name: str, file_path: str) -> TraceSummary:
    """从文件追踪信号 (便捷函数) - 支持跨模块"""
    tracer = SignalTracerApp("", file_path)
    with open(file_path) as f:
        sv_code = f.read()
    return trace_signal(signal_name, sv_code, file_path)


# 保持向后兼容
from signal_tracer.tracer import SignalTracer, SignalTracerFromFile, trace_signal as tracer_trace_signal

__all__ = [
    'SignalTracerApp',
    'trace_signal',
    'trace_signal_from_file',
    'SignalTracer',  # 向后兼容
    'SignalTracerFromFile',  # 向后兼容
    'tracer_trace_signal',  # 原有的单独 tracer
]