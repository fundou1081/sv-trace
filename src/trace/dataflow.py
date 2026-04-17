"""
Data Flow Tracer - 数据流分析
"""
from typing import List, Dict, Set, Optional
from ..core.models import Signal, Driver, Load, Connection


class DataFlowTracer:
    """数据流分析器"""
    
    def __init__(self, parser):
        self.parser = parser
        self.driver_tracer = None  # 后续注入
        self.load_tracer = None
    
    def find_data_flow(self, signal_name: str, 
                   depth: int = 10) -> Dict[str, Any]:
        """查找信号的数据流"""
        result = {
            "signal": signal_name,
            "drivers": [],
            "loads": [],
            "paths": [],
            "depth": depth,
        }
        
        # 收集驱动
        if self.driver_tracer:
            result["drivers"] = self.driver_tracer.find_driver(signal_name)
        
        # 收集加载
        if self.load_tracer:
            result["loads"] = self.load_tracer.find_load(signal_name)
        
        # 构建路径（简化版）
        if result["drivers"] and result["loads"]:
            for d in result["drivers"]:
                for l in result["loads"]:
                    result["paths"].append({
                        "src": f"{d.file}:{d.line}",
                        "dst": f"{l.file}:{l.line}",
                    })
        
        return result
    
    def find_path(self, src_signal: str, dst_signal: str,
                max_depth: int = 10) -> List[str]:
        """查找从源信号到目标信号的路径"""
        path = []
        visited = set()
        
        self._dfs_find_path(src_signal, dst_signal, path, visited, max_depth)
        
        return path
    
    def _dfs_find_path(self, current: str, target: str,
                     path: List[str], visited: Set[str],
                     max_depth: int):
        """DFS 查找路径"""
        if len(path) > max_depth:
            return
        
        if current == target:
            path.append(current)
            return
        
        visited.add(current)
        path.append(current)
        
        # 查找 current 信号的驱动
        if self.driver_tracer:
            drivers = self.driver_tracer.find_driver(current)
            for d in drivers:
                # 简化：假设驱动表达式中包含其他信号
                # 实际需要解析表达式
                pass
        
        # 继续查找
        if path:
            path.pop()
        
        visited.remove(current)
