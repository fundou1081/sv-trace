"""
semantic_ast.graph - 语义关系图

用于高效查询语义关系的图结构。
"""

from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field

from semantic_ast.nodes import (
    SemanticAST,
    SemanticScopeNode,
    SemanticSignalNode,
    SemanticDriverRef,
    SemanticLoadRef,
    SemanticNodeKind,
    ConfidenceLevel,
)


class SemanticRelationGraph:
    """语义关系图
    
    提供高效查询接口，基于 SemanticAST 构建。
    支持:
    - 按信号名查找驱动/负载关系
    - 查找多驱动信号
    - 查找跨模块引用
    - 查找时钟域
    """
    
    def __init__(self, sem_ast: SemanticAST):
        self.sem_ast = sem_ast
        self._build_indexes()
    
    def _build_indexes(self):
        """构建辅助索引，加快查询速度"""
        # 信号名 → 信号节点的映射
        self._signal_index: Dict[str, List[SemanticSignalNode]] = {}
        
        # 实例名 → 实例作用域的映射
        self._instance_index: Dict[str, SemanticScopeNode] = {}
        
        # 时钟信号 → 被它驱动的信号列表
        self._clock_domain_index: Dict[str, List[str]] = {}
        
        for scope in self.sem_ast.scopes.values():
            # 索引信号
            for sig in scope.signals.values():
                # 按短名索引
                if sig.name not in self._signal_index:
                    self._signal_index[sig.name] = []
                self._signal_index[sig.name].append(sig)
                
                # 按完全限定名索引
                full_name = f"{scope.hierarchy_path}.{sig.name}" if scope.hierarchy_path else sig.name
                if full_name not in self._signal_index:
                    self._signal_index[full_name] = []
                self._signal_index[full_name].append(sig)
            
            # 索引实例
            if scope.instance_name:
                self._instance_index[scope.instance_name] = scope
        
        # 构建时钟域索引
        for sig in self.sem_ast.all_signals:
            for drv in sig.drivers:
                if drv.clock:
                    if drv.clock not in self._clock_domain_index:
                        self._clock_domain_index[drv.clock] = []
                    self._clock_domain_index[drv.clock].append(sig.name)
    
    def find_signal(self, name: str, scope_id: str = None) -> Optional[SemanticSignalNode]:
        """查找信号"""
        if scope_id:
            scope = self.sem_ast.get_scope(scope_id)
            if scope:
                return scope.signals.get(name)
        
        # 全局查找
        matches = self._signal_index.get(name, [])
        return matches[0] if matches else None
    
    def find_signals_like(self, pattern: str) -> List[SemanticSignalNode]:
        """按模式查找信号 (简单实现)"""
        import fnmatch
        results = []
        for sig_list in self._signal_index.values():
            for sig in sig_list:
                if fnmatch.fnmatch(sig.name, pattern):
                    if sig not in results:
                        results.append(sig)
        return results
    
    @property
    def multi_driven_signals(self) -> Dict[str, List[SemanticDriverRef]]:
        """返回所有被多驱动的信号"""
        result = {}
        for sig in self.sem_ast.all_signals:
            if sig.is_multi_driven:
                result[sig.name] = sig.drivers
        return result
    
    @property
    def clock_domains(self) -> Dict[str, List[str]]:
        """返回时钟域映射"""
        return self._clock_domain_index
    
    def get_signals_by_clock(self, clock: str) -> List[str]:
        """获取属于指定时钟域的所有信号"""
        return self._clock_domain_index.get(clock, [])
    
    def get_driver_chain(self, signal: str, max_depth: int = 10) -> List[str]:
        """获取信号的驱动链
        
        Args:
            signal: 信号名
            max_depth: 最大深度
        
        Returns:
            驱动链列表，如 ['a', 'b', 'c'] 表示 a ← b ← c ← ...
        """
        chain = []
        visited = set()
        current = signal
        
        for _ in range(max_depth):
            if current in visited:
                break
            visited.add(current)
            
            sig = self.find_signal(current)
            if not sig or not sig.drivers:
                break
            
            # 取第一个驱动源
            driver = sig.drivers[0]
            chain.append(driver.source_expr)
            current = driver.source_expr
        
        return chain
    
    def find_loads_by_signal(self, signal: str) -> List[SemanticLoadRef]:
        """查找加载指定信号的所有引用"""
        results = []
        for sig in self.sem_ast.all_signals:
            for load in sig.loads:
                if signal in load.load_expr:
                    results.append(load)
        return results
    
    def __repr__(self):
        return (f"SemanticRelationGraph(signals={len(self._signal_index)}, "
                f"instances={len(self._instance_index)}, "
                f"clock_domains={len(self._clock_domain_index)})")