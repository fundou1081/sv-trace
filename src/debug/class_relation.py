"""ClassRelationExtractor - SystemVerilog 类关系与方法调用图提取器。

提取类之间的关系和方法调用图：
- 类继承关系
- 类实例化关系
- 方法调用关系
- 依赖图

Example:
    >>> from debug.class_relation import ClassRelationExtractor
    >>> from debug.class_extractor import ClassExtractor
    >>> ce = ClassExtractor(parser)
    >>> cre = ClassRelationExtractor(parser, ce)
    >>> for rel in cre.relations:
    ...     print(f"{rel.from_class} -> {rel.to_class} ({rel.relation_type})")
    >>> print(cre.get_dependency_graphviz())
"""
import sys
import re
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field

from .class_info import ClassInfo
from .class_extractor import ClassExtractor


@dataclass
class MethodCallInfo:
    """方法调用信息数据类。
    
    Attributes:
        caller_name: 调用者名（类名或模块名）
        method_name: 被调用的方法名
        full_call: 完整调用字符串
        is_internal: 是否为内部调用
        is_super_call: 是否为 super:: 调用
        is_this_call: 是否为 this:: 调用
        line_number: 行号
        file_name: 文件名
        constraint_name: 约束名（如果是约束中的调用）
    """
    caller_name: str
    method_name: str
    full_call: str
    is_internal: bool = False
    is_super_call: bool = False
    is_this_call: bool = False
    line_number: int = 0
    file_name: str = ""
    constraint_name: str = ""


@dataclass
class ClassRelationInfo:
    """类关系信息数据类。
    
    Attributes:
        from_class: 源类名
        to_class: 目标类名
        relation_type: 关系类型 (extends/instantiates/uses)
        details: 详细信息
        line_number: 行号
        is_instantiated: 是否为实例化
        instantiation_context: 实例化上下文
    """
    from_class: str
    to_class: str
    relation_type: str
    details: str = ""
    line_number: int = 0
    is_instantiated: bool = False  # True if new() called
    instantiation_context: str = ""


@dataclass
class MethodDefinition:
    """方法定义信息数据类。
    
    Attributes:
        class_name: 所属类名
        name: 方法名
        is_function: 是否为 function
        is_virtual: 是否为虚方法
        is_pure: 是否为纯虚方法
        is_static: 是否为静态方法
        return_type: 返回类型
        arguments: 参数列表
    """
    class_name: str
    name: str
    is_function: bool = True
    is_virtual: bool = False
    is_pure: bool = False
    is_static: bool = False
    return_type: str = ""
    arguments: str = ""


