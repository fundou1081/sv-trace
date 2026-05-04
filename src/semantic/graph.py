"""
Semantic Graph - 语义图
"""
from dataclasses import dataclass, field
from typing import Dict, Set, List, Optional
from .signal import SignalNode
from .connection import ConnectionEdge, ClockEdge, ResetEdge


@dataclass
class SemanticGraph:
    """语义图 - 纯数据结构，可缓存"""
    
    # 节点索引
    nodes: Dict[str, SignalNode] = field(default_factory=dict)
    
    # 边
    connections: List[ConnectionEdge] = field(default_factory=list)
    clock_edges: List[ClockEdge] = field(default_factory=list)
    reset_edges: List[ResetEdge] = field(default_factory=list)
    
    # 元数据
    top_modules: Set[str] = field(default_factory=set)
    clock_domains: Set[str] = field(default_factory=set)
    
    # 功能标志
    elaborated: bool = False
    
    # 添加信号节点
    def add_signal(self, node: SignalNode) -> None:
        """添加信号节点"""
        self.nodes[node.full_path] = node
    
    # 添加连接
    def add_connection(self, edge: ConnectionEdge) -> None:
        """添加连接边"""
        if edge not in self.connections:
            self.connections.append(edge)
            # 同步更新节点的驱动/加载
            if edge.source in self.nodes:
                src_node = self.nodes[edge.source]
                if edge.sink not in src_node.loads:
                    self.nodes[edge.source] = SignalNode(
                        full_path=src_node.full_path,
                        width=src_node.width,
                        kind=src_node.kind,
                        direction=src_node.direction,
                        clock_domain=src_node.clock_domain,
                        reset_domain=src_node.reset_domain,
                        drivers=src_node.drivers,
                        loads=src_node.loads + (edge.sink,),
                        module_path=src_node.module_path,
                    )
    
    # 获取信号
    def get_signal(self, path: str) -> Optional[SignalNode]:
        return self.nodes.get(path)
    
    # 获取模块所有信号
    def get_module_signals(self, module_path: str) -> List[SignalNode]:
        return [
            n for n in self.nodes.values()
            if n.module_path == module_path
        ]
    
    # 获取驱动关系
    def get_drivers(self, path: str) -> List[str]:
        node = self.nodes.get(path)
        return list(node.drivers) if node else []
    
    # 获取负载
    def get_loads(self, path: str) -> List[str]:
        node = self.nodes.get(path)
        return list(node.loads) if node else []
    
    # 获取时钟域信号
    def get_clock_signals(self) -> List[SignalNode]:
        return [
            n for n in self.nodes.values()
            if n.is_clock
        ]
    
    # 统计
    @property
    def signal_count(self) -> int:
        return len(self.nodes)
    
    @property
    def edge_count(self) -> int:
        return len(self.connections) + len(self.clock_edges)
    
    # JSON 序列化
    def to_dict(self) -> dict:
        return {
            'top_modules': list(self.top_modules),
            'clock_domains': list(self.clock_domains),
            'signal_count': self.signal_count,
            'edge_count': self.edge_count,
            'elaborated': self.elaborated,
        }
    
    def __len__(self):
        return len(self.nodes)
    
    def __repr__(self):
        return f"SemanticGraph(signals={len(self)}, edges={self.edge_count})"


__all__ = ['SemanticGraph']
