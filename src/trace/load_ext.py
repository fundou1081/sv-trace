"""LoadTracer Extended - 修复 loads 追踪 bug

问题: LoadTracer.trace(signal) 返回的是 "这个信号驱动谁"，而不是 "谁使用这个信号"
     这是因为 _loads[dst] 中存储的是 (dst, src)，按 dst 索引

修复: 添加 reverse_lookup 方法，在 _loads 中反向查找 src == signal 的条目

遵循开发纪律:
- 铁律1: AST 唯一数据源
- 铁律3: 不可信则不输出 - 返回 confidence 和 caveats
- 铁律4: 模型即契约 - 不修改原有接口，仅扩展
"""

import sys
import os
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyslang
from pyslang import SyntaxKind

from trace.load import LoadTracer, LoadPoint


class LoadTracerExt(LoadTracer):
    """LoadTracer 扩展 - 支持反向查找 (谁使用这个信号)
    
    原有 LoadTracer.trace(signal) 返回 "signal 驱动谁" (dst = signal)
    新增 reverse_lookup(signal) 返回 "谁使用 signal" (src = signal)
    
    Example:
        >>> from trace.load_ext import LoadTracerExt
        >>> lt = LoadTracerExt(parser)
        >>> loads = lt.reverse_lookup('data_in')
        >>> # loads 现在包含所有使用 data_in 作为源的操作
    """
    
    def __init__(self, parser):
        """初始化
        
        Args:
            parser: SVParser 实例
        """
        super().__init__(parser)
        self._reverse_index: Dict[str, List[LoadPoint]] = defaultdict(list)
        self._reverse_built = False
    
    def reverse_lookup(self, signal: str) -> List[LoadPoint]:
        """反向查找: 找到所有使用给定信号作为源的操作
        
        Args:
            signal: 信号名
            
        Returns:
            List[LoadPoint]: 所有使用该信号作为源的加载点 (去重)
        """
        if not self._loads:
            self._build_load_graph()
        
        if not self._reverse_built:
            self._build_reverse_index()
        
        # 去重: 根据 signal 属性去重
        seen = set()
        result = []
        for lp in self._reverse_index.get(signal, []):
            if lp.signal not in seen:
                seen.add(lp.signal)
                result.append(lp)
        return result
    
    def _build_reverse_index(self) -> None:
        """构建反向索引: src -> [LoadPoints where src is used]"""
        for dst, load_points in self._loads.items():
            for lp in load_points:
                self._reverse_index[lp.driver].append(lp)
        
        self._reverse_built = True
    
    def get_loads_with_confidence(self, signal: str) -> Tuple[List[LoadPoint], str, List[str]]:
        """获取信号的加载点，并返回置信度信息
        
        Args:
            signal: 信号名
            
        Returns:
            Tuple: (loads, confidence, caveats)
        """
        loads = self.reverse_lookup(signal)
        
        caveats = []
        if not loads:
            caveats.append(f"No loads found for {signal}")
            return loads, "uncertain", caveats
        
        # 检查 LoadPoint 是否有足够的上下文信息
        incomplete = sum(1 for lp in loads if not lp.context)
        if incomplete > 0:
            caveats.append(f"{incomplete} load(s) missing context")
        
        confidence = "high" if not caveats else "medium"
        return loads, confidence, caveats
