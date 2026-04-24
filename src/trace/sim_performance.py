"""
SimulationPerformance - 仿真性能估算器
估算仿真运行时间、吞吐量、时间约束
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import re
import math


@dataclass
class SimulationMetrics:
    """仿真指标"""
    # 时钟参数
    clock_period_ns: float = 0.0
    clock_freq_mhz: float = 0.0
    
    # 仿真器参数
    sim_type: str = "accellera"
    
    # 仿真速度
    sim_speed_cycles_per_sec: float = 0.0  # cycles/sec
    sim_speed_per_mhz: float = 0.0        # cycles/sec/MHz
    
    # 估算时间
    estimated_runtime_sec: float = 0.0
    estimated_runtime_min: float = 0.0
    
    # 时间进度
    total_cycles: int = 0
    total_time_ns: float = 0.0
    
    # 时间效率
    runtime_per_cycle_ns: float = 0.0  # 实际仿真时间/设计周期
    
    # 时序约束
    meets_timing: bool = True
    setup_violation_ns: float = 0.0
    hold_violation_ns: float = 0.0
    
    # 代码复杂度因子
    complexity_factor: float = 1.0
    
    def visualize(self) -> str:
        lines = []
        
        lines.append(f"  ⏱️ Clock: {self.clock_freq_mhz:.1f} MHz ({self.clock_period_ns:.2f} ns)")
        lines.append(f"  🖥️ Simulator: {self.sim_type}")
        
        if self.sim_speed_cycles_per_sec > 0:
            speed = self.sim_speed_cycles_per_sec
            if speed >= 1e6:
                speed_str = f"{speed/1e6:.1f}M"
            elif speed >= 1e3:
                speed_str = f"{speed/1e3:.0f}K"
            else:
                speed_str = f"{speed:.0f}"
            lines.append(f"  🚀 Sim Speed: {speed_str} cycles/sec")
            lines.append(f"     Est. Runtime: {self.estimated_runtime_sec:.2f}s")
            if self.estimated_runtime_min >= 0.01:
                lines.append(f"                ({self.estimated_runtime_min:.1f} min)")
        
        if self.total_cycles > 0:
            lines.append(f"  🔄 Design Cycles: {self.total_cycles:,}")
            lines.append(f"  ⏳ Design Time: {self.total_time_ns:.0f} ns ({self.total_time_ns/1e6:.2f} ms)")
        
        if self.complexity_factor > 1.0:
            lines.append(f"  📊 Complexity: {self.complexity_factor:.1f}x")
        
        return "\n".join(lines)


@dataclass
class SimulationResult:
    """仿真结果"""
    module_name: str
    metrics: SimulationMetrics = field(default_factory=SimulationMetrics)
    
    clock_domains: List[str] = field(default_factory=list)
    combinational_logic: int = 0
    sequential_elements: int = 0
    
    def visualize(self) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append(f"⏱️ SIMULATION PERFORMANCE: {self.module_name}")
        lines.append("=" * 60)
        
        if self.clock_domains:
            lines.append(f"\n🔔 Clock Domains: {', '.join(self.clock_domains)}")
        
        if self.combinational_logic > 0 or self.sequential_elements > 0:
            lines.append(f"\n📐 Complexity:")
            lines.append(f"  Comb: {self.combinational_logic} nodes")
            lines.append(f"  Seq:  {self.sequential_elements} FFs")
        
        lines.append(f"\n{self.metrics.visualize()}")
        lines.append("=" * 60)
        return "\n".join(lines)


class SimulationPerformance:
    """仿真性能估算器"""
    
    # 仿真速度基准 (cycles/sec/MHz)
    # 基于公开基准测试和经验数据
    BENCHMARKS = {
        # 商业仿真器
        'cadence': 800000,
        'synopsys': 750000,
        'mentor': 700000,
        
        # 开源/免费仿真器  
        'accellera': 150000,     # Questa (免费版) / ModelSim
        'iverilog': 50000,       # Icarus Verilog
        'verilator': 2000000,    # Verilator (优化模式)
        'verilator_opt': 5000000,  # Verilator (最高优化)
        
        # 默认
        'default': 100000,
    }
    
    def __init__(self, parser):
        self.parser = parser
    
    def analyze(self, module_name: str = None,
               clock_freq_mhz: float = 100.0,
               sim_type: str = 'accellera',
               total_cycles: int = 1000000,
               design_complexity: int = 100) -> SimulationResult:
        
        if not module_name:
            module_name = self._get_default_module()
        
        result = SimulationResult(module_name=module_name)
        
        # 获取代码复杂度
        result.combinational_logic, result.sequential_elements = \
            self._count_logic(module_name)
        
        # 时钟域
        result.clock_domains = self._extract_clock_domains(module_name)
        
        # 计算指标
        result.metrics = self._calculate_metrics(
            clock_freq_mhz,
            sim_type,
            total_cycles,
            result.combinational_logic + result.sequential_elements
        )
        
        return result
    
    def estimate_runtime(self, module_name: str = None,
                        clock_freq_mhz: float = 100.0,
                        sim_type: str = 'accellera',
                        design_time_us: float = 1000.0) -> SimulationResult:
        """根据设计运行时间估算仿真时间"""
        
        if not module_name:
            module_name = self._get_default_module()
        
        # 设计需要的时间 -> 周期
        total_cycles = int(design_time_us * 1000 / clock_freq_mhz * 1000)
        
        return self.analyze(module_name, clock_freq_mhz, sim_type, total_cycles)
    
    def estimate_cycles_for_duration(self, clock_freq_mhz: float,
                                   design_time_us: float) -> int:
        """估算特定运行时间需要的周期数"""
        return int(design_time_us * 1000 / clock_freq_mhz)
    
    def _get_default_module(self) -> str:
        import pyslang
        for fname, tree in self.parser.trees.items():
            if tree and hasattr(tree, 'root'):
                members = list(tree.root.members)
                for m in members:
                    if m.kind == pyslang.SyntaxKind.ModuleDeclaration:
                        if hasattr(m, 'header') and hasattr(m.header, 'name'):
                            return str(m.header.name).strip()
        return "unknown"
    
    def _extract_clock_domains(self, module_name: str) -> List[str]:
        """提取时钟域"""
        domains = []
        seen = set()
        
        for fname, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            source = ""
            try:
                source = tree.source if hasattr(tree, 'source') else ""
            except:
                pass
            
            if not source:
                try:
                    with open(fname) as f:
                        source = f.read()
                except:
                    continue
            
            in_module = False
            for line in source.split('\n'):
                stripped = line.strip()
                
                if stripped.startswith('module '):
                    in_module = module_name in stripped
                    continue
                elif stripped.startswith('endmodule'):
                    in_module = False
                    continue
                
                if not in_module:
                    continue
                
                # @(posedge clk) or @(negedge clk)
                if '@(posedge' in stripped or '@(negedge' in stripped:
                    match = re.search(r'@\(pos?edge\s+(\w+)', stripped)
                    if match:
                        clk = match.group(1)
                        if clk not in seen:
                            seen.add(clk)
                            domains.append(clk)
                
                # always_ff @(posedge clk
                if 'always_ff' in stripped:
                    # 下一行找时钟
                    pass
        
        return domains if domains else ['clk']
    
    def _count_logic(self, module_name: str) -> tuple:
        """统计逻辑复杂度"""
        comb = 0
        seq = 0
        
        for fname, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            source = ""
            try:
                source = tree.source if hasattr(tree, 'source') else ""
            except:
                pass
            
            if not source:
                try:
                    with open(fname) as f:
                        source = f.read()
                except:
                    continue
            
            in_module = False
            for line in source.split('\n'):
                stripped = line.strip()
                
                if stripped.startswith('module '):
                    in_module = module_name in stripped
                    continue
                elif stripped.startswith('endmodule'):
                    in_module = False
                    continue
                
                if not in_module:
                    continue
                
                # always_ff -> 顺序逻辑
                if 'always_ff' in stripped:
                    seq += 1
                
                # always_comb -> 组合逻辑
                if 'always_comb' in stripped:
                    comb += 1
                
                # always_latch
                if 'always_latch' in stripped:
                    seq += 1
                
                # assign -> 组合逻辑
                if stripped.startswith('assign '):
                    comb += 1
        
        return comb, seq
    
    def _calculate_metrics(self, clock_freq_mhz: float,
                        sim_type: str,
                        total_cycles: int,
                        complexity_nodes: int) -> SimulationMetrics:
        
        m = SimulationMetrics()
        
        m.sim_type = sim_type
        m.clock_freq_mhz = clock_freq_mhz
        m.clock_period_ns = 1000.0 / clock_freq_mhz if clock_freq_mhz > 0 else 10.0
        m.total_cycles = total_cycles
        m.total_time_ns = total_cycles * m.clock_period_ns
        
        # 获取基准速度
        base_speed = self.BENCHMARKS.get(sim_type, self.BENCHMARKS['default'])
        m.sim_speed_per_mhz = base_speed
        
        # 总仿真速度
        m.sim_speed_cycles_per_sec = base_speed * clock_freq_mhz
        
        # 估算运行时间
        if m.sim_speed_cycles_per_sec > 0:
            m.estimated_runtime_sec = total_cycles / m.sim_speed_cycles_per_sec
            m.estimated_runtime_min = m.estimated_runtime_sec / 60.0
        
        # 运行时间/设计周期 的比率
        if total_cycles > 0:
            m.runtime_per_cycle_ns = m.estimated_runtime_sec * 1e9 / total_cycles
        
        # 复杂度因子 (基于逻辑节点数)
        # 更多的 FF ���组���逻辑会降低仿真速度
        if complexity_nodes > 0:
            m.complexity_factor = 1.0 + (complexity_nodes / 1000.0)
            
            # 应用复杂度修正
            m.sim_speed_cycles_per_sec /= m.complexity_factor
            m.estimated_runtime_sec = total_cycles / m.sim_speed_cycles_per_sec
            m.estimated_runtime_min = m.estimated_runtime_sec / 60.0
        
        return m


def analyze_sim_performance(parser, module_name: str = None,
                       clock_freq_mhz: float = 100.0,
                       sim_type: str = 'accellera',
                       total_cycles: int = 1000000) -> SimulationResult:
    """便捷函数"""
    est = SimulationPerformance(parser)
    return est.analyze(module_name, clock_freq_mhz, sim_type, total_cycles)
