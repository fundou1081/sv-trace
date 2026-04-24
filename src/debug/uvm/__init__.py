"""UVM structure analysis module."""

from .uvm_extractor import UVMExtractor
from .uvm_component import UVMComponentInfo, UVMConnectionInfo

__all__ = ['UVMExtractor', 'UVMComponentInfo', 'UVMConnectionInfo']
