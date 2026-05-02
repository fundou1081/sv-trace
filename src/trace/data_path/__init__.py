"""Data Path Analysis Module

RTL数据通路概率分析 - 寻找低概率×高影响组合
"""

from .extractor import DataPathExtractor, extract_data_path
from .graph import DataPathGraph
from .analyzer import ProbabilisticDataPathAnalyzer

# 提供别名以便兼容
analyze_data_path = extract_data_path

__all__ = [
    'DataPathExtractor',
    'DataPathGraph',
    'ProbabilisticDataPathAnalyzer',
    'extract_data_path',
    'analyze_data_path',
]
