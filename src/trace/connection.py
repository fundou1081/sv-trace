"""Connection Tracer - 模块/接口连接追踪.

该模块分析 SystemVerilog 代码中的模块实例化和信号连接。

功能：
- 提取模块实例化信息
- 追踪端口连接关系
- 构建连接图

Example:
    >>> from parse import SVParser
    >>> from trace.connection import ConnectionTracer
    >>> p = SVParser()
    >>> ct = ConnectionTracer(p, verbose=True)
    >>> instances = ct.get_all_instances()
"""

import sys
import os
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, List, Optional
from dataclasses import dataclass, field
import pyslang

# 导入解析警告模块
from trace.parse_warn import (
    ParseWarningHandler, 
    warn_unsupported, 
    warn_error,
    WarningLevel
)


@dataclass
class Connection:
    """信号连接数据类
    
    Attributes:
        source: 源信号
        dest: 目标信号
        signal: 信号名
        port_name: 端口名
        instance_name: 实例名
    """
    source: str = ""
    dest: str = ""
    signal: str = ""
    port_name: str = ""
    instance_name: str = ""


@dataclass 
class Instance:
    """模块实例数据类
    
    Attributes:
        name: 实例名
        module_type: 模块类型
        connections: 连接列表
        parent_module: 父模块名
    """
    name: str = ""
    module_type: str = ""
    connections: List[Connection] = field(default_factory=list)
    parent_module: str = ""


