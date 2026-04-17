"""
Load Tracer - 追踪信号加载点
"""
import pyslang
from typing import List, Dict, Any
from ..core.models import Load


class LoadTracer:
    """信号加载点追踪器"""
    
    def __init__(self, parser):
        self.parser = parser
        self.compilation = parser.compilation
    
    def find_load(self, signal_name: str, module_name: str = None) -> List[Load]:
        """查找信号的加载点"""
        loads = []
        
        # 获取模块
        if module_name:
            module = self.parser.get_module_by_name(module_name)
            if module:
                loads.extend(self._find_in_module(module, signal_name))
        else:
            for module in self.parser.get_modules():
                loads.extend(self._find_in_module(module, signal_name))
        
        return loads
    
    def _find_in_module(self, module, signal_name: str) -> List[Load]:
        """在模块中查找加载"""
        loads = []
        
        if not hasattr(module, 'members'):
            return loads
        
        for member in module.members:
            if not hasattr(member, 'kind'):
                continue
            
            kind = member.kind
            
            # 在连续赋值、always 块、函数等中查找
            if kind in (pyslang.SyntaxKind.ContinuousAssign,
                    pyslang.SyntaxKind.AlwaysBlock,
                    pyslang.SyntaxKind.FunctionDeclaration,
                    pyslang.SyntaxKind.TaskDeclaration):
                loads.extend(self._find_in_block(member, signal_name))
        
        return loads
    
    def _find_in_block(self, block, signal_name: str) -> List[Load]:
        """在块中查找加载"""
        loads = []
        
        # 提取所有表达式引用
        # 这里需要遍历 AST 查找对信号的引用
        # 简化版本：检查 if/while/case 等条件中是否使用信号
        
        return loads
