"""Class extractor for SystemVerilog.

Extracts:
- Class declarations
- Properties (variables)
- Constraints
- Methods
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
    """Extract SystemVerilog class information from parsed AST."""
    
    def __init__(self, parser):
        self.parser = parser
        self.classes: Dict[str, ClassInfo] = {}
        self._extract()
    
    def extract(self) -> Dict[str, ClassInfo]:
        """Return extracted classes dict."""
        return self.classes
    
    def _extract(self):
        """Extract classes from all parsed trees."""
        for fname, tree in self.parser.trees.items():
            if tree and hasattr(tree, 'root') and tree.root:
                self._extract_from_tree(tree.root, fname)
    
    def _extract_from_tree(self, node, filename: str):
        """Recursively traverse AST to find class declarations."""
        if node is None:
            return
        
        node_type = type(node).__name__
        
        if 'ClassDeclaration' in node_type:
            self._extract_class(node, filename)
        
        if hasattr(node, 'members') and node.members:
            for child in node.members:
                self._extract_from_tree(child, filename)
    
    def _extract_class(self, class_node, filename: str):
        """Extract complete class information."""
        try:
            name = str(class_node.name).strip() if hasattr(class_node, 'name') and class_node.name else ""
            if not name:
                return
            
            info = ClassInfo(name=name, line_number=0)
            
            if hasattr(class_node, 'extendsClause') and class_node.extendsClause:
                extends_str = str(class_node.extendsClause).strip()
                if extends_str.startswith('extends '):
                    info.extends = extends_str[8:].split('#')[0].strip()
            
            if hasattr(class_node, 'parameters') and class_node.parameters:
                self._extract_parameters(class_node.parameters, info)
            
            if hasattr(class_node, 'items') and class_node.items:
                self._extract_class_items(class_node.items, info)
            
            self.classes[name] = info
            
        except Exception as e:
            print(f"Error extracting class: {e}")
    
    def _extract_parameters(self, params_node, info: ClassInfo):
        """Extract class type parameters."""
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
        """Extract properties, constraints, methods from class items."""
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
        """Extract a class property."""
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
        """Extract a constraint."""
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
        """Extract a class method."""
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
