"""ClassExtractor - SystemVerilog 类提取器。

从 SystemVerilog 代码中提取类定义信息：
- 类声明
- 属性 (variables)
- 约束 (constraints)
- 方法 (methods)

Example:
    >>> from debug.class_extractor import ClassExtractor
    >>> from parse import SVParser
    >>> parser = SVParser()
    >>> parser.parse_file("design.sv")
    >>> extractor = ClassExtractor(parser)
    >>> for name, cls in extractor.classes.items():
    ...     print(f"Class: {name}, extends: {cls.extends}")
    >>> print(f"Total: {len(extractor.classes)} classes")
"""
import sys
import re
from typing import Dict, List
from dataclasses import dataclass

from .class_info import (
    ClassInfo, PropertyInfo, ConstraintInfo, MethodInfo,
    TypeParameterInfo, ValueParameterInfo
)


class ClassExtractor:
    """SystemVerilog 类提取器。
    
    使用 pyslang AST 解析器提取类定义信息。

    Attributes:
        parser: SVParser 实例
        classes: 类名字典 (name -> ClassInfo)
    
    Example:
        >>> extractor = ClassExtractor(parser)
        >>> print(f"Found {len(extractor.classes)} classes")
    """
    
    def __init__(self, parser):
        """初始化提取器。
        
        Args:
            parser: SVParser 实例
        """
        self.parser = parser
        self.classes: Dict[str, ClassInfo] = {}
        self._extract_all()
    
    def _extract_all(self):
        """提取所有类定义。"""
        for fname, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            self._scan_tree(tree)
    
    def _scan_tree(self, tree):
        """扫描语法树提取类。
        
        Args:
            tree: SyntaxTree 对象
        """
        root = tree.root
        
        if not hasattr(root, 'members') or not root.members:
            return
        
        for i in range(len(root.members)):
            member = root.members[i]
            if member is None:
                continue
            
            member_type = str(type(member).__name__)
            
            if 'ClassDeclaration' in member_type:
                info = self._extract_class(member)
                if info:
                    self.classes[info.name] = info
    
    def _extract_class(self, class_node) -> ClassInfo:
        """提取单个类。
        
        Args:
            class_node: 类声明节点
        
        Returns:
            ClassInfo: 类信息对象
        """
        info = ClassInfo(name="")
        
        # Get class name
        if hasattr(class_node, 'header') and class_node.header:
            if hasattr(class_node.header, 'name') and class_node.header.name:
                name_val = class_node.header.name
                if hasattr(name_val, 'value'):
                    info.name = str(name_val.value).strip()
                else:
                    info.name = str(name_val).strip()
        
        if not info.name:
            return info
        
        # Check for extends (inheritance)
        if hasattr(class_node, 'header') and class_node.header:
            if hasattr(class_node.header, 'extends') and class_node.header.extends:
                extends_node = class_node.header.extends
                if hasattr(extends_node, 'name') and extends_node.name:
                    info.extends = str(extends_node.name).strip()
        
        # Check virtual/abstract
        if hasattr(class_node, 'qualifiers') and class_node.qualifiers:
            quals_str = str(class_node.qualifiers).lower()
            if 'virtual' in quals_str:
                info.is_virtual = True
            if 'abstract' in quals_str:
                info.is_abstract = True
        
        # Extract parameters
        if hasattr(class_node, 'parameters') and class_node.parameters:
            self._extract_parameters(class_node.parameters, info)
        
        # Extract class items (body)
        if hasattr(class_node, 'items') and class_node.items:
            self._extract_class_items(class_node.items, info)
        elif hasattr(class_node, 'members') and class_node.members:
            self._extract_class_items(class_node.members, info)
        
        return info
    
    def _extract_parameters(self, params_node, info: ClassInfo):
        """提取类型参数和值参数。
        
        Args:
            params_node: 参数节点
            info: ClassInfo 对象
        """
        try:
            if not hasattr(params_node, 'declarations'):
                return
            
            decls = params_node.declarations
            if not hasattr(decls, '__iter__'):
                return
            
            for decl in decls:
                decl_type = type(decl).__name__
                
                if 'TypeParameterDeclaration' in decl_type:
                    name = ""
                    default_type = None
                    if hasattr(decl, 'declarators'):
                        for d in decl.declarators:
                            if hasattr(d, 'name'):
                                name = str(d.name).strip()
                            if hasattr(d, 'assignment') and d.assignment:
                                default_type = str(d.assignment).lstrip('= ').strip()
                    if name:
                        info.type_parameters.append(TypeParameterInfo(name=name, default_type=default_type))
                
                elif 'ParameterDeclaration' in decl_type:
                    data_type = "int"
                    if hasattr(decl, 'type') and decl.type:
                        data_type = str(decl.type).strip()
                    
                    if hasattr(decl, 'declarators'):
                        for d in decl.declarators:
                            if hasattr(d, 'name'):
                                name = str(d.name).strip()
                                default_value = None
                                if hasattr(d, 'initializer') and d.initializer:
                                    default_value = str(d.initializer).lstrip('= ').strip()
                                info.value_parameters.append(
                                    ValueParameterInfo(name=name, data_type=data_type, default_value=default_value)
                                )
        except Exception as e:
            print(f"Error extracting parameters: {e}")
    
    def _extract_class_items(self, items, info: ClassInfo):
        """提取属性、约束、方法。
        
        Args:
            items: 类项列表
            info: ClassInfo 对象
        """
        if not items:
            return
        
        try:
            for item in items:
                item_type = type(item).__name__
                
                if 'Property' in item_type:
                    self._extract_property(item, info)
                elif 'Constraint' in item_type:
                    self._extract_constraint(item, info)
                elif 'Method' in item_type:
                    self._extract_method(item, info)
                    
        except Exception as e:
            print(f"Error extracting class items: {e}")
    
    def _extract_property(self, prop_node, info: ClassInfo):
        """提取类属性。
        
        Args:
            prop_node: 属性节点
            info: ClassInfo 对象
        """
        try:
            data_type = "logic"
            prop_name = ""
            qualifiers = []
            rand_mode = "none"
            dimensions = []
            
            decl = prop_node
            if hasattr(prop_node, 'declaration') and prop_node.declaration:
                decl = prop_node.declaration
            
            # Extract qualifiers from prop_node (not decl)
            if hasattr(prop_node, 'qualifiers') and prop_node.qualifiers:
                quals_str = str(prop_node.qualifiers).lower()
                for q in ['rand', 'randc', 'local', 'protected', 'static', 'const', 'var']:
                    if q in quals_str:
                        qualifiers.append(q)
                if 'randc' in quals_str:
                    rand_mode = "randc"
                elif 'rand' in quals_str:
                    rand_mode = "rand"
            
            # Get base type
            if hasattr(decl, 'type') and decl.type:
                data_type = str(decl.type).strip()
            
            # Extract declarators (may contain array dimensions)
            if hasattr(decl, 'declarators') and decl.declarators:
                for d in decl.declarators:
                    if hasattr(d, 'name'):
                        prop_name = str(d.name).strip()
                    # Check for array dimensions in declarator
                    if hasattr(d, 'dimensions') and d.dimensions:
                        for dim in d.dimensions:
                            dim_str = str(dim).strip()
                            if dim_str:
                                dimensions.append(dim_str)
            
            if not prop_name:
                return
            
            # Parse dimensions from data_type if not already extracted
            if not dimensions and '[' in data_type:
                dims = re.findall(r'\[[^\]]+\]', data_type)
                dimensions = dims
            
            prop = PropertyInfo(
                name=prop_name,
                data_type=data_type,
                dimensions=dimensions,
                qualifiers=qualifiers,
                rand_mode=rand_mode
            )
            info.properties.append(prop)
            
        except Exception as e:
            print(f"Error extracting property: {e}")
    
    def _extract_constraint(self, const_node, info: ClassInfo):
        """提取类约束。
        
        Args:
            const_node: 约束节点
            info: ClassInfo 对象
        """
        try:
            const_name = ""
            const_type = "simple"
            expression = ""
            is_soft = False
            
            if hasattr(const_node, 'name') and const_node.name:
                const_name = str(const_node.name).strip()
            
            if not const_name:
                return
            
            # Get expression and check for soft from the block's first statement
            if hasattr(const_node, 'block') and const_node.block:
                block = const_node.block
                expression = str(block).strip()
                
                # Check for soft keyword in constraint block statements
                if hasattr(block, 'items') and block.items:
                    for stmt in block.items:
                        # ExpressionConstraintSyntax has 'soft' attribute
                        if hasattr(stmt, 'soft') and stmt.soft:
                            is_soft = True
                            const_type = "soft"
                            break
                        # For other statement types, check string
                        elif 'soft' in str(stmt).lower():
                            is_soft = True
                            const_type = "soft"
                            break
                
                # Clean expression
                expression = re.sub(r'^\{', '', expression)
                expression = re.sub(r'\}$', '', expression)
                expression = expression.strip()
                
                # Detect other types only if not soft
                if not is_soft:
                    expr_lower = expression.lower()
                    if '->' in expression:
                        const_type = "implication"
                    elif 'dist' in expr_lower:
                        const_type = "dist"
                    elif 'solve' in expr_lower and 'before' in expr_lower:
                        const_type = "solve_before"
            
            # Extract dist items - use simple pattern
            dist_items = []
            if const_type == "dist":
                dist_matches = re.findall(r'\[.*?\] := \d+', expression)
                dist_items = dist_matches
            
            const = ConstraintInfo(
                name=const_name,
                constraint_type=const_type,
                expression=expression,
                is_soft=is_soft,
                dist_items=dist_items
            )
            info.constraints.append(const)
            
        except Exception as e:
            print(f"Error extracting constraint: {e}")
    
    def _extract_method(self, method_node, info: ClassInfo):
        """提取类方法。
        
        Args:
            method_node: 方法节点
            info: ClassInfo 对象
        """
        try:
            method_name = ""
            qualifiers = []
            prototype = ""
            return_type = "void"
            
            # Get qualifiers from ClassMethodDeclarationSyntax
            if hasattr(method_node, 'qualifiers') and method_node.qualifiers:
                for q in method_node.qualifiers:
                    qualifiers.append(str(q).strip())
            
            # Get declaration and prototype
            decl = method_node
            if hasattr(method_node, 'declaration') and method_node.declaration:
                decl = method_node.declaration
            
            proto = decl
            if hasattr(decl, 'prototype') and decl.prototype:
                proto = decl.prototype
            
            if proto is None:
                return
            
            if hasattr(proto, 'name') and proto.name:
                method_name = str(proto.name).strip()
            
            if not method_name:
                return
            
            if hasattr(proto, 'returnType') and proto.returnType:
                return_type = str(proto.returnType).strip()
            
            if hasattr(proto, 'portList') and proto.portList:
                prototype = f"({proto.portList})"
            
            method = MethodInfo(
                name=method_name,
                prototype=prototype,
                qualifiers=qualifiers,
                return_type=return_type
            )
            info.methods.append(method)
            
        except Exception as e:
            print(f"Error extracting method: {e}")
