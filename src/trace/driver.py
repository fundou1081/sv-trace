"""
Driver Tracer - 追踪信号驱动源
"""
import pyslang
from typing import List, Dict, Any, Optional
from ..core.models import Driver, DriverKind


class DriverTracer:
    """信号驱动源追踪器"""
    
    def __init__(self, parser):
        self.parser = parser
        self.compilation = parser.compilation
    
    def find_driver(self, signal_name: str, module_name: str = None) -> List[Driver]:
        """查找信号的驱动源"""
        drivers = []
        
        # 获取模块
        if module_name:
            module = self.parser.get_module_by_name(module_name)
            if module:
                drivers.extend(self._find_in_module(module, signal_name))
        else:
            # 全局搜索
            for module in self.parser.get_modules():
                drivers.extend(self._find_in_module(module, signal_name))
        
        return drivers
    
    def _find_in_module(self, module, signal_name: str) -> List[Driver]:
        """在模块中查找驱动"""
        drivers = []
        
        # 遍历模块成员
        if not hasattr(module, 'members'):
            return drivers
        
        for member in module.members:
            if not hasattr(member, 'kind'):
                continue
            
            kind = member.kind
            
            if kind == pyslang.SyntaxKind.ContinuousAssign:
                drivers.extend(self._extract_continuous_assign(member, signal_name))
            elif kind == pyslang.SyntaxKind.AlwaysBlock:
                drivers.extend(self._extract_always_block(member, signal_name))
        
        return drivers
    
    def _extract_continuous_assign(self, assign, signal_name: str) -> List[Driver]:
        """提取连续赋值驱动"""
        drivers = []
        
        if not hasattr(assign, 'assignment') or not assign.assignment:
            return drivers
        
        for stmt in assign.assignment:
            if not hasattr(stmt, 'variable') or not stmt.variable:
                continue
            
            # 检查是否是目标信号
            var_name = stmt.variable.name.value if hasattr(stmt.variable, 'name') else ""
            if var_name == signal_name:
                drivers.append(Driver(
                    signal_name=signal_name,
                    driver_kind=DriverKind.ASSIGN,
                    source_expr=str(stmt.value) if hasattr(stmt, 'value') else "",
                    line=stmt.getFirstToken().location.line if hasattr(stmt, 'getFirstToken') else 0,
                ))
        
        return drivers
    
    def _extract_always_block(self, always, signal_name: str) -> List[Driver]:
        """提取 always 块驱动"""
        drivers = []
        
        if not hasattr(always, 'statement') or not always.statement:
            return drivers
        
        # 判断 always 类型
        block_kind = always.kind if hasattr(always, 'kind') else pyslang.SyntaxKind.AlwaysBlock
        
        # 递归查找赋值语句
        drivers.extend(self._find_assignment_in_stmt(
            always.statement, signal_name, block_kind
        ))
        
        return drivers
    
    def _find_assignment_in_stmt(self, stmt, signal_name: str, 
                      block_kind) -> List[Driver]:
        """在语句中查找赋值"""
        drivers = []
        
        if not stmt:
            return drivers
        
        # 查找阻塞/非阻塞赋值
        if hasattr(stmt, 'kind'):
            if stmt.kind in (pyslang.SyntaxKind.NonBlockingAssignment, 
                        pyslang.SyntaxKind.BlockingAssignment):
                drivers.extend(self._extract_assignment(stmt, signal_name, block_kind))
            elif stmt.kind == pyslang.SyntaxKind.IfStatement:
                if hasattr(stmt, 'ifBody'):
                    drivers.extend(self._find_assignment_in_stmt(
                        stmt.ifBody, signal_name, block_kind))
                if hasattr(stmt, 'elseBody'):
                    drivers.extend(self._find_assignment_in_stmt(
                        stmt.elseBody, signal_name, block_kind))
            elif stmt.kind == pyslang.SyntaxKind.CaseStatement:
                if hasattr(stmt, 'caseItems'):
                    for item in stmt.caseItems:
                        if hasattr(item, 'body'):
                            drivers.extend(self._find_assignment_in_stmt(
                                item.body, signal_name, block_kind))
        
        return drivers
    
    def _extract_assignment(self, stmt, signal_name: str, 
                         block_kind) -> List[Driver]:
        """提取赋值语句"""
        drivers = []
        
        if not hasattr(stmt, 'variable') or not stmt.variable:
            return drivers
        
        # 获取目标信号名
        var_name = ""
        if hasattr(stmt.variable, 'name'):
            var_name = stmt.variable.name.value
        elif hasattr(stmt.variable, 'name') and stmt.variable.name:
            var_name = stmt.variable.name.value
        
        if var_name != signal_name:
            return drivers
        
        # 确定驱动类型
        if stmt.kind == pyslang.SyntaxKind.NonBlockingAssignment:
            driver_type = self._detect_driver_kind(block_kind)
        else:
            driver_type = DriverKind.ALWAYS_COMB
        
        drivers.append(Driver(
            signal_name=signal_name,
            driver_kind=driver_type,
            source_expr=str(stmt.value) if hasattr(stmt, 'value') else "",
            line=stmt.getFirstToken().location.line if hasattr(stmt, 'getFirstToken') else 0,
        ))
        
        return drivers
    
    def _detect_driver_kind(self, block_kind) -> DriverKind:
        """检测驱动类型"""
        kind_map = {
            pyslang.SyntaxKind.AlwaysFFBlock: DriverKind.ALWAYS_FF,
            pyslang.SyntaxKind.AlwaysCombBlock: DriverKind.ALWAYS_COMB,
            pyslang.SyntaxKind.AlwaysLatchBlock: DriverKind.ALWAYS_LATCH,
        }
        return kind_map.get(block_kind, DriverKind.ALWAYS_FF)
