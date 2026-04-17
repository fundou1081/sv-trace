"""
Signal Query - 信号查询接口
"""
from typing import List, Optional, Dict, Any
import pyslang
from ..core.models import Signal, SignalType


class SignalQuery:
    """信号查询接口"""
    
    def __init__(self, parser):
        self.parser = parser
    
    def find_signal(self, name: str, module_name: str = None) -> Optional[Signal]:
        """查找信号定义"""
        # 从 AST 中查找信号
        modules = [self.parser.get_module_by_name(module_name)] if module_name \
            else self.parser.get_modules()
        
        for module in modules:
            if not module:
                continue
            # 搜索成员
            for member in module.members:
                if hasattr(member, 'kind') and member.kind == pyslang.SyntaxKind.DataDeclaration:
                    if hasattr(member, 'declarators'):
                        for decl in member.declarators:
                            if hasattr(decl, 'name') and decl.name.value == name:
                                return self._to_signal(decl, member)
        
        return None
    
    def find_signals_by_pattern(self, pattern: str, module_name: str = None) -> List[Signal]:
        """按模式查找信号"""
        import re
        results = []
        
        modules = [self.parser.get_module_by_name(module_name)] if module_name \
            else self.parser.get_modules()
        
        for module in modules:
            if not module:
                continue
            for member in module.members:
                if hasattr(member, 'kind') and member.kind == pyslang.SyntaxKind.DataDeclaration:
                    if hasattr(member, 'declarators'):
                        for decl in member.declarators:
                            if hasattr(decl, 'name') and re.match(pattern, decl.name.value):
                                results.append(self._to_signal(decl, member))
        
        return results
    
    def _to_signal(self, decl, decl_info) -> Signal:
        """转换为信号对象"""
        width = 1
        signed = False
        
        # 提取位宽
        if hasattr(decl_info, 'dataType') and decl_info.dataType:
            if hasattr(decl_info.dataType, 'width') and decl_info.dataType.width:
                width = self._parse_width(decl_info.dataType.width)
            signed = hasattr(decl_info.dataType, 'signed') and decl_info.dataType.signed
        
        return Signal(
            name=decl.name.value,
            width=width,
            signed=signed,
        )
    
    def _parse_width(self, width) -> int:
        """解析位宽表达式"""
        if hasattr(width, 'matches') and width.matches:
            # 范围表达式 [7:0]
            msb = width.matches[0].value if width.matches else 0
            lsb = width.matches[1].value if len(width.matches) > 1 else 0
            return int(msb) - int(lsb) + 1
        return 1
