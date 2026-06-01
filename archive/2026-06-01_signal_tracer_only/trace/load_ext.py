"""LoadTracer Extended - 兼容层

迁移到 extractors/ 架构后，本文件作为兼容层。
trace/query/signal_chain.py 等依赖此模块。

底层使用新的 extractors/load.py，通过 SemanticGraph 提供：
- 正向负载查找 (signal 被谁驱动)
- 反向负载查找 (signal 被谁加载)

符合铁律 18-20: 底层调用 extractors/LoadExtractor
"""

from parse import SVParser
from trace.load import LoadTracer, LoadPoint

# re-export
__all__ = ['LoadTracerExt', 'LoadPoint']


class LoadTracerExt(LoadTracer):
    """扩展的 LoadTracer
    
    提供反向查找能力：通过 SemanticGraph.add_load 同时注册正向和反向关系，
    使得 graph.get_load(sig) 既能查到"谁驱动 sig"，也能查到"sig 被谁使用"。
    """
    
    def __init__(self, trees: dict = None, verbose: bool = True, use_semantic: bool = True):
        super().__init__(trees=trees, verbose=verbose, use_semantic=use_semantic)
    
    def trace(self, signal: str):
        """追踪信号的负载（正向）"""
        return self.find_load(signal)
    
    def reverse_lookup(self, signal: str):
        """反向查找：谁使用这个信号（作为 load_by）"""
        # SemanticGraph 的 loads 字典中，signal 作为 load_by 的记录
        # 即 graph.get_load(signal) 中 load_by == signal
        results = []
        for target, load_points in self.loads.items():
            for lp in load_points:
                if lp.load_by == signal:
                    results.append(lp)
        return results
    
    def get_loads_with_confidence(self, signal: str):
        """获取负载并标注置信度"""
        loads = self.find_load(signal)
        # TODO: 基于 ScopeTree 评估置信度
        return loads
