"""
Simulator - 仿真器抽象层
统一接口，支持多种仿真器 (VCS/Verilator/ModelSim)
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class SimConfig:
    """仿真配置"""
    top: str = "tb_top"
    extra_args: List[str] = None
    
    def __post_init__(self):
        if self.extra_args is None:
            self.extra_args = []

class Simulator(ABC):
    """仿真器基类"""
    
    @abstractmethod
    def compile(self, rtl_files: List[str], out_dir: str = "./sim_build") -> bool:
        """编译RTL"""
        pass
    
    @abstractmethod
    def run(self, config: SimConfig) -> Dict:
        """运行仿真"""
        pass
    
    @abstractmethod
    def get_coverage(self) -> Dict:
        """获取覆盖率"""
        pass

class VCSSimulator(Simulator):
    """VCS仿真器"""
    
    def compile(self, rtl_files: List[str], out_dir: str = "./sim_build") -> bool:
        cmd = f"vcs -o {out_dir}/simv " + " ".join(rtl_files)
        # TODO: 实现完整编译命令
        return True
    
    def run(self, config: SimConfig) -> Dict:
        # TODO: 实现运行
        return {'status': 'ok'}
    
    def get_coverage(self) -> Dict:
        # TODO: 实现覆盖率提取
        return {'line': 0, 'branch': 0, 'fsm': 0}

class VerilatorSimulator(Simulator):
    """Verilator仿真器"""
    
    def compile(self, rtl_files: List[str], out_dir: str = "./sim_build") -> bool:
        cmd = f"verilator --cc " + " ".join(rtl_files)
        # TODO: 实现
        return True
    
    def run(self, config: SimConfig) -> Dict:
        return {'status': 'ok'}
    
    def get_coverage(self) -> Dict:
        return {'line': 0, 'branch': 0}

class SimulatorFactory:
    """仿真器工厂"""
    
    _simulators = {
        'vcs': VCSSimulator,
        'verilator': VerilatorSimulator,
    }
    
    @classmethod
    def create(cls, name: str) -> Simulator:
        if name not in cls._simulators:
            raise ValueError(f"Unknown simulator: {name}")
        return cls._simulators[name]()
    
    @classmethod
    def list_supported(cls) -> List[str]:
        return list(cls._simulators.keys())