class ClassRelationExtractor:
    """类关系与方法调用图提取器。
    
    提取 SystemVerilog 类之间的继承、实例化、使用关系，
    以及方法调用图。

    Attributes:
        parser: SVParser 实例
        class_extractor: 类提取器
        classes: 类信息字典
        relations: 类关系列表
        method_calls: 方法调用列表
        method_definitions: 方法定义字典
        global_functions: 全局函数字典
        global_tasks: 全局任务集合
        dependency_graph: 依赖图
    
    Example:
        >>> cre = ClassRelationExtractor(parser, ce)
        >>> print(cre.get_dependency_graphviz())
    """
    
    def __init__(self, parser, class_extractor: ClassExtractor):
        """初始化提取器。
        
        Args:
            parser: SVParser 实例
            class_extractor: ClassExtractor 实例
        """
        self.parser = parser
        self.class_extractor = class_extractor
        self.classes: Dict[str, ClassInfo] = class_extractor.classes
        self.relations: List[ClassRelationInfo] = []
        self.method_calls: List[MethodCallInfo] = []
        self.method_definitions: Dict[str, List[MethodDefinition]] = {}
        self.global_functions: Dict[str, str] = {}
        self.global_tasks: Set[str] = set()
        self.dependency_graph: Dict[str, List[str]] = {}
        self._extract_all()
    
    def _extract_all(self):
        """提取所有关系和调用。"""
        for fname, tree in self.parser.trees.items():
            self._extract_from_tree(tree, fname)
    
    def _extract_from_tree(self, tree, filename: str):
        """从语法树提取关系。
        
        Args:
            tree: SyntaxTree 对象
            filename: 文件名
        """
        root = tree.root
        if not hasattr(root, 'members') or not root.members:
            return
        
        current_class = None
        current_module = None
        
        for i in range(len(root.members)):
            member = root.members[i]
            member_type = type(member).__name__
            
            if 'ModuleDeclaration' in member_type:
                current_module = self._get_module_name(member)
                self._process_module_members(member, filename, current_class, current_module)
            elif 'ClassDeclaration' in member_type:
                cls_name = self._get_name(member.name)
                old_class = current_class
                current_class = cls_name
                
                if cls_name not in self.method_definitions:
                    self.method_definitions[cls_name] = []
                
                if hasattr(member, 'items') and member.items:
                    self._process_class_items(member.items, cls_name, filename)
                
                self._extract_class_relations(member, cls_name, filename)
                current_class = old_class
    
    def _get_module_name(self, module_node) -> str:
        """获取模块名。
        
        Args:
            module_node: 模块节点
        
        Returns:
            str: 模块名
        """
        if hasattr(module_node, 'header') and module_node.header:
            header = module_node.header
            if hasattr(header, 'name') and header.name:
                name_val = header.name
                if hasattr(name_val, 'value'):
                    return str(name_val.value).strip()
                return str(name_val).strip()
        return ""
    
    def _process_module_members(self, module, filename: str, current_class: str, current_module: str):
        """处理模块成员。
        
        Args:
            module: 模块节点
            filename: 文件名
            current_class: 当前类名
            current_module: 当前模块名
        """
        if not hasattr(module, 'members') or not module.members:
            return
        
        for j in range(len(module.members)):
            stmt = module.members[j]
            if stmt is None:
                continue
            self._analyze_statement_recursive(stmt, current_class, current_module, filename)
    
    def _process_class_items(self, items, class_name: str, filename: str):
        """处理类成员。
        
        Args:
            items: 类项列表
            class_name: 类名
            filename: 文件名
        """
        for item in items:
            if item is None:
                continue
            item_type = type(item).__name__
            
            if 'Method' in item_type:
                self._extract_method_definition(item, class_name)
                # Extract method calls from method body
                if hasattr(item, 'body') and item.body:
                    self._extract_calls_from_statement(item.body, class_name, filename)
                elif hasattr(item, 'statement') and item.statement:
                    self._extract_calls_from_statement(item.statement, class_name, filename)
            
            elif 'Constraint' in item_type:
                if hasattr(item, 'block') and item.block:
                    self._extract_calls_from_statement(item.block, class_name, filename, constraint_name=getattr(item, 'name', ''))
    
    def _extract_method_definition(self, method_node, class_name: str):
        """提取方法定义。
        
        Args:
            method_node: 方法节点
            class_name: 类名
        """
        try:
            method_def = MethodDefinition(class_name=class_name, name="")
            
            decl = method_node
            if hasattr(method_node, 'declaration') and method_node.declaration:
                decl = method_node.declaration
            
            proto = decl
            if hasattr(decl, 'prototype') and decl.prototype:
                proto = decl.prototype
            
            if proto is None:
                return
            
            if hasattr(proto, 'name') and proto.name:
                method_def.name = str(proto.name).strip()
            
            if not method_def.name:
                return
            
            # Get qualifiers
            if hasattr(method_node, 'qualifiers') and method_node.qualifiers:
                quals_str = str(method_node.qualifiers).lower()
                method_def.is_virtual = 'virtual' in quals_str
                method_def.is_pure = 'pure' in quals_str
                method_def.is_static = 'static' in quals_str
            
            method_def.is_function = 'function' in str(type(method_node)).lower()
            
            # Get return type
            if hasattr(proto, 'returnType') and proto.returnType:
                method_def.return_type = str(proto.returnType).strip()
            
            # Get arguments
            if hasattr(proto, 'portList') and proto.portList:
                method_def.arguments = f"({proto.portList})"
            
            self.method_definitions.setdefault(class_name, []).append(method_def)
            
        except Exception as e:
            print(f"Error extracting method definition: {e}")
    
    def _extract_calls_from_statement(self, stmt, class_name: str, filename: str, constraint_name: str = ""):
        """从语句中提取方法调用。
        
        Args:
            stmt: 语句节点
            class_name: 类名
            filename: 文件名
            constraint_name: 约束名
        """
        if stmt is None:
            return
        
        try:
            stmt_str = str(stmt)
            
            # Pattern: object.method()
            pattern = r'(\w+)\.(\w+)\s*\('
            matches = re.findall(pattern, stmt_str)
            
            for obj_name, method_name in matches:
                if obj_name in ('this', 'super', 'null'):
                    continue
                
                is_internal = obj_name in self.classes
                is_super = False
                is_this = False
                
                full_call = f"{obj_name}.{method_name}()"
                
                call_info = MethodCallInfo(
                    caller_name=class_name,
                    method_name=method_name,
                    full_call=full_call,
                    is_internal=is_internal,
                    is_super_call=is_super,
                    is_this_call=is_this,
                    file_name=filename,
                    constraint_name=constraint_name
                )
                self.method_calls.append(call_info)
            
            # Recursively process child statements
            for attr_name in ['statement', 'consequent', 'alternate', 'body', 'statements', 'items']:
                if hasattr(stmt, attr_name):
                    child = getattr(stmt, attr_name)
                    if child:
                        if isinstance(child, list):
                            for c in child:
                                self._extract_calls_from_statement(c, class_name, filename, constraint_name)
                        else:
                            self._extract_calls_from_statement(child, class_name, filename, constraint_name)
                            
        except Exception as e:
            pass
    
    def _analyze_statement_recursive(self, stmt, class_name: str, module_name: str, filename: str):
        """递归分析语句。
        
        Args:
            stmt: 语句节点
            class_name: 类名
            module_name: 模块名
            filename: 文件名
        """
        if stmt is None:
            return
        
        try:
            stmt_str = str(stmt)
            
            # Pattern: object.method()
            pattern = r'(\w+)\.(\w+)\s*\('
            matches = re.findall(pattern, stmt_str)
            
            for obj_name, method_name in matches:
                if obj_name in ('this', 'super', 'null'):
                    continue
                
                is_internal = obj_name in self.classes
                caller = class_name if class_name else module_name
                
                call_info = MethodCallInfo(
                    caller_name=caller,
                    method_name=method_name,
                    full_call=f"{obj_name}.{method_name}()",
                    is_internal=is_internal,
                    file_name=filename
                )
                self.method_calls.append(call_info)
            
            # Process child statements
            for attr_name in ['statement', 'consequent', 'alternate', 'body', 'statements', 'items']:
                if hasattr(stmt, attr_name):
                    child = getattr(stmt, attr_name)
                    if child:
                        if isinstance(child, list):
                            for c in child:
                                self._analyze_statement_recursive(c, class_name, module_name, filename)
                        else:
                            self._analyze_statement_recursive(child, class_name, module_name, filename)
                            
        except Exception:
            pass
    
    def _extract_class_relations(self, class_node, class_name: str, filename: str):
        """提取类关系。
        
        Args:
            class_node: 类节点
            class_name: 类名
            filename: 文件名
        """
        # Check extends
        if hasattr(class_node, 'header') and class_node.header:
            if hasattr(class_node.header, 'extends') and class_node.header.extends:
                extends_name = self._get_name(class_node.header.extends.name)
                if extends_name:
                    rel = ClassRelationInfo(
                        from_class=class_name,
                        to_class=extends_name,
                        relation_type='extends',
                        file_name=filename
                    )
                    self.relations.append(rel)
    
    def _get_name(self, name_node) -> str:
        """从节点获取名称。
        
        Args:
            name_node: 名称节点
        
        Returns:
            str: 名称字符串
        """
        if not name_node:
            return ""
        if hasattr(name_node, 'value'):
            return str(name_node.value).strip()
        return str(name_node).strip()
    
    def get_class_relations(self, class_name: str) -> List[ClassRelationInfo]:
        """获取类的所有关系。
        
        Args:
            class_name: 类名
        
        Returns:
            List[ClassRelationInfo]: 关系列表
        """
        return [r for r in self.relations if r.from_class == class_name or r.to_class == class_name]
    
    def get_method_calls(self, class_name: str = None) -> List[MethodCallInfo]:
        """获取方法调用。
        
        Args:
            class_name: 可选的类名过滤
        
        Returns:
            List[MethodCallInfo]: 调用列表
        """
        if class_name:
            return [c for c in self.method_calls if c.caller_name == class_name]
        return self.method_calls
    
    def get_callers_of_method(self, method_name: str) -> List[MethodCallInfo]:
        """获取调用指定方法的所有调用者。
        
        Args:
            method_name: 方法名
        
        Returns:
            List[MethodCallInfo]: 调用列表
        """
        return [c for c in self.method_calls if c.method_name == method_name]
    
    def get_callees_of_method(self, class_name: str, method_name: str) -> List[str]:
        """获取方法调用的其他方法。
        
        Args:
            class_name: 类名
            method_name: 方法名
        
        Returns:
            List[str]: 被调用的方法名列表
        """
        callees = []
        for call in self.method_calls:
            if call.caller_name == class_name and call.method_name != method_name:
                callees.append(call.method_name)
        return list(set(callees))
    
    def build_dependency_graph(self):
        """构建依赖图。"""
        self.dependency_graph = {}
        
        for rel in self.relations:
            if rel.relation_type == 'extends':
                self.dependency_graph.setdefault(rel.from_class, []).append(rel.to_class)
            elif rel.relation_type == 'instantiates':
                self.dependency_graph.setdefault(rel.from_class, []).append(rel.to_class)
    
    def get_dependency_graphviz(self) -> str:
        """生成 Graphviz 格式的依赖图。
        
        Returns:
            str: Graphviz DOT 格式字符串
        """
        self.build_dependency_graph()
        
        lines = ["digraph class_dependencies {"]
        lines.append("  rankdir=BT;")
        lines.append("  node [shape=box];")
        
        for cls, deps in self.dependency_graph.items():
            for dep in deps:
                lines.append(f'  "{cls}" -> "{dep}";')
        
        lines.append("}")
        return "\n".join(lines)
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """查找循环依赖。
        
        Returns:
            List[List[str]]: 循环路径列表
        """
        cycles = []
        visited = set()
        path = []
        
        def dfs(cls, start):
            if cls in path:
                cycle_start = path.index(cls)
                cycle = path[cycle_start:] + [cls]
                if cycle not in cycles:
                    cycles.append(cycle)
                return
            
            if cls in visited:
                return
            
            visited.add(cls)
            path.append(cls)
            
            for dep in self.dependency_graph.get(cls, []):
                dfs(dep, start)
            
            path.pop()
        
        for cls in self.dependency_graph:
            dfs(cls, cls)
        
        return cycles
