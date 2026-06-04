"""signal_tracer.port_resolver - 语法层端口连接解析器

通过解析 SyntaxTree 获取模块实例的端口连接关系。

端口连接信息在语义层不可用，必须从语法层解析。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
# M5.1h fix: pyslang 11 把 SyntaxTree 移到了 pyslang.syntax 子模块
# 尝试新位置, fallback 到旧位置 (兼容 v10 和 v11+)
try:
    from pyslang.syntax import SyntaxTree
except ImportError:
    from pyslang import SyntaxTree


@dataclass
class PortConnection:
    """一个端口的连接信息"""
    instance_name: str           # 实例名称 (如 'u_dut')
    instance_path: str # 完整实例路径 (如 'top.u_dut')
    port_name: str              # 端口名称 (如 'data_in')
    connected_signal: str      # 连接的信号名称 (如 'sig_in')
    line: int = 0              # 连接语句行号 (1-indexed)
    
    def __repr__(self) -> str:
        return f"{self.instance_path}.{self.port_name} -> {self.connected_signal}"


@dataclass 
class InstanceConnection:
    """一个模块实例的所有端口连接"""
    instance_name: str          # 实例名称
    instance_path: str          # 完整路径
    module_name: str # 模块名称 (dut)
    connections: List[PortConnection] = field(default_factory=list)
    
    def get_port_signal(self, port_name: str) -> Optional[str]:
        """获取指定端口连接的信号名"""
        for conn in self.connections:
            if conn.port_name == port_name:
                return conn.connected_signal
        return None


class PortResolver:
    """端口连接解析器 - 通过语法层解析"""
    
    def __init__(self, sv_code: str):
        self._sv_code = sv_code
        self._tree: SyntaxTree = None
        self._instances: List[InstanceConnection] = []
        self._module_stack: List[str] = []  # 模块名栈
    
    def build(self) -> 'PortResolver':
        """构建端口连接索引"""
        self._tree = SyntaxTree.fromText(self._sv_code)
        self._instances = []
        self._module_stack = []
        
        # Walk the syntax tree to find port connections
        self._walk_syntax_tree(self._tree.root)
        
        return self
    
    def _walk_syntax_tree(self, node, depth=0):
        """递归遍历语法树"""
        if not hasattr(node, 'kind'):
            return
        
        kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
        
        # Track current module
        if 'ModuleDeclaration' in kind_name:
            self._process_module_declaration(node)
        
        # Found a hierarchy instantiation
        if 'HierarchyInstantiation' in kind_name:
            self._process_instantiation(node)
        
        # Continue walking children
        if hasattr(node, '__iter__'):
            try:
                for child in node:
                    self._walk_syntax_tree(child, depth+1)
            except:
                pass
    
    def _process_module_declaration(self, node):
        """处理模块声明，提取模块名"""
        header = getattr(node, 'header', None)
        if header:
            for child in header:
                if hasattr(child, 'kind') and 'Identifier' in child.kind.name:
                    # Module name is in valueText of Token
                    if hasattr(child, 'valueText'):
                        module_name = getattr(child, 'valueText', '') or ''
                    else:
                        module_name = ''
                    
                    if module_name:
                        self._module_stack.append(module_name)
                    break
    
    def _process_instantiation(self, node):
        """处理模块实例化，提取端口连接"""
        # Get the module type name from Identifier child (not Token)
        module_name = ''
        for child in node:
            child_kn = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            if child_kn == 'Identifier':
                # This is the module name
                if hasattr(child, 'valueText'):
                    module_name = getattr(child, 'valueText', '') or ''
                break
        
        # Use instances attribute to get the instance container
        inst_container = getattr(node, 'instances', None)
        if not inst_container:
            return
        
        # Iterate over inst_container to get HierarchicalInstance items
        for item in inst_container:
            if not hasattr(item, 'kind') or 'HierarchicalInstance' not in item.kind.name:
                continue
            
            # Extract instance name from InstanceName Token
            instance_name = ''
            for child in item:
                if hasattr(child, 'kind') and 'InstanceName' in child.kind.name:
                    # InstanceName contains the name token
                    for token_child in child:
                        if hasattr(token_child, 'valueText'):
                            instance_name = getattr(token_child, 'valueText', '') or ''
                            break
                    break
            
            if not instance_name:
                continue
            
            # Build instance path (parent module + instance name)
            if self._module_stack:
                parent_module = self._module_stack[-1]
                instance_path = f"{parent_module}.{instance_name}"
            else:
                instance_path = instance_name
            
            # Get line number from source range
            line = 1
            sr = getattr(item, 'sourceRange', None)
            if sr and hasattr(sr, 'start') and hasattr(sr.start, 'line'):
                line = sr.start.line + 1  # Convert to 1-indexed
            
            # Find port connections in SeparatedList
            connections = []
            for child in item:
                if hasattr(child, 'kind') and 'SeparatedList' in child.kind.name:
                    # This contains the NamedPortConnection items
                    for port_conn in child:
                        if hasattr(port_conn, 'kind') and 'NamedPortConnection' in port_conn.kind.name:
                            conn = self._process_named_port_connection(port_conn, instance_path)
                            if conn:
                                connections.append(conn)
            
            if connections:
                inst_conn = InstanceConnection(
                    instance_name=instance_name,
                    instance_path=instance_path,
                    module_name=module_name,
                    connections=connections,
                )
                self._instances.append(inst_conn)
    
    def _get_signal_name_from_expr(self, expr):
        """从表达式中提取信号名称
        
        NamedPortConnection.expr 结构:
        SimplePropertyExprSyntax
          -> SimpleSequenceExprSyntax
              -> IdentifierNameSyntax
                  -> identifier: Token (valueText = signal_name)
        """
        # Navigate through the expression tree
        if not expr:
            return ''
        
        # Try SimplePropertyExprSyntax -> SimpleSequenceExprSyntax -> IdentifierNameSyntax
        seq_expr = None
        for child in expr:
            if hasattr(child, 'kind') and 'SimpleSequence' in child.kind.name:
                seq_expr = child
                break
        
        if not seq_expr:
            # Try direct Token
            if hasattr(expr, 'valueText'):
                return getattr(expr, 'valueText', '') or ''
            return ''
        
        # Find IdentifierNameSyntax
        for child in seq_expr:
            if hasattr(child, 'kind') and 'IdentifierName' in child.kind.name:
                ident = getattr(child, 'identifier', None)
                if ident and hasattr(ident, 'valueText'):
                    return getattr(ident, 'valueText', '') or ''
        
        return ''
    
    def _process_named_port_connection(self, node, instance_path: str) -> Optional[PortConnection]:
        """处理一个命名端口连接 .port_name(signal)"""
        # port_name might be a Token or a string
        port_name_raw = getattr(node, 'name', None)
        if port_name_raw is None:
            return None
        
        if hasattr(port_name_raw, 'valueText'):
            port_name = getattr(port_name_raw, 'valueText', '') or ''
        elif isinstance(port_name_raw, str):
            port_name = port_name_raw
        else:
            port_name = str(port_name_raw)
        
        if not port_name:
            return None
        
        # Get connected signal from expr
        connected_signal = self._get_signal_name_from_expr(getattr(node, 'expr', None))
        
        # Get line number
        line = 1
        sr = getattr(node, 'sourceRange', None)
        if sr and hasattr(sr, 'start') and hasattr(sr.start, 'line'):
            line = sr.start.line + 1
        
        return PortConnection(
            instance_name=instance_path.split('.')[-1],
            instance_path=instance_path,
            port_name=port_name,
            connected_signal=connected_signal,
            line=line,
        )
    
    def get_instance(self, instance_path: str) -> Optional[InstanceConnection]:
        """根据路径获取实例连接信息"""
        for inst in self._instances:
            if inst.instance_path == instance_path:
                return inst
        return None
    
    def get_signal_connections(self, signal_name: str) -> List[PortConnection]:
        """查找连接到某个信号的所有端口"""
        results = []
        for inst in self._instances:
            for conn in inst.connections:
                if conn.connected_signal == signal_name:
                    results.append(conn)
        return results
    
    @property
    def instances(self) -> List[InstanceConnection]:
        """获取所有实例连接"""
        return self._instances


def resolve_ports(sv_code: str) -> List[InstanceConnection]:
    """解析 SV 代码中的所有端口连接"""
    resolver = PortResolver(sv_code)
    resolver.build()
    return resolver.instances