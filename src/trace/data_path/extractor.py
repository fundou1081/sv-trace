"""RTL Data Path Extractor

从RTL提取数据通路元素:
- 操作单元(ADD, MUL, MUX, etc.)
- 数据流边
- 控制信号
- 时序/组合逻辑边界

增强版: 添加解析警告，显式打印不支持的语法结构
"""

import re
from typing import Dict, List, Set, Tuple, Any, Optional
from dataclasses import dataclass

from trace.parse_warn import (
    ParseWarningHandler,
    warn_unsupported,
    warn_error,
    WarningLevel
)


@dataclass
class DataPathNode:
    """数据通路节点"""
    name: str
    node_type: str  # 'operator', 'register', 'mux', 'fifo', 'signal'
    width: int = 0
    line: int = 0
    modules: List[str] = None
    
    def __post_init__(self):
        if self.modules is None:
            self.modules = []


@dataclass
class DataPathEdge:
    """数据通路边 / 数据流"""
    src: str
    dst: str
    edge_type: str  # 'data', 'control', 'valid'
    condition: str = ""  # MUX selection condition
    width: int = 0


class DataPathExtractor:
    """从RTL提取数据通路
    
    增强: 解析过程中显式打印不支持的语法结构
    """
    
    # 操作符映射
    OPERATORS = {
        'add': 'ADD', '+': 'ADD',
        'sub': 'SUB', '-': 'SUB', 
        'mul': 'MUL', '*': 'MUL',
        'div': 'DIV', '/': 'DIV',
        'shl': 'SHL', '>>': 'SHL',
        'shr': 'SHR', '<<': 'SHR',
        'and': 'AND', '&': 'AND',
        'or': 'OR', '|': 'OR',
        'xor': 'XOR', '^': 'XOR',
        'compare': 'CMP', '==': 'CMP', '!=': 'CMP',
        'mux': 'MUX',
    }
    
    # 不支持的语法类型
    UNSUPPORTED_NODE_TYPES = {
        'CovergroupDeclaration': '覆盖率group不支持',
        'PropertyDeclaration': 'property声明不支持',
        'SequenceDeclaration': 'sequence声明不支持',
        'ClassDeclaration': 'class声明不支持',
        'ConstraintBlock': '约束块不支持',
        'ClockingBlock': 'clocking block不支持',
        'RandSequenceExpression': 'rand sequence不支持',
    }
    
    def __init__(self, parser, verbose: bool = True):
        self.parser = parser
        self.verbose = verbose
        # 创建警告处理器
        self.warn_handler = ParseWarningHandler(
            verbose=verbose,
            component="DataPathExtractor"
        )
        self.nodes: Dict[str, DataPathNode] = {}
        self.edges: List[DataPathEdge] = []
        self._unsupported_nodes: List[str] = []
        self._extract()
    
    def _extract(self):
        """提取数据通路"""
        try:
            # 检查是否有class提取器
            if hasattr(self.parser, 'trees'):
                for fname, tree in self.parser.trees.items():
                    if tree and hasattr(tree, 'root'):
                        self._extract_from_tree(tree.root, fname)
            else:
                self.warn_handler.warn_unsupported(
                    "UnknownParserType",
                    context=type(self.parser).__name__,
                    suggestion="请使用pyslang解析树",
                    component="DataPathExtractor"
                )
        except Exception as e:
            self.warn_handler.warn_error(
                "DataPathExtraction",
                e,
                context="整体提取",
                component="DataPathExtractor"
            )
    
    def _extract_from_tree(self, root, source: str = ""):
        """从解析树提取"""
        if not root:
            return
        
        # 遍历顶层成员
        if hasattr(root, 'members') and root.members:
            members = self._to_list(root.members)
            for member in members:
                self._process_member(member, source)
    
    def _to_list(self, obj):
        if isinstance(obj, list):
            return obj
        if hasattr(obj, '__iter__') and not isinstance(obj, str):
            try:
                return list(obj)
            except:
                pass
        return []
    
    def _process_member(self, member, source: str = ""):
        """处理成员节点"""
        if member is None:
            return
        
        kind_name = str(member.kind) if hasattr(member, 'kind') else ""
        
        # 检查是否是不支持的类型
        if kind_name in self.UNSUPPORTED_NODE_TYPES:
            self.warn_handler.warn_unsupported(
                kind_name,
                context=source,
                suggestion=self.UNSUPPORTED_NODE_TYPES[kind_name],
                component="DataPathExtractor"
            )
            self._unsupported_nodes.append(kind_name)
            return
        
        # 处理支持的类型
        if 'ModuleDeclaration' in kind_name:
            self._extract_from_module(member, source)
        elif 'DataDeclaration' in kind_name or 'NetDeclaration' in kind_name:
            self._extract_from_declaration(member)
        else:
            # 递归处理子节点
            handled = False
            for attr in ['members', 'statements', 'body']:
                if hasattr(member, attr):
                    child = getattr(member, attr)
                    if child:
                        children = self._to_list(child)
                        if children:
                            handled = True
                            for c in children:
                                self._process_member(c, source)
            
            # 如果没有子节点且是未知类型，打印警告
            if not handled and kind_name and kind_name not in ['Unknown', '']:
                self.warn_handler.warn_unsupported(
                    kind_name,
                    context=source,
                    suggestion="可能影响数据通路提取完整性",
                    component="DataPathExtractor"
                )
    
    def _extract_from_module(self, module_node, source: str = ""):
        """从模块提取"""
        module_name = ""
        try:
            if hasattr(module_node, 'header') and module_node.header:
                if hasattr(module_node.header, 'name') and module_node.header.name:
                    module_name = str(module_node.header.name).strip()
            
            if hasattr(module_node, 'members') and module_node.members:
                members = self._to_list(module_node.members)
                for member in members:
                    self._process_member(member, f"{source}/{module_name}")
        except Exception as e:
            self.warn_handler.warn_error(
                "ModuleExtraction",
                e,
                context=f"模块 {module_name}",
                component="DataPathExtractor"
            )
    
    def _extract_from_declaration(self, decl_node):
        """从声明提取"""
        try:
            # 提取变量名
            if hasattr(decl_node, 'declarators') and decl_node.declarators:
                for decl in self._to_list(decl_node.declarators):
                    if hasattr(decl, 'name'):
                        name = str(decl.name)
                        width = 1
                        if hasattr(decl, 'dimensions') and decl.dimensions:
                            # 尝试获取位宽
                            pass
                        
                        node_type = 'REGISTER' if 'reg' in str(decl_node.kind).lower() else 'SIGNAL'
                        self._add_node(name, node_type, 0, width)
        except Exception as e:
            self.warn_handler.warn_error(
                "DeclarationExtraction",
                e,
                context="变量声明",
                component="DataPathExtractor"
            )
    
    def _get_classes(self):
        """获取class列表"""
        from debug.class_extractor import ClassExtractor
        extractor = ClassExtractor(self.parser)
        return extractor.classes
    
    def _extract_from_class(self, class_name: str, cls):
        """从class提取数据通路"""
        # 添加操作符
        for method in cls.methods:
            node_type = self._get_operator_type(method.prototype)
            if node_type:
                self._add_node(method.name, node_type, cls.line_number if hasattr(cls, 'line_number') else 0)
        
        # 添加属性作为寄存器/信号
        for prop in cls.properties:
            node_type = 'REGISTER' if prop.rand_mode in ('rand', 'randc') else 'SIGNAL'
            self._add_node(prop.name, node_type, 0, prop.width if hasattr(prop, 'width') else 0)
    
    def _get_operator_type(self, proto: str) -> Optional[str]:
        """识别操作符类型"""
        for keyword, op_type in self.OPERATORS.items():
            if keyword in proto.lower():
                return op_type
        return None
    
    def _add_node(self, name: str, node_type: str, line: int = 0, width: int = 0):
        """添加节点"""
        full_name = f"{name}"  # 可以加class前缀
        if full_name not in self.nodes:
            self.nodes[full_name] = DataPathNode(full_name, node_type, width, line)
    
    def build_edges(self) -> List[DataPathEdge]:
        """构建数据流边"""
        try:
            from debug.constraint_parser_v2 import parse_constraints
            cp = parse_constraints(self.parser)
            
            for const in cp.constraints.values():
                # 变量之间的依赖 = 数据流
                for var in const.variables:
                    if var.name in self.nodes:
                        edge = DataPathEdge(
                            src=var.name,
                            dst=const.name,
                            edge_type='data'
                        )
                        self.edges.append(edge)
        except ImportError:
            self.warn_handler.warn_unsupported(
                "ConstraintParserNotFound",
                context="build_edges",
                suggestion="debug.constraint_parser_v2 不可用",
                component="DataPathExtractor"
            )
        except Exception as e:
            self.warn_handler.warn_error(
                "EdgeBuilding",
                e,
                context="build_edges",
                component="DataPathExtractor"
            )
        
        return self.edges
    
    def get_summary(self) -> str:
        """返回摘要"""
        by_type = {}
        for node in self.nodes.values():
            by_type[node.node_type] = by_type.get(node.node_type, 0) + 1
        
        lines = ["Data Path Extraction Summary", "=" * 40]
        lines.append(f"Total nodes: {len(self.nodes)}")
        lines.append(f"Total edges: {len(self.edges)}")
        lines.append(f"Unsupported types encountered: {len(set(self._unsupported_nodes))}")
        
        if by_type:
            lines.append("\nBy type:")
            for t, c in sorted(by_type.items()):
                lines.append(f"  {t}: {c}")
        
        if self._unsupported_nodes:
            lines.append(f"\n⚠️ Unsupported node types: {set(self._unsupported_nodes)}")
        
        return "\n".join(lines)
    
    def get_warning_report(self) -> str:
        """获取警告报告"""
        return self.warn_handler.get_report()
    
    def print_warning_report(self):
        """打印警告报告"""
        self.warn_handler.print_report()


def extract_data_path(parser, verbose: bool = True) -> DataPathExtractor:
    """便捷函数"""
    return DataPathExtractor(parser, verbose=verbose)
