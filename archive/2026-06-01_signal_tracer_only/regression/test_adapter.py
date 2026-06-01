"""
TestAdapter - 测试适配自动化
根据RTL变更自动适配测试用例
"""
import os
import re
from typing import List, Dict, Set

class TestAdapter:
    """测试适配器"""
    
    def __init__(self):
        self.signal_map = {}  # 旧信号 -> 新信号的映射
    
    def detect_signal_renames(self, old_file: str, new_file: str) -> Dict[str, str]:
        """检测信号重命名"""
        # 简化版本：基于模式匹配
        rename_map = {}
        
        # 实际应该用AST对比，这里是简化版本
        # TODO: 实现完整的信号重命名检测
        
        return rename_map
    
    def adapt_test_for_change(self, test_file: str, changes: List[str]) -> bool:
        """根据变更适配测试"""
        # 1. 分析变更影响的信号
        affected_signals = self._analyze_affected_signals(changes)
        
        # 2. 检查测试是否依赖这些信号
        test_deps = self._extract_test_dependencies(test_file)
        
        # 3. 找出需要适配的测试
        needs_adapter = affected_signals & test_deps
        
        if needs_adapter:
            # TODO: 生成适配代码
            pass
        
        return True
    
    def _analyze_affected_signals(self, changes: List[str]) -> Set[str]:
        """分析变更影响的信号"""
        signals = set()
        for change in changes:
            # 简化：提取=左边的信号
            match = re.search(r'(\w+)\s*<=', change)
            if match:
                signals.add(match.group(1))
        return signals
    
    def _extract_test_dependencies(self, test_file: str) -> Set[str]:
        """提取测试依赖的信号"""
        if not os.path.exists(test_file):
            return set()
        
        with open(test_file, 'r') as f:
            content = f.read()
        
        signals = set()
        # 简化：提取所有信号名
        matches = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', content)
        signals.update(matches)
        
        return signals
