"""
Driver Tracer - 追踪信号驱动源
"""
import pyslang
from typing import List, Any
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.models import Driver, DriverKind


class DriverTracer:
    """信号驱动源追踪器"""
    
    def __init__(self, parser):
        self.parser = parser
        self.compilation = parser.compilation
    
    def find_driver(self, signal_name: str, module_name: str = None) -> List[Driver]:
        """查找信号的驱动源"""
        drivers = []
        
        for key, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root') or not tree.root:
                continue
            
            root = tree.root
            
            if 'ModuleDeclaration' not in str(type(root)):
                continue
            
            header = getattr(root, 'header', None)
            name = ""
            if header:
                name_attr = getattr(header, 'name', None)
                if name_attr:
                    name = name_attr.value
            
            if module_name and name != module_name:
                continue
            
            drivers.extend(self._find_in_module(root, signal_name))
        
        return drivers
    
    def _find_in_module(self, module, signal_name: str) -> List[Driver]:
        if not module:
            return []
        
        drivers = []
        
        # 检查 module.members
        if hasattr(module, 'members') and module.members:
            for m in module.members:
                drivers.extend(self._visit_member(m, signal_name))
        
        # 检查 module.body
        if hasattr(module, 'body') and module.body:
            for b in module.body:
                drivers.extend(self._visit_member(b, signal_name))
        
        return drivers
    
    def _visit_member(self, node, signal_name: str) -> List[Driver]:
        if not node:
            return []
        
        drivers = []
        type_name = str(type(node))
        
        # ContinuousAssign
        if 'ContinuousAssign' in type_name:
            drivers.extend(self._extract_continuous_assign(node, signal_name))
        
        # ProceduralBlock (always_ff/comb/latch)
        elif 'ProceduralBlock' in type_name:
            drivers.extend(self._extract_always_block(node, signal_name))
        
        # 递归
        for attr in ['members', 'body', 'statements']:
            if hasattr(node, attr):
                child = getattr(node, attr)
                if child:
                    if isinstance(child, list):
                        for c in child:
                            drivers.extend(self._visit_member(c, signal_name))
                    else:
                        drivers.extend(self._visit_member(child, signal_name))
        
        return drivers
    
    def _extract_continuous_assign(self, assign, signal_name: str) -> List[Driver]:
        drivers = []
        
        if not hasattr(assign, 'assignments') or not assign.assignments:
            return drivers
        
        for stmt in assign.assignments:
            if not hasattr(stmt, 'left'):
                continue
            
            var = stmt.left
            var_name = str(var).strip()
            
            if var_name == signal_name:
                line = 0
                try:
                    if hasattr(stmt, 'getFirstToken') and stmt.getFirstToken():
                        line = stmt.getFirstToken().location.offset
                except:
                    pass
                
                source = str(stmt.right) if hasattr(stmt, 'right') else ""
                
                drivers.append(Driver(
                    signal_name=signal_name,
                    driver_kind=DriverKind.ASSIGN,
                    source_expr=source,
                    line=line,
                ))
        
        return drivers
    
    def _extract_always_block(self, always, signal_name: str) -> List[Driver]:
        drivers = []
        
        if not hasattr(always, 'statement') or not always.statement:
            return drivers
        
        # 判断类型 - 通过检查 event control
        driver_type = DriverKind.ALWAYS_FF
        
        # 检查 clock event
        if hasattr(always, 'statement') and always.statement:
            stmt = always.statement
            # 查找 event control
            if hasattr(stmt, 'control') and stmt.control:
                ctrl = stmt.control
                if hasattr(ctrl, 'Event'):
                    # FF
                    driver_type = DriverKind.ALWAYS_FF
                elif hasattr(ctrl, 'delay'):
                    driver_type = DriverKind.ALWAYS_COMB
        
        self._find_assignment_in_stmt(always.statement, signal_name, driver_type, drivers)
        
        return drivers
    
    def _find_assignment_in_stmt(self, stmt, signal_name: str,
                              driver_type: DriverKind, drivers: List[Driver]):
        if not stmt:
            return
        
        type_name = str(type(stmt))
        
        # 赋值语句 - 检查 NonBlocking 或 Blocking
        if 'NonBlocking' in type_name or 'Blocking' in type_name:
            self._extract_blocking_assignment(stmt, signal_name, driver_type, drivers)
        
        # If 语句
        elif 'If' in type_name:
            if hasattr(stmt, 'ifBody') and stmt.ifBody:
                self._find_assignment_in_stmt(stmt.ifBody, signal_name, driver_type, drivers)
            if hasattr(stmt, 'elseBody') and stmt.elseBody:
                self._find_assignment_in_stmt(stmt.elseBody, signal_name, driver_type, drivers)
        
        # Case 语句
        elif 'Case' in type_name:
            if hasattr(stmt, 'items') and stmt.items:
                for item in stmt.items:
                    if hasattr(item, 'body') and item.body:
                        self._find_assignment_in_stmt(item.body, signal_name, driver_type, drivers)
        
        # 递归
        for attr in ['statements', 'body', 'ifBody', 'elseBody', 'control']:
            if hasattr(stmt, attr):
                child = getattr(stmt, attr)
                if child:
                    if isinstance(child, list):
                        for c in child:
                            self._find_assignment_in_stmt(c, signal_name, driver_type, drivers)
                    else:
                        self._find_assignment_in_stmt(child, signal_name, driver_type, drivers)
    
    def _extract_blocking_assignment(self, stmt, signal_name: str,
                             driver_type: DriverKind, drivers: List[Driver]):
        if not hasattr(stmt, 'left') or not stmt.left:
            return
        
        var = stmt.left
        var_name = str(var).strip()
        
        if var_name != signal_name:
            return
        
        line = 0
        try:
            if hasattr(stmt, 'getFirstToken') and stmt.getFirstToken():
                line = stmt.getFirstToken().location.offset
        except:
            pass
        
        source_expr = str(stmt.right) if hasattr(stmt, 'right') else ""
        
        drivers.append(Driver(
            signal_name=signal_name,
            driver_kind=driver_type,
            source_expr=source_expr,
            line=line,
        ))
    
    def _extract_assignment_stmt(self, stmt, signal_name: str,
                            driver_type: DriverKind, drivers: List[Driver]):
        self._extract_blocking_assignment(stmt, signal_name, driver_type, drivers)
