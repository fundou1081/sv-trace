"""
Elaboration - 详细设计数据模型
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal


@dataclass(frozen=True)
class ElabSignal:
    """详细信号 - 全路径 + 已解析位宽"""
    full_path: str                    # "top.mod_a.clk[7:0]"
    width: int                         # 位宽 (参数展开后)
    direction: str                    # Input/Output/Inout/Internal
    clock_domain: Optional[str] = None # 关联时钟
    
    # 驱动关系 (路径字符串)
    drivers: frozenset = frozenset()
    loads: frozenset = frozenset()
    
    def __hash__(self):
        return hash(self.full_path)
    
    def __eq__(self, other):
        return self.full_path == getattr(other, 'full_path', '')
    
    @property
    def name(self) -> str:
        return self.full_path.split('.')[-1].split('[')[0]


@dataclass
class ElabInstance:
    """实例信息"""
    instance_path: str               # "top.u_sub"
    module_name: str                 # "sub_module"
    parameters: Dict[str, str] = field(default_factory=dict)
    ports: Dict[str, str] = field(default_factory=dict)  # port_name -> signal_path


@dataclass
class ElabDesign:
    """完整设计 - 纯数据结构"""
    top_modules: List[str] = field(default_factory=list)
    signals: Dict[str, ElabSignal] = field(default_factory=dict)  # path -> ElabSignal
    instances: Dict[str, ElabInstance] = field(default_factory=dict)  # path -> Instance
    
    # 模块级别信息
    clock_domains: set = field(default_factory=set)
    reset_domains: set = field(default_factory=set)
    
    def add_signal(self, signal: ElabSignal) -> None:
        self.signals[signal.full_path] = signal
    
    def get_signal(self, path: str) -> Optional[ElabSignal]:
        return self.signals.get(path)
    
    def get_module_signals(self, module_path: str) -> List[ElabSignal]:
        prefix = f"{module_path}."
        return [
            s for s in self.signals.values()
            if s.full_path.startswith(prefix)
        ]
    
    def get_clock_signals(self) -> List[ElabSignal]:
        return [s for s in self.signals.values() if 'clk' in s.full_path.lower()]
    
    def get_reset_signals(self) -> List[ElabSignal]:
        return [s for s in self.signals.values() if 'rst' in s.full_path.lower()]
    
    def get_driven_signals(self, driver_path: str) -> List[ElabSignal]:
        sig = self.signals.get(driver_path)
        if not sig:
            return []
        return [self.signals[p] for p in sig.loads if p in self.signals]
    
    def get_driving_signals(self, load_path: str) -> List[ElabSignal]:
        sig = self.signals.get(load_path)
        if not sig:
            return []
        return [self.signals[p] for p in sig.drivers if p in self.signals]
    
    def count(self) -> dict:
        return {
            'signals': len(self.signals),
            'instances': len(self.instances),
            'clock_domains': len(self.clock_domains),
            'reset_domains': len(self.reset_domains),
        }
    
    def __len__(self):
        return len(self.signals)


__all__ = ['ElabSignal', 'ElabInstance', 'ElabDesign']
