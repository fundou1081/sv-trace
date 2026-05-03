"""Signal Query - SystemVerilog 统一信号查询接口。

提供信号的查找、过滤和详细信息查询功能。

Example:
    >>> from query.signal import SignalQuery
    >>> from parse import SVParser
    >>> parser = SVParser()
    >>> parser.parse_file("design.sv")
    >>> sq = SignalQuery(parser)
    >>> sig = sq.find_signal("clk", "top")
    >>> print(f"Found: {sig.name} [{sig.width} bits]")
"""
import sys
import os
import pyslang
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.models import Signal
from parse.params import ParameterResolver
from typing import List, Optional


class SignalQuery:
    """信号查询器。
    
    提供信号查找和查询功能，支持按名称和模块名过滤。

    Attributes:
        parser: SVParser 实例
        param_resolver: 参数解析器
    
    Example:
        >>> sq = SignalQuery(parser)
        >>> sig = sq.find_signal("clk", "top")
    """
    
    def __init__(self, parser):
        """初始化信号查询器。
        
        Args:
            parser: SVParser 实例
        """
        self.parser = parser
        self.param_resolver = ParameterResolver(parser)
    
    def find_signal(self, name: str, module_name: str = None) -> Optional[Signal]:
        """查找信号。
        
        在指定模块中查找信号，首先搜索端口，然后搜索内部信号声明。

        Args:
            name: 信号名称
            module_name: 可选的模块名过滤
        
        Returns:
            Signal: 找到的信号对象，未找到返回 None
        """
        from core.models import Signal
        
        # 遍历所有解析的树
        for key, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root') or not tree.root:
                continue
            
            root = tree.root
            
            # Use visitor to find all ModuleDeclarations
            modules = []
            def visitor(node):
                if node.kind == pyslang.SyntaxKind.ModuleDeclaration:
                    modules.append(node)
                return pyslang.VisitAction.Advance
            
            root.visit(visitor)
            
            for member in modules:
                # 获取模块名
                header = getattr(member, 'header', None)
                mod_name = ""
                if header:
                    name_attr = getattr(header, 'name', None)
                    if name_attr:
                        try:
                            mod_name = name_attr.value
                        except:
                            mod_name = str(name_attr)
                
                if module_name and mod_name != module_name:
                    continue
                
                # 1. 首先在端口列表中查找 (ImplicitAnsiPort)
                ports = []
                def port_visitor(n):
                    if n.kind == pyslang.SyntaxKind.ImplicitAnsiPort:
                        ports.append(n)
                    return pyslang.VisitAction.Advance
                
                member.visit(port_visitor)
                
                for p in ports:
                    if hasattr(p, 'declarator') and p.declarator:
                        decl = p.declarator
                        if hasattr(decl, 'name') and decl.name:
                            decl_name = str(decl.name).strip()
                            if decl_name == name:
                                # Get width from dimensions string
                                width = 1
                                if hasattr(p, 'header') and p.header:
                                    header = p.header
                                    if hasattr(header, 'dataType') and header.dataType:
                                        dt = header.dataType
                                        if hasattr(dt, 'dimensions') and dt.dimensions:
                                            dim_str = str(dt.dimensions)
                                            match = re.search(r'\[(\d+):(\d+)\]', dim_str)
                                            if match:
                                                left = int(match.group(1))
                                                right = int(match.group(2))
                                                width = left - right + 1
                                
                                return Signal(name=name, module=mod_name, width=width)
                
                # 2. 然后在模块 body 中查找信号声明 (DataDeclaration)
                data_decls = []
                def data_visitor(n):
                    if n.kind == pyslang.SyntaxKind.DataDeclaration:
                        data_decls.append(n)
                    return pyslang.VisitAction.Advance
                
                member.visit(data_visitor)
                
                for body_member in data_decls:
                    if hasattr(body_member, 'declarators') and body_member.declarators:
                        declarators = body_member.declarators
                        for j in range(len(declarators)):
                            decl = declarators[j]
                            if hasattr(decl, 'name') and decl.name:
                                decl_name = str(decl.name).strip()
                                if decl_name == name:
                                    # Get width from type
                                    width = 1
                                    if hasattr(body_member, 'type') and body_member.type:
                                        typ = body_member.type
                                        if hasattr(typ, 'dimensions') and typ.dimensions:
                                            dim_str = str(typ.dimensions)
                                            match = re.search(r'\[(\d+):(\d+)\]', dim_str)
                                            if match:
                                                left = int(match.group(1))
                                                right = int(match.group(2))
                                                width = left - right + 1
                                    
                                    return Signal(name=name, module=mod_name, width=width)
        
        # 没找到
        return None
    
    def query_signal(self, name: str, module_name: str = None) -> Optional[Signal]:
        """查询信号的详细信息。
        
        Args:
            name: 信号名称
            module_name: 可选的模块名过滤
        
        Returns:
            Signal: 信号对象，未找到返回 None
        """
        return self.find_signal(name, module_name)
    
    def get_all_signals(self, module_name: str = None) -> List[Signal]:
        """获取所有信号。
        
        Args:
            module_name: 可选的模块名过滤
        
        Returns:
            List[Signal]: 信号列表
        """
        signals = []
        
        for key, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root') or not tree.root:
                continue
            
            root = tree.root
            
            # Use visitor to find all ModuleDeclarations
            modules = []
            def visitor(node):
                if node.kind == pyslang.SyntaxKind.ModuleDeclaration:
                    modules.append(node)
                return pyslang.VisitAction.Advance
            
            root.visit(visitor)
            
            for member in modules:
                # 获取模块名
                header = getattr(member, 'header', None)
                mod_name = ""
                if header:
                    name_attr = getattr(header, 'name', None)
                    if name_attr:
                        try:
                            mod_name = name_attr.value
                        except:
                            mod_name = str(name_attr)
                
                if module_name and mod_name != module_name:
                    continue
                
                # Find ports
                ports = []
                def port_visitor(n):
                    if n.kind == pyslang.SyntaxKind.ImplicitAnsiPort:
                        ports.append(n)
                    return pyslang.VisitAction.Advance
                
                member.visit(port_visitor)
                
                for p in ports:
                    if hasattr(p, 'declarator') and p.declarator:
                        decl = p.declarator
                        if hasattr(decl, 'name') and decl.name:
                            name = str(decl.name).strip()
                            
                            # Get width
                            width = 1
                            if hasattr(p, 'header') and p.header:
                                header = p.header
                                if hasattr(header, 'dataType') and header.dataType:
                                    dt = header.dataType
                                    if hasattr(dt, 'dimensions') and dt.dimensions:
                                        dim_str = str(dt.dimensions)
                                        match = re.search(r'\[(\d+):(\d+)\]', dim_str)
                                        if match:
                                            left = int(match.group(1))
                                            right = int(match.group(2))
                                            width = left - right + 1
                            
                            signals.append(Signal(name=name, module=mod_name, width=width))
                
                # Find data declarations
                data_decls = []
                def data_visitor(n):
                    if n.kind == pyslang.SyntaxKind.DataDeclaration:
                        data_decls.append(n)
                    return pyslang.VisitAction.Advance
                
                member.visit(data_visitor)
                
                for body_member in data_decls:
                    if hasattr(body_member, 'declarators') and body_member.declarators:
                        for decl in body_member.declarators:
                            if hasattr(decl, 'name') and decl.name:
                                name = str(decl.name).strip()
                                
                                # Get width
                                width = 1
                                if hasattr(body_member, 'type') and body_member.type:
                                    typ = body_member.type
                                    if hasattr(typ, 'dimensions') and typ.dimensions:
                                        dim_str = str(typ.dimensions)
                                        match = re.search(r'\[(\d+):(\d+)\]', dim_str)
                                        if match:
                                            left = int(match.group(1))
                                            right = int(match.group(2))
                                            width = left - right + 1
                                
                                signals.append(Signal(name=name, module=mod_name, width=width))
        
        return signals


def query_signals(source: str):
    """从源码文本查询信号。
    
    便捷函数，从源码字符串创建信号查询器。

    Args:
        source: SystemVerilog 源代码字符串
    
    Returns:
        SignalQuery: 查询器实例，失败返回 None
    """
    try:
        import pyslang
        tree = pyslang.SyntaxTree.fromText(source)
        
        class TextParser:
            def __init__(self, tree):
                self.trees = {"input.sv": tree}
                self.compilation = tree
        
        sq = SignalQuery(TextParser(tree))
        return sq
    except Exception as e:
        print(f"Signal query error: {e}")
        return None
