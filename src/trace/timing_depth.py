"""
TimingDepthAnalyzer - 时序深度分析器
- 时序深度: 寄存器间的时钟周期数
- 逻辑深度: 路径上的运算符总数
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.models import Register, DomainInfo, TimingPath


class TimingDepthAnalyzer:
    def __init__(self, parser):
        self.parser = parser
        self._init_from_driver()
    
    def _init_from_driver(self):
        """从 DriverCollector 初始化"""
        from .driver import DriverCollector, DriverKind, AssignKind
        
        dc = DriverCollector(self.parser)
        
        # 初始化
        self.registers: dict = {}
        self.domains: dict = {}
        # 数据流图: signal -> [sources that drive this signal]
        # 即 flow_graph[dest] = [src1, src2, ...]
        self.flow_graph: dict = {}
        # 每条边的运算符数量: (src, dest) -> op_count
        self.edge_ops: dict = {}
        
        for signal, drivers in dc.drivers.items():
            for driver in drivers:
                if driver.assign_kind == AssignKind.Nonblocking:
                    # 非阻塞赋值 -> 时序元素
                    if signal not in self.registers:
                        self.registers[signal] = Register(
                            name=signal,
                            module=driver.module,
                            clock=driver.clock or ''
                        )
                        if driver.clock:
                            if driver.clock not in self.domains:
                                self.domains[driver.clock] = DomainInfo(
                                    name=driver.clock,
                                    clock=driver.clock
                                )
                            if signal not in self.domains[driver.clock].registers:
                                self.domains[driver.clock].registers.append(signal)
                    
                    # 建立数据流: signal <- sources
                    # flow_graph[signal] 包含驱动 signal 的所有 source
                    if signal not in self.flow_graph:
                        self.flow_graph[signal] = []
                    for src in driver.sources:
                        if src not in self.flow_graph[signal]:
                            self.flow_graph[signal].append(src)
                        # 记录边的运算符数量
                        self.edge_ops[(src, signal)] = driver.operator_count
                
                else:
                    # 阻塞赋值 -> 组合逻辑
                    if signal not in self.flow_graph:
                        self.flow_graph[signal] = []
                    for src in driver.sources:
                        if src not in self.flow_graph[signal]:
                            self.flow_graph[signal].append(src)
                        self.edge_ops[(src, signal)] = driver.operator_count
    
    def analyze(self, domain: str = "default") -> list:
        """分析时序路径"""
        paths = []
        regs = self.get_registers_by_domain(domain)
        
        for end_reg in regs:
            result = self._trace_upstream(end_reg, set())
            if result and len(result[0]) >= 2:
                signals, logic_depth = result
                # 路径是反的（从 end 到 start），需要反转
                signals = signals[::-1]  # 反转
                
                # 找到路径上的所有寄存器
                reg_positions = [(i, s) for i, s in enumerate(signals) if s in self.registers]
                if len(reg_positions) >= 2:
                    start_idx, start_reg = reg_positions[0]
                    end_idx, end_reg_found = reg_positions[-1]
                    if start_reg != end_reg_found:
                        timing_depth = len(reg_positions) - 1
                        paths.append(TimingPath(
                            start_reg=start_reg,
                            end_reg=end_reg_found,
                            timing_depth=timing_depth,
                            logic_depth=logic_depth,
                            signals=signals,
                            domains=[domain]
                        ))
        return paths
    
    def _trace_upstream(self, signal: str, visited: set) -> tuple:
        """追溯信号源，返回 (路径, 逻辑深度)"""
        if signal in visited:
            return None
        
        visited.add(signal)
        current_path = [signal]
        
        # 向上追溯 - 找 sources
        sources = self.flow_graph.get(signal, [])
        if not sources:
            return (current_path, 0)
        
        best = (current_path, 0)
        for src in sources:
            if src in visited:
                continue
            result = self._trace_upstream(src, visited.copy())
            if result:
                path, logic_depth = result
                # edge 是 (src, signal) = (source, current)
                edge_depth = self.edge_ops.get((src, signal), 0)
                new_depth = logic_depth + edge_depth
                new_path = path + current_path
                if len(new_path) > len(best[0]) or (len(new_path) == len(best[0]) and new_depth > best[1]):
                    best = (new_path, new_depth)
        
        return best
    
    def get_registers_by_domain(self, domain: str) -> list:
        if domain == "default":
            return list(self.registers.keys())
        domain_info = self.domains.get(domain)
        if domain_info:
            return domain_info.registers
        return []
    
    def find_critical_path(self, domain: str = "default"):
        paths = self.analyze(domain)
        if not paths:
            return None
        return max(paths, key=lambda p: p.timing_depth * 100 + p.logic_depth)
    
    def find_worst_logic_path(self, domain: str = "default"):
        paths = self.analyze(domain)
        if not paths:
            return None
        return max(paths, key=lambda p: p.logic_depth)
