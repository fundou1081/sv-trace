"""ClassUsage - SystemVerilog 类实例追踪器。

追踪模块中的类实例化和使用情况。

Example:
    >>> from debug.class_usage import ClassInstantiationTracer
    >>> from debug.class_extractor import ClassExtractor
    >>> ce = ClassExtractor(parser)
    >>> tracer = ClassInstantiationTracer(parser, ce)
    >>> instances = tracer.get_all_instances_of_class("Packet")
    >>> print(f"Found {len(instances)} instances")
"""
import sys
import re
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field

from .class_info import ClassInfo
from .class_extractor import ClassExtractor


@dataclass
class ClassInstanceInfo:
    """类实例信息数据类。
    
    Attributes:
        instance_name: 实例名
        class_name: 类名
        handle_type: 句柄类型 (handle/new/null)
        constructor_args: 构造参数列表
        line_number: 行号
        file_name: 文件名
    """
    instance_name: str
    class_name: str
    handle_type: str = "handle"  # handle, null, new
    constructor_args: List[str] = field(default_factory=list)
    line_number: int = 0
    file_name: str = ""


@dataclass
class ClassUsageInfo:
    """类的使用信息数据类。
    
    Attributes:
        module_name: 模块名
        instances: 实例列表
        method_calls: 方法调用列表
    """
    module_name: str
    instances: List[ClassInstanceInfo] = field(default_factory=list)
    method_calls: List[str] = field(default_factory=list)


