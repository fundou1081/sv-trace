"""
Driver Tracer - 追踪信号驱动源
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.models import Driver, DriverKind


class DriverTracer:
    """信号驱动源追踪器"""
    
    def __init__(self, parser):
        self.parser = parser
        self.compilation = parser.compilation
    
    def find_driver(self, signal_name: str, module_name: str = None):
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
    
    def _find_in_module(self, module, signal_name: str):
        if not module:
            return []
        
        drivers = []
        
        if hasattr(module, 'members') and module.members:
            for m in module.members:
                drivers.extend(self._visit_member(m, signal_name))
        
        if hasattr(module, 'body') and module.body:
            for b in module.body:
                drivers.extend(self._visit_member(b, signal_name))
        
        return drivers
    
    def _visit_member(self, node, signal_name: str):
        if not node:
            return []
        
        drivers = []
        type_name = str(type(node))
        
        if 'ContinuousAssign' in type_name:
            drivers.extend(self._extract_continuous_assign(node, signal_name))
        
        elif 'ProceduralBlock' in type_name:
            drivers.extend(self._extract_always_block(node, signal_name))
        
        elif 'Function' in type_name or 'Task' in type_name:
            drivers.extend(self._extract_func_driver(node, signal_name))
        
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
    
    def _extract_continuous_assign(self, assign, signal_name: str):
        drivers = []
        
        if not hasattr(assign, 'assignments') or not assign.assignments:
            return drivers
        
        for stmt in assign.assignments:
            if not hasattr(stmt, 'left'):
                continue
            
            var_name = str(stmt.left).strip()
            
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
    
    def _extract_always_block(self, always, signal_name: str):
        drivers = []
        
        if not hasattr(always, 'statement'):
            return drivers
        
        stmt = always.statement
        driver_type = self._detect_always_type(always)
        
        if 'TimingControl' in str(type(stmt)):
            if hasattr(stmt, 'statement'):
                self._process_expression_stmt(stmt.statement, signal_name, driver_type, drivers)
        else:
            self._find_assignment_in_stmt(stmt, signal_name, driver_type, drivers)
        
        return drivers
    
    def _detect_always_type(self, always):
        if hasattr(always, 'statement') and always.statement:
            stmt = always.statement
            if hasattr(stmt, 'timingControl') and stmt.timingControl:
                tc = stmt.timingControl
                if hasattr(tc, 'event') and tc.event:
                    return DriverKind.ALWAYS_FF
                elif hasattr(tc, 'delay'):
                    return DriverKind.ALWAYS_COMB
        
        return DriverKind.ALWAYS_FF
    
    def _extract_func_driver(self, func, signal_name: str):
        drivers = []
        
        body = getattr(func, 'body', None)
        if body:
            self._find_assignment_in_stmt(body, signal_name, DriverKind.ALWAYS_COMB, drivers)
        
        if hasattr(func, 'statements') and func.statements:
            for stmt in func.statements:
                self._find_assignment_in_stmt(stmt, signal_name, DriverKind.ALWAYS_COMB, drivers)
        
        return drivers
    
    def _process_expression_stmt(self, stmt, signal_name: str,
                                  driver_type, drivers):
        expr = getattr(stmt, 'expr', None)
        if not expr:
            return
        
        type_name = str(type(expr))
        
        if 'Binary' in type_name:
            left = getattr(expr, 'left', None)
            if left:
                var_name = str(left).strip()
                if var_name == signal_name:
                    line = 0
                    try:
                        if hasattr(stmt, 'getFirstToken') and stmt.getFirstToken():
                            line = stmt.getFirstToken().location.offset
                    except:
                        pass
                    
                    drivers.append(Driver(
                        signal_name=signal_name,
                        driver_kind=driver_type,
                        source_expr=str(expr),
                        line=line,
                    ))
        
        if hasattr(expr, 'statements'):
            for s in expr.statements:
                self._find_assignment_in_stmt(s, signal_name, driver_type, drivers)
    
    def _find_assignment_in_stmt(self, stmt, signal_name: str,
                              driver_type, drivers):
        if not stmt:
            return
        
        type_name = str(type(stmt))
        
        if 'Expression' in type_name:
            self._process_expr_stmt(stmt, signal_name, driver_type, drivers)
        
        elif 'If' in type_name:
            if hasattr(stmt, 'ifBody') and stmt.ifBody:
                self._find_assignment_in_stmt(stmt.ifBody, signal_name, driver_type, drivers)
            if hasattr(stmt, 'elseBody') and stmt.elseBody:
                self._find_assignment_in_stmt(stmt.elseBody, signal_name, driver_type, drivers)
        
        elif 'Case' in type_name:
            if hasattr(stmt, 'items') and stmt.items:
                for item in stmt.items:
                    if hasattr(item, 'body') and item.body:
                        self._find_assignment_in_stmt(item.body, signal_name, driver_type, drivers)
            if hasattr(stmt, 'defaultItem') and stmt.defaultItem:
                self._find_assignment_in_stmt(stmt.defaultItem, signal_name, driver_type, drivers)
        
        elif 'ForLoop' in type_name:
            if hasattr(stmt, 'body') and stmt.body:
                self._find_assignment_in_stmt(stmt.body, signal_name, driver_type, drivers)
        
        elif 'WhileLoop' in type_name:
            if hasattr(stmt, 'body') and stmt.body:
                self._find_assignment_in_stmt(stmt.body, signal_name, driver_type, drivers)
        
        for attr in ['statements', 'body', 'ifBody', 'elseBody']:
            if hasattr(stmt, attr):
                child = getattr(stmt, attr)
                if child:
                    if isinstance(child, list):
                        for c in child:
                            self._find_assignment_in_stmt(c, signal_name, driver_type, drivers)
                    else:
                        self._find_assignment_in_stmt(child, signal_name, driver_type, drivers)
    
    def _process_expr_stmt(self, stmt, signal_name: str,
                         driver_type, drivers):
        expr = getattr(stmt, 'expr', None)
        if not expr:
            return
        
        type_name = str(type(expr))
        
        if 'Binary' in type_name:
            left = getattr(expr, 'left', None)
            if left:
                var_name = str(left).strip()
                if var_name == signal_name:
                    line = 0
                    try:
                        if hasattr(stmt, 'getFirstToken') and stmt.getFirstToken():
                            line = stmt.getFirstToken().location.offset
                    except:
                        pass
                    
                    drivers.append(Driver(
                        signal_name=signal_name,
                        driver_kind=driver_type,
                        source_expr=str(expr),
                        line=line,
                    ))
        
        for attr in ['left', 'right']:
            if hasattr(expr, attr):
                child = getattr(expr, attr)
                if child:
                    self._process_expr_stmt(child, signal_name, driver_type, drivers)
