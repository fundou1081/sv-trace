"""
Load Tracer - 追踪信号加载点
"""
import pyslang
from typing import List, Any
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.models import Load


class LoadTracer:
    """信号加载点追踪器"""
    
    def __init__(self, parser):
        self.parser = parser
        self.compilation = parser.compilation
    
    def find_load(self, signal_name: str, module_name: str = None) -> List[Load]:
        """查找信号的加载点"""
        loads = []
        
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
            
            loads.extend(self._find_in_module(root, signal_name))
        
        return loads
    
    def _find_in_module(self, module, signal_name: str) -> List[Load]:
        if not module:
            return []
        
        loads = []
        
        # 检查 module.members
        if hasattr(module, 'members') and module.members:
            for m in module.members:
                loads.extend(self._visit_member(m, signal_name))
        
        # 检查 module.body
        if hasattr(module, 'body') and module.body:
            for b in module.body:
                loads.extend(self._visit_member(b, signal_name))
        
        return loads
    
    def _visit_member(self, node, signal_name: str) -> List[Load]:
        if not node:
            return []
        
        loads = []
        type_name = str(type(node))
        
        # ContinuousAssign - 检查 RHS 使用
        if 'ContinuousAssign' in type_name:
            loads.extend(self._extract_continuous_assign(node, signal_name))
        
        # ProceduralBlock
        elif 'ProceduralBlock' in type_name:
            loads.extend(self._extract_always_load(node, signal_name))
        
        # Function/Task
        elif 'Function' in type_name or 'Task' in type_name:
            loads.extend(self._extract_func_load(node, signal_name))
        
        # 递归
        for attr in ['members', 'body', 'statements']:
            if hasattr(node, attr):
                child = getattr(node, attr)
                if child:
                    if isinstance(child, list):
                        for c in child:
                            loads.extend(self._visit_member(c, signal_name))
                    else:
                        loads.extend(self._visit_member(child, signal_name))
        
        return loads
    
    def _extract_continuous_assign(self, assign, signal_name: str) -> List[Load]:
        """提取连续赋值中的加载（RHS 使用）"""
        loads = []
        
        if not hasattr(assign, 'assignments') or not assign.assignments:
            return loads
        
        for stmt in assign.assignments:
            if not hasattr(stmt, 'right'):
                continue
            
            # 检查 RHS 是否包含信号名
            rhs = str(stmt.right)
            if signal_name in rhs:
                line = 0
                try:
                    if hasattr(stmt, 'getFirstToken') and stmt.getFirstToken():
                        line = stmt.getFirstToken().location.offset
                except:
                    pass
                
                loads.append(Load(
                    signal_name=signal_name,
                    context=rhs,
                    line=line,
                ))
        
        return loads
    
    def _extract_always_load(self, always, signal_name: str) -> List[Load]:
        """提取 always 块中的加载"""
        loads = []
        
        if not hasattr(always, 'statement') or not always.statement:
            return loads
        
        self._find_load_in_stmt(always.statement, signal_name, loads)
        
        return loads
    
    def _extract_func_load(self, func, signal_name: str) -> List[Load]:
        """提取函数/任务中的加载"""
        loads = []
        
        # 检查 body
        body = getattr(func, 'body', None)
        if body:
            self._find_load_in_stmt(body, signal_name, loads)
        
        # 检查 statements
        if hasattr(func, 'statements') and func.statements:
            for stmt in func.statements:
                self._find_load_in_stmt(stmt, signal_name, loads)
        
        return loads
    
    def _find_load_in_stmt(self, stmt, signal_name: str, loads: List[Load]):
        """在语句中查找信号引用"""
        if not stmt:
            return
        
        type_name = str(type(stmt))
        
        # 赋值 - 检查 RHS
        if 'Assignment' in type_name:
            if hasattr(stmt, 'right') and stmt.right:
                rhs = str(stmt.right)
                if signal_name in rhs:
                    line = 0
                    try:
                        if hasattr(stmt, 'getFirstToken') and stmt.getFirstToken():
                            line = stmt.getFirstToken().location.offset
                    except:
                        pass
                    
                    loads.append(Load(
                        signal_name=signal_name,
                        context=rhs,
                        line=line,
                    ))
        
        # If 语句 - 递归检查条件
        elif 'If' in type_name:
            if hasattr(stmt, 'ifBody') and stmt.ifBody:
                self._find_load_in_stmt(stmt.ifBody, signal_name, loads)
            if hasattr(stmt, 'elseBody') and stmt.elseBody:
                self._find_load_in_stmt(stmt.elseBody, signal_name, loads)
        
        # Case 语句
        elif 'Case' in type_name:
            if hasattr(stmt, 'condition') and stmt.condition:
                cond = str(stmt.condition)
                if signal_name in cond:
                    line = 0
                    try:
                        if hasattr(stmt, 'getFirstToken') and stmt.getFirstToken():
                            line = stmt.getFirstToken().location.offset
                    except:
                        pass
                    
                    loads.append(Load(
                        signal_name=signal_name,
                        context=cond,
                        line=line,
                    ))
            
            if hasattr(stmt, 'items') and stmt.items:
                for item in stmt.items:
                    if hasattr(item, 'body') and item.body:
                        self._find_load_in_stmt(item.body, signal_name, loads)
        
        # 递归
        for attr in ['statements', 'body', 'ifBody', 'elseBody', 'condition']:
            if hasattr(stmt, attr):
                child = getattr(stmt, attr)
                if child:
                    if isinstance(child, list):
                        for c in child:
                            self._find_load_in_stmt(c, signal_name, loads)
                    else:
                        self._find_load_in_stmt(child, signal_name, loads)