class ClassInstantiationTracer:
    """类实例化追踪器。
    
    追踪模块中的类实例化和方法调用。

    Attributes:
        parser: SVParser 实例
        class_extractor: 类提取器
        classes: 类信息字典
        usages: 模块使用信息字典
    
    Example:
        >>> tracer = ClassInstantiationTracer(parser, ce)
        >>> usages = tracer.get_all_instances_of_class("Packet")
    """
    
    def __init__(self, parser, class_extractor: ClassExtractor):
        """初始化追踪器。
        
        Args:
            parser: SVParser 实例
            class_extractor: ClassExtractor 实例
        """
        self.parser = parser
        self.class_extractor = class_extractor
        self.classes: Dict[str, ClassInfo] = class_extractor.classes
        self.usages: Dict[str, ClassUsageInfo] = {}
        self._trace_usages()
    
    def _trace_usages(self):
        """追踪所有使用情况。"""
        for fname, tree in self.parser.trees.items():
            self._scan_tree_for_usage(tree, fname)
    
    def _scan_tree_for_usage(self, tree, filename: str):
        """扫描语法树查找类实例。
        
        Args:
            tree: 语法树
            filename: 文件名
        """
        root = tree.root
        
        if not hasattr(root, 'members') or not root.members:
            return
        
        for i in range(len(root.members)):
            member = root.members[i]
            
            # Only process modules
            if 'ModuleDeclaration' not in str(type(member)):
                continue
            
            module_name = self._get_module_name(member)
            if not module_name:
                continue
            
            usage = ClassUsageInfo(module_name=module_name)
            
            # Scan module members for class usage
            if hasattr(member, 'members') and member.members:
                for j in range(len(member.members)):
                    stmt = member.members[j]
                    self._analyze_statement_recursive(stmt, usage, filename)
            
            if usage.instances or usage.method_calls:
                self.usages[module_name] = usage
    
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
                name = header.name
                if hasattr(name, 'value'):
                    return str(name.value).strip()
                return str(name).strip()
        return ""
    
    def _analyze_statement_recursive(self, stmt, usage: ClassUsageInfo, filename: str):
        """递归分析语句查找类使用。
        
        Args:
            stmt: 语句节点
            usage: 使用信息对象
            filename: 文件名
        """
        if stmt is None:
            return
        
        stmt_type = str(type(stmt))
        
        # Handle ProceduralBlock (initial/always blocks)
        if 'ProceduralBlock' in stmt_type:
            if hasattr(stmt, 'statement') and stmt.statement:
                self._analyze_statement_recursive(stmt.statement, usage, filename)
            return
        
        # Handle BlockStatement (begin...end)
        if 'Block' in stmt_type:
            if hasattr(stmt, 'items') and stmt.items:
                for item in stmt.items:
                    self._analyze_statement_recursive(item, usage, filename)
            return
        
        # Handle CaseStatement
        if 'Case' in stmt_type:
            if hasattr(stmt, 'items') and stmt.items:
                for item in stmt.items:
                    if hasattr(item, 'clause') and item.clause:
                        self._analyze_statement_recursive(item.clause, usage, filename)
            return
        
        # Handle ConditionalStatement (if/else)
        if 'Conditional' in stmt_type:
            if hasattr(stmt, 'statement') and stmt.statement:
                self._analyze_statement_recursive(stmt.statement, usage, filename)
            if hasattr(stmt, 'elseClause') and stmt.elseClause:
                else_clause = stmt.elseClause
                if hasattr(else_clause, 'clause') and else_clause.clause:
                    self._analyze_statement_recursive(else_clause.clause, usage, filename)
            return
        
        # Handle LoopStatement (for, while, do-while)
        if 'Loop' in stmt_type and 'Generate' not in stmt_type:
            if hasattr(stmt, 'statement') and stmt.statement:
                self._analyze_statement_recursive(stmt.statement, usage, filename)
            return
        
        # Handle ForLoopStatement
        if 'ForLoop' in stmt_type:
            if hasattr(stmt, 'statement') and stmt.statement:
                self._analyze_statement_recursive(stmt.statement, usage, filename)
            return
        
        # DataDeclaration - class handle declaration
        if 'DataDeclaration' in stmt_type:
            self._analyze_data_declaration(stmt, usage, filename)
            return
        
        # ExpressionStatement - method calls
        if 'ExpressionStatement' in stmt_type or 'VoidCasted' in stmt_type:
            self._analyze_expression_statement(stmt, usage)
            return
        
        # Assignment statements
        if 'Assignment' in stmt_type:
            self._analyze_assignment(stmt, usage)
            return
    
    def _clean_type_string(self, type_str: str) -> str:
        """清理类型字符串。
        
        Args:
            type_str: 原始类型字符串
        
        Returns:
            str: 清理后的字符串
        """
        type_str = re.sub(r'//.*$', '', type_str, flags=re.MULTILINE)
        type_str = re.sub(r'/\*.*?\*/', '', type_str, flags=re.DOTALL)
        type_str = ' '.join(type_str.split())
        return type_str.strip()
    
    def _analyze_data_declaration(self, decl, usage: ClassUsageInfo, filename: str):
        """分析数据声明查找类句柄。
        
        Args:
            decl: 数据声明节点
            usage: 使用信息对象
            filename: 文件名
        """
        try:
            if not hasattr(decl, 'type') or not decl.type:
                return
            
            type_str = self._clean_type_string(str(decl.type).strip())
            
            # Check if type is a known class
            class_name = self._resolve_class_name(type_str)
            if not class_name:
                return
            
            if hasattr(decl, 'declarators') and decl.declarators:
                declarators = decl.declarators
                try:
                    for i in range(len(declarators)):
                        dec = declarators[i]
                        var_name = self._get_name(dec.name)
                        if var_name:
                            handle_type = "handle"
                            if hasattr(dec, 'initializer') and dec.initializer:
                                init_str = str(dec.initializer).strip()
                                if 'new' in init_str.lower():
                                    handle_type = "new"
                            
                            instance = ClassInstanceInfo(
                                instance_name=var_name,
                                class_name=class_name,
                                handle_type=handle_type,
                                file_name=filename
                            )
                            usage.instances.append(instance)
                except:
                    pass
        except Exception as e:
            print(f"Error analyzing data declaration: {e}")
    
    def _analyze_expression_statement(self, stmt, usage: ClassUsageInfo):
        """分析表达式语句。
        
        Args:
            stmt: 语句节点
            usage: 使用信息对象
        """
        try:
            stmt_str = str(stmt)
            method_pattern = r'(\w+)\.(\w+)\s*\('
            matches = re.findall(method_pattern, stmt_str)
            
            for obj_name, method_name in matches:
                if obj_name in ('this', 'super'):
                    continue
                full_call = f"{obj_name}.{method_name}()"
                if full_call not in usage.method_calls:
                    usage.method_calls.append(full_call)
        except Exception as e:
            print(f"Error analyzing expression statement: {e}")
    
    def _analyze_assignment(self, stmt, usage: ClassUsageInfo):
        """分析赋值语句。
        
        Args:
            stmt: 语句节点
            usage: 使用信息对象
        """
        try:
            stmt_str = str(stmt)
            method_pattern = r'(\w+)\.(\w+)\s*\('
            matches = re.findall(method_pattern, stmt_str)
            
            for obj_name, method_name in matches:
                if obj_name in ('this', 'super'):
                    continue
                full_call = f"{obj_name}.{method_name}()"
                if full_call not in usage.method_calls:
                    usage.method_calls.append(full_call)
        except Exception as e:
            print(f"Error analyzing assignment: {e}")
    
    def _resolve_class_name(self, type_str: str) -> Optional[str]:
        """解析类型字符串为类名。
        
        Args:
            type_str: 类型字符串
        
        Returns:
            str: 类名，未找到返回 None
        """
        if type_str in self.classes:
            return type_str
        
        parts = type_str.split('::')
        if len(parts) > 1:
            potential = parts[-1]
            if potential in self.classes:
                return potential
        
        return None
    
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
    
    def get_module_usages(self, module_name: str) -> Optional[ClassUsageInfo]:
        """获取模块的类使用信息。
        
        Args:
            module_name: 模块名
        
        Returns:
            ClassUsageInfo: 使用信息，未找到返回 None
        """
        return self.usages.get(module_name)
    
    def get_all_instances_of_class(self, class_name: str) -> List[ClassInstanceInfo]:
        """获取所有指定类的实例。
        
        Args:
            class_name: 类名
        
        Returns:
            List[ClassInstanceInfo]: 实例列表
        """
        instances = []
        for usage in self.usages.values():
            for inst in usage.instances:
                if inst.class_name == class_name:
                    instances.append(inst)
        return instances
    
    def get_class_usage_summary(self) -> Dict[str, int]:
        """获取类使用统计。
        
        Returns:
            Dict[str, int]: 类名到实例数量的映射
        """
        summary = {}
        for usage in self.usages.values():
            for inst in usage.instances:
                class_name = inst.class_name
                summary[class_name] = summary.get(class_name, 0) + 1
        return summary