class ConnectionTracer:
    """追踪模块实例和连接
    
    遍历 AST 提取模块实例化和端口连接信息。
    
    Attributes:
        instances: 实例列表
        instance_map: 实例名到实例的映射
        signal_connections: 信号到连接的映射
        warn_handler: 警告处理器
        
    Example:
        >>> ct = ConnectionTracer(parser, verbose=True)
        >>> for inst in ct.get_all_instances():
        ...     print(f"{inst.name}: {inst.module_type}")
    """
    
    # 支持的节点类型映射
    SUPPORTED_TYPES = {
        'HierarchyInstantiation': '模块层次化实例化',
        'ModuleDeclaration': '模块声明',
        'InterfaceDeclaration': '接口声明',
        'DataDeclaration': '数据声明',
        'NetDeclaration': '网络声明',
        'VariableDeclaration': '变量声明',
    }
    
    def __init__(self, parser, verbose: bool = True):
        """初始化连接追踪器
        
        Args:
            parser: SVParser 实例
            verbose: 是否打印警告信息
        """
        self.parser = parser
        self.verbose = verbose
        self.warn_handler = ParseWarningHandler(
            verbose=verbose, 
            component="ConnectionTracer"
        )
        self.instances: List[Instance] = []
        self.instance_map: Dict[str, Instance] = {}
        self.signal_connections: Dict[str, List[Connection]] = {}
        self._extract_all()
    
    def _extract_all(self) -> None:
        """从所有解析树提取连接信息"""
        for fname, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root') or not tree.root:
                self.warn_handler.warn_info(
                    f"文件 {fname} 解析树为空或无效",
                    context=fname
                )
                continue
            root = tree.root
            
            if hasattr(root, 'members') and root.members:
                members = self._to_list(root.members)
                for member in members:
                    kind_name = str(member.kind) if hasattr(member, 'kind') else ""
                    
                    if 'ModuleDeclaration' in kind_name:
                        self._extract_from_module(member, str(fname))
                    elif kind_name and kind_name != 'Unknown':
                        self._check_and_warn_unhandled(member, kind_name, str(fname))
    
    def _to_list(self, obj):
        """安全转换为列表"""
        if isinstance(obj, list):
            return obj
        if hasattr(obj, '__iter__') and not isinstance(obj, str):
            try:
                return list(obj)
            except:
                pass
        return []
    
    def _extract_from_module(self, module_node, source_file: str = "") -> None:
        """从模块节点提取信息
        
        Args:
            module_node: 模块 AST 节点
            source_file: 源文件
        """
        module_name = ""
        try:
            if hasattr(module_node, 'header') and module_node.header:
                if hasattr(module_node.header, 'name') and module_node.header.name:
                    module_name = str(module_node.header.name).strip()
            
            if hasattr(module_node, 'members') and module_node.members:
                members = self._to_list(module_node.members)
                for member in members:
                    self._extract_member(member, module_name, source_file)
                    
        except Exception as e:
            self.warn_handler.warn_error(
                "ModuleExtraction", e,
                context=f"模块 {module_name}",
                component="ConnectionTracer"
            )
    
    def _extract_member(self, member, parent_module: str, source_file: str = "") -> None:
        """提取成员节点
        
        Args:
            member: 成员 AST 节点
            parent_module: 父模块名
            source_file: 源文件
        """
        if member is None:
            return
        
        kind_name = str(member.kind) if hasattr(member, 'kind') else ""
        if not kind_name:
            return
        
        # 已处理的类型
        if 'HierarchyInstantiation' in kind_name:
            self._process_hierarchy_instantiation(member, parent_module)
            return
        
        # 递归检查子节点
        handled = False
        for attr in ['members', 'statements', 'body']:
            if hasattr(member, attr):
                child = getattr(member, attr)
                if child:
                    children = self._to_list(child)
                    if children:
                        handled = True
                        for c in children:
                            self._extract_member(c, parent_module, source_file)
        
        # 顶层成员未处理
        if not handled and kind_name not in ['Unknown', '']:
            self._check_and_warn_unhandled(member, kind_name, source_file)
    
    def _check_and_warn_unhandled(self, member, kind_name: str, 
                                 source_file: str = "") -> None:
        """检查并警告未处理的节点类型
        
        Args:
            member: AST 节点
            kind_name: 节点类型名
            source_file: 源文件
        """
        context = source_file
        if hasattr(member, 'name') and member.name:
            context += f" / {str(member.name)}"
        
        if hasattr(member, 'source') and member.source:
            try:
                loc = member.source
                if hasattr(loc, 'start') and loc.start:
                    context += f":{loc.start.line}"
            except:
                pass
        
        suggestions = {
            'InterfaceDeclaration': '尝试解析接口连接',
            'ClassDeclaration': 'class内部连接可能不完整',
            'PackageDeclaration': 'package级别连接不受支持',
            'ProgramDeclaration': 'program块连接可能不完整',
            'CovergroupDeclaration': 'covergroup不涉及连接',
            'PropertyDeclaration': 'property声明无连接',
            'SequenceDeclaration': 'sequence声明无连接',
            'ConstraintBlock': 'constraint块无模块连接',
            'ClockingBlock': 'clocking block连接不受支持',
            'ModportItem': 'modport信号连接可能不完整',
            'InterfacePortDeclaration': 'interface端口连接可能不完整',
        }
        
        suggestion = suggestions.get(kind_name, '请确认此语法是否影响连接分析')
        
        self.warn_handler.warn_unsupported(
            node_kind=kind_name,
            context=context,
            suggestion=suggestion,
            component="ConnectionTracer"
        )
    
    def _process_hierarchy_instantiation(self, inst_node, parent_module: str) -> None:
        """处理层次化实例
        
        Args:
            inst_node: 实例化 AST 节点
            parent_module: 父模块名
        """
        try:
            module_type = ""
            if hasattr(inst_node, 'type') and inst_node.type:
                module_type = str(inst_node.type).strip()
            
            if not module_type:
                return
            
            if hasattr(inst_node, 'instances') and inst_node.instances:
                for hier_inst in inst_node.instances:
                    self._process_hierarchical_instance(hier_inst, module_type, parent_module)
                    
        except Exception as e:
            self.warn_handler.warn_error(
                "HierarchyInstantiation", e,
                context=f"parent={parent_module}",
                component="ConnectionTracer"
            )
    
    def _process_hierarchical_instance(self, hier_inst, module_type: str, 
                                      parent_module: str) -> None:
        """处理层次化实例
        
        Args:
            hier_inst: 实例 AST 节点
            module_type: 模块类型
            parent_module: 父模块名
        """
        try:
            instance_name = ""
            if hasattr(hier_inst, 'decl') and hier_inst.decl:
                if hasattr(hier_inst.decl, 'name') and hier_inst.decl.name:
                    instance_name = str(hier_inst.decl.name).strip()
            
            if not instance_name:
                return
            
            inst = Instance(
                name=instance_name,
                module_type=module_type,
                parent_module=parent_module
            )
            self.instances.append(inst)
            self.instance_map[instance_name] = inst
            
            if hasattr(hier_inst, 'connections') and hier_inst.connections:
                self._extract_named_port_connections(hier_inst.connections, inst)
                    
        except Exception as e:
            self.warn_handler.warn_error(
                "HierarchicalInstance", e,
                context=f"instance={instance_name}",
                component="ConnectionTracer"
            )
    
    def _extract_named_port_connections(self, conn_node, inst: Instance) -> None:
        """提取命名端口连接
        
        Args:
            conn_node: 连接 AST 节点
            inst: Instance 对象
        """
        try:
            results = []
            
            def visitor(node):
                try:
                    if 'NamedPortConnection' in str(node.kind):
                        text = str(node).strip()
                        if text.startswith('.'):
                            text = text[1:]
                            parts = text.split('(', 1)
                            if len(parts) == 2:
                                port_name = parts[0].strip()
                                source = parts[1].rstrip(')').strip()
                                results.append((port_name, source))
                except Exception as e:
                    self.warn_handler.warn_error(
                        "NamedPortVisitor", e,
                        context=f"instance={inst.name}",
                        component="ConnectionTracer"
                    )
                return pyslang.VisitAction.Advance
            
            conn_node.visit(visitor)
            
            for port_name, source in results:
                conn_obj = Connection(
                    source=source,
                    dest=port_name,
                    signal=source,
                    port_name=port_name,
                    instance_name=inst.name
                )
                inst.connections.append(conn_obj)
                
                if source not in self.signal_connections:
                    self.signal_connections[source] = []
                self.signal_connections[source].append(conn_obj)
                
        except Exception as e:
            self.warn_handler.warn_error(
                "NamedPortExtraction", e,
                context=f"instance={inst.name}",
                component="ConnectionTracer"
            )
    
    def get_all_instances(self) -> List[Instance]:
        """获取所有实例
        
        Returns:
            List[Instance]: 实例列表
        """
        return self.instances
    
    def find_instance(self, name: str) -> Optional[Instance]:
        """查找实例（别名）"""
        return self.get_instance(name)

    def get_instance(self, name: str) -> Optional[Instance]:
        """获取指定名称的实例
        
        Args:
            name: 实例名
            
        Returns:
            Optional[Instance]: 实例对象，不存在则返回 None
        """
        return self.instance_map.get(name)
    
    def get_instances_by_type(self, module_type: str) -> List[Instance]:
        """获取指定类型的实例
        
        Args:
            module_type: 模块类型名
            
        Returns:
            List[Instance]: 实例列表
        """
        return [i for i in self.instances if i.module_type == module_type]
    
    def get_signal_connections(self, signal: str) -> List[Connection]:
        """获取信号的连接
        
        Args:
            signal: 信号名
            
        Returns:
            List[Connection]: 连接列表
        """
        return self.signal_connections.get(signal, [])
    
    def get_instance_inputs(self, instance_name: str) -> List[str]:
        """获取实例的输入信号
        
        Args:
            instance_name: 实例名
            
        Returns:
            List[str]: 输入信号列表
        """
        inst = self.instance_map.get(instance_name)
        if not inst:
            return []
        return [c.source for c in inst.connections if c.source]
    
    def get_instance_outputs(self, instance_name: str) -> List[str]:
        """获取实例的输出信号
        
        Args:
            instance_name: 实例名
            
        Returns:
            List[str]: 输出信号列表
        """
        inst = self.instance_map.get(instance_name)
        if not inst:
            return []
        return [c.dest for c in inst.connections if c.dest]
    
    def get_warning_report(self) -> str:
        """获取警告报告
        
        Returns:
            str: 警告报告字符串
        """
        return self.warn_handler.get_report()
    
    def print_warning_report(self) -> None:
        """打印警告报告到标准输出"""
        self.warn_handler.print_report()


def trace_connections(parser, verbose: bool = True) -> ConnectionTracer:
    """追踪连接的便捷函数
    
    Args:
        parser: SVParser 实例
        verbose: 是否打印警告
        
    Returns:
        ConnectionTracer: 连接追踪器实例
    """
    return ConnectionTracer(parser, verbose=verbose)
