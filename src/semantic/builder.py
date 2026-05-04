"""
Semantic Builder - 从 pyslang 构建语义图
"""
import pyslang
from typing import Dict, Set, List, Optional
from .signal import SignalNode, PortDirection
from .connection import ConnectionEdge, ClockEdge, ResetEdge
from .graph import SemanticGraph


class SemanticBuilder:
    """构建器 - 将 pyslang AST 转换为语义图"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.graph = SemanticGraph()
        
        # 路径追踪
        self._current_module = ""
        self._signal_paths: Dict[str, str] = {}  # name -> full_path
        
    def build(self, tree: pyslang.SyntaxTree, filename: str) -> SemanticGraph:
        """从 SyntaxTree 构建语义图"""
        
        # 重置
        self.graph = SemanticGraph()
        self._current_module = filename
        
        # 遍历 AST
        tree.root.visit(self._visitor)
        
        self.graph.elaborated = True
        return self.graph
    
    def _visitor(self, node):
        """AST 遍历"""
        kn = node.kind.name if hasattr(node.kind, 'name') else ''
        
        # 模块声明
        if kn == 'ModuleDeclaration':
            self._current_module = self._get_module_name(node)
            self.graph.top_modules.add(self._current_module)
        
        # 端口声明
        elif kn == 'PortDeclaration':
            port = self._extract_port(node)
            if port:
                self.graph.add_signal(port)
        
        # 变量声明
        elif kn == 'VariableDeclarator':
            var = self._extract_variable(node)
            if var:
                self.graph.add_signal(var)
        
        # 连续赋值 (assign)
        elif kn == 'ContinuousAssign':
            self._extract_assign(node)
        
        # always_ff (时序逻辑)
        elif kn == 'AlwaysFFBlock':
            self._extract_always_ff(node)
        
        # always_comb (组合逻辑)
        elif kn == 'AlwaysCombBlock':
            self._extract_always_comb(node)
        
        return pyslang.VisitAction.Advance
    
    def _get_module_name(self, node) -> str:
        try:
            return str(node.header.name)
        except:
            return "unknown"
    
    def _extract_port(self, node) -> Optional[SignalNode]:
        """提取端口"""
        try:
            name = direction = ""
            width = 1
            
            for child in node:
                ckn = child.kind.name if hasattr(child.kind, 'name') else ''
                
                if ckn == 'Identifier':
                    name = str(child)
                elif ckn in ('InputKeyword', 'OutputKeyword', 'InoutKeyword'):
                    direction = PortDirection.INPUT if 'Input' in ckn else \
                               PortDirection.OUTPUT if 'Output' in ckn else PortDirection.INOUT
            
            if name:
                path = f"{self._current_module}.{name}"
                return SignalNode(
                    full_path=path,
                    width=width,
                    kind='port',
                    direction=direction,
                    module_path=self._current_module,
                )
        except:
            pass
        return None
    
    def _extract_variable(self, node) -> Optional[SignalNode]:
        """提取变量声明"""
        try:
            name = width = 1
            
            for child in node:
                ckn = child.kind.name if hasattr(child.kind, 'name') else ''
                
                if ckn == 'Identifier':
                    name = str(child)
            
            if name:
                path = f"{self._current_module}.{name}"
                return SignalNode(
                    full_path=path,
                    width=width,
                    kind='reg' if 'logic' in str(node) else 'wire',
                    direction=PortDirection.INTERNAL,
                    module_path=self._current_module,
                )
        except:
            pass
        return None
    
    def _extract_assign(self, node) -> None:
        """提取连续赋值"""
        # 简化: 记录到连接
        for child in node:
            ckn = child.kind.name if hasattr(child.kind, 'name') else ''
            if ckn == 'AssignmentPattern':
                # 取左手右手
                pass
    
    def _extract_always_ff(self, node) -> None:
        """提取 always_ff"""
        # 提取时钟和复位
        for child in node:
            ckn = child.kind.name if hasattr(child.kind, 'name') else ''
            if ckn == 'TimingControlStatement':
                for sub in child:
                    skn = sub.kind.name if hasattr(sub.kind, 'name') else ''
                    if skn == 'EventControlWithExpression':
                        # 提取时钟
                        pass
    
    def _extract_always_comb(self, node) -> None:
        """提取 always_comb"""
        pass


__all__ = ['SemanticBuilder']
