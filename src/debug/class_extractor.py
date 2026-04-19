"""Class declaration extractor for SystemVerilog classes."""

import sys
import re
from typing import List, Dict, Optional, Set

from .class_info import (
    ClassInfo, PropertyInfo, ConstraintInfo, MethodInfo,
    ConstraintModeInfo
)


# Valid SystemVerilog property/method qualifiers
VALID_QUALIFIERS: Set[str] = {
    'rand', 'randc',           # Random qualifiers
    'local', 'protected', 'public',  # Access qualifiers  
    'static',                   # Storage
    'const',                    # Constant
    'virtual', 'pure',          # Method qualifiers
    'automatic',                # Function/task qualifiers
}


class ClassExtractor:
    """Extract class declarations from parsed SystemVerilog code."""

    def __init__(self, parser):
        self.parser = parser
        self.classes: Dict[str, ClassInfo] = {}

    def extract(self) -> Dict[str, ClassInfo]:
        """Extract all class declarations from parsed code."""
        self.classes = {}

        for fname, tree in self.parser.trees.items():
            self._extract_from_tree(tree)

        return self.classes

    def get_class(self, name: str) -> Optional[ClassInfo]:
        """Get a specific class by name."""
        return self.classes.get(name)

    def _extract_from_tree(self, tree):
        """Extract classes from a syntax tree."""
        root = tree.root

        # CompilationUnitSyntax has members
        if hasattr(root, 'members') and root.members:
            for i in range(len(root.members)):
                member = root.members[i]
                if self._is_class_declaration(member):
                    class_info = self._extract_class(member)
                    if class_info:
                        self.classes[class_info.name] = class_info
        # Direct ClassDeclarationSyntax (single file with one class)
        elif self._is_class_declaration(root):
            class_info = self._extract_class(root)
            if class_info:
                self.classes[class_info.name] = class_info

    def _is_class_declaration(self, node) -> bool:
        """Check if node is a class declaration."""
        return "ClassDeclarationSyntax" in str(type(node))

    def _extract_class(self, cls_node) -> Optional[ClassInfo]:
        """Extract information from a ClassDeclarationSyntax node."""
        try:
            name = self._get_name(cls_node.name)
            if not name:
                return None

            info = ClassInfo(name=name)

            # Get line number
            try:
                if hasattr(cls_node, 'getFirstToken') and cls_node.getFirstToken():
                    info.line_number = cls_node.getFirstToken().location.line
            except:
                pass

            # Check if virtual
            if hasattr(cls_node, 'virtualOrInterface'):
                virt = cls_node.virtualOrInterface
                if virt and 'virtual' in str(virt).lower():
                    info.is_virtual = True

            # Check extends clause
            if hasattr(cls_node, 'extendsClause') and cls_node.extendsClause:
                info.extends = self._extract_extends(cls_node.extendsClause)

            # Check abstract
            if hasattr(cls_node, 'items'):
                info.is_abstract = self._check_abstract(cls_node.items)

            # Extract items
            if hasattr(cls_node, 'items') and cls_node.items:
                self._extract_items(cls_node.items, info)

            return info

        except Exception as e:
            print(f"Error extracting class: {e}")
            return None

    def _get_name(self, name_node) -> str:
        """Get name from a name node."""
        if not name_node:
            return ""
        if hasattr(name_node, 'value'):
            return str(name_node.value).strip()
        return str(name_node).strip()

    def _extract_extends(self, extends_node) -> str:
        """Extract the parent class name from extends clause."""
        if not extends_node:
            return ""
        ext_str = str(extends_node).strip()
        if ext_str.startswith("extends "):
            ext_str = ext_str[8:]
        return ext_str.strip()

    def _check_abstract(self, items) -> bool:
        """Check if class has abstract methods."""
        try:
            for i in range(len(items)):
                item = items[i]
                item_str = str(type(item))
                if 'ClassMethod' in item_str or 'Prototype' in item_str:
                    if hasattr(item, 'qualifiers'):
                        quals = str(item.qualifiers)
                        if 'pure' in quals.lower() or 'abstract' in quals.lower():
                            return True
        except:
            pass
        return False

    def _filter_qualifiers(self, quals_list: List[str]) -> List[str]:
        """Filter qualifiers to only include valid SV keywords."""
        return [q for q in quals_list if q in VALID_QUALIFIERS]

    def _extract_items(self, items, info: ClassInfo):
        """Extract properties, constraints, and methods from class items."""
        try:
            for i in range(len(items)):
                item = items[i]
                item_type = str(type(item))

                if 'ClassPropertyDeclaration' in item_type:
                    prop = self._extract_property(item)
                    if prop:
                        info.properties.append(prop)

                elif 'ConstraintDeclaration' in item_type:
                    constraint = self._extract_constraint(item)
                    if constraint:
                        info.constraints.append(constraint)

                elif 'ClassMethod' in item_type or 'MethodDeclaration' in item_type:
                    method = self._extract_method(item)
                    if method:
                        info.methods.append(method)
                        
                elif 'ClassMethodPrototype' in item_type:
                    # Pure virtual method prototypes
                    method = self._extract_method(item)
                    if method:
                        info.methods.append(method)

        except Exception as e:
            print(f"Error extracting class items: {e}")

    def _extract_property(self, prop_node) -> Optional[PropertyInfo]:
        """Extract property information from ClassPropertyDeclarationSyntax."""
        try:
            name = ""
            data_type = ""
            width = None
            dimensions = []
            qualifiers = []
            rand_mode = "none"
            default_value = None

            # Get qualifiers
            if hasattr(prop_node, 'qualifiers') and prop_node.qualifiers:
                quals_str = str(prop_node.qualifiers).strip()
                quals_list = quals_str.split()
                qualifiers = self._filter_qualifiers(quals_list)
                
                if 'rand' in qualifiers:
                    rand_mode = 'rand'
                elif 'randc' in qualifiers:
                    rand_mode = 'randc'

            # Get declaration (the actual variable declaration)
            if hasattr(prop_node, 'declaration') and prop_node.declaration:
                decl = prop_node.declaration

                # type contains the base type and width
                if hasattr(decl, 'type') and decl.type:
                    data_type = str(decl.type).strip()
                    # Parse width from type string like "bit [7:0]"
                    width = self._parse_width_from_type(data_type)

                # declarators contains the variable names and dimensions
                if hasattr(decl, 'declarators') and decl.declarators:
                    declarators = decl.declarators
                    try:
                        for i in range(len(declarators)):
                            dec = declarators[i]
                            dec_name = self._get_name(dec.name)
                            if dec_name:
                                name = dec_name
                                
                                # Extract dimensions
                                if hasattr(dec, 'dimensions') and dec.dimensions:
                                    dims = dec.dimensions
                                    dims_str = str(dims).strip()
                                    if dims_str:
                                        dimensions = self._parse_dimensions(dims_str)
                                    
                                    # Check for initializer/default value
                                    if hasattr(dec, 'initializer') and dec.initializer:
                                        default_value = str(dec.initializer)
                            
                            if name:
                                break
                    except:
                        pass

            if not name:
                return None

            return PropertyInfo(
                name=name,
                data_type=data_type,
                width=width,
                dimensions=dimensions,
                qualifiers=qualifiers,
                rand_mode=rand_mode,
                default_value=default_value
            )

        except Exception as e:
            print(f"Error extracting property: {e}")
            return None

    def _parse_width_from_type(self, type_str: str) -> Optional[int]:
        """Parse width from type string like 'bit [7:0]' or 'logic [15:0]'."""
        if not type_str:
            return None
        # Match [high:low] pattern with numeric values
        match = re.search(r'\[(\d+):(\d+)\]', type_str)
        if match:
            high = int(match.group(1))
            low = int(match.group(2))
            return high - low + 1
        # If no numeric range found but has brackets, it's parameterized
        if '[' in type_str and ']' in type_str:
            return 1  # Parameterized width
        return 1  # Scalar defaults to width 1

    def _parse_dimensions(self, dims_str: str) -> List[str]:
        """Parse array dimensions from string like '[4]' or '[$]'."""
        if not dims_str:
            return []
        
        dimensions = []
        matches = re.findall(r'\[.*?\]', dims_str)
        for m in matches:
            if m not in dimensions:
                dimensions.append(m)
        
        return dimensions

    def _extract_constraint(self, cons_node) -> Optional[ConstraintInfo]:
        """Extract constraint information."""
        try:
            name = ""
            constraint_type = "simple"
            expression = ""
            raw_text = str(cons_node)
            is_soft = False
            dist_items = []

            # Get constraint name
            if hasattr(cons_node, 'name') and cons_node.name:
                name = self._get_name(cons_node.name)

            # Get constraint body from 'block' attribute
            if hasattr(cons_node, 'block') and cons_node.block:
                block_str = str(cons_node.block).strip()
                # Remove braces
                if block_str.startswith('{'):
                    block_str = block_str[1:]
                if block_str.endswith('}'):
                    block_str = block_str[:-1]
                expression = block_str.strip()

                # Determine constraint type by analyzing expression
                constraint_type, is_soft, dist_items = self._classify_constraint(expression)

            if not name:
                return None

            return ConstraintInfo(
                name=name,
                constraint_type=constraint_type,
                expression=expression,
                raw_text=raw_text,
                is_soft=is_soft,
                dist_items=dist_items
            )

        except Exception as e:
            print(f"Error extracting constraint: {e}")
            return None

    def _classify_constraint(self, expr: str) -> tuple:
        """Classify constraint type and extract additional info."""
        expr_lower = expr.lower()
        constraint_type = "simple"
        is_soft = False
        dist_items = []
        
        # Check for soft constraint
        if 'soft ' in expr_lower or expr_lower.startswith('soft '):
            constraint_type = "soft"
            is_soft = True
            # Remove soft keyword for further analysis
            expr = re.sub(r'\bsoft\b', '', expr, flags=re.IGNORECASE).strip()
        
        # Check for distribution constraint
        if 'dist {' in expr_lower:
            constraint_type = "dist"
            # Extract dist items
            dist_match = re.search(r'dist\s*\{([^}]+)\}', expr, re.IGNORECASE)
            if dist_match:
                dist_items = [item.strip() for item in dist_match.group(1).split(',')]
        
        # Check for solve before
        elif 'solve ' in expr_lower and ' before ' in expr_lower:
            constraint_type = "solve_before"
        
        # Check for foreach
        elif 'foreach' in expr_lower:
            constraint_type = "loop"
        
        # Check for implication (after soft check)
        elif '->' in expr:
            constraint_type = "implication"
        
        # Check for conditional (if-else without soft)
        elif re.search(r'\bif\b.*\belse\b', expr, re.IGNORECASE | re.DOTALL) and constraint_type == "simple":
            constraint_type = "conditional"
        
        return constraint_type, is_soft, dist_items

    def _extract_method(self, method_node) -> Optional[MethodInfo]:
        """Extract method information from ClassMethodDeclarationSyntax."""
        try:
            name = ""
            qualifiers = []
            return_type = ""
            prototype_str = ""

            # Get qualifiers from the method node
            if hasattr(method_node, 'qualifiers') and method_node.qualifiers:
                quals_str = str(method_node.qualifiers).strip()
                quals_list = quals_str.split()
                qualifiers = self._filter_qualifiers(quals_list)

            # Try to get name and prototype
            if hasattr(method_node, 'declaration') and method_node.declaration:
                decl = method_node.declaration
                prototype_str = str(decl)

                if hasattr(decl, 'prototype') and decl.prototype:
                    proto = decl.prototype
                    if hasattr(proto, 'name') and proto.name:
                        name = self._get_name(proto.name)
                    
                    if hasattr(proto, 'returnType') and proto.returnType:
                        return_type = str(proto.returnType).strip()
            
            elif hasattr(method_node, 'prototype') and method_node.prototype:
                proto = method_node.prototype
                prototype_str = str(proto)
                if hasattr(proto, 'name') and proto.name:
                    name = self._get_name(proto.name)
                if hasattr(proto, 'returnType') and proto.returnType:
                    return_type = str(proto.returnType).strip()

            if not name and hasattr(method_node, 'name') and method_node.name:
                name = self._get_name(method_node.name)

            if not name:
                return None

            return MethodInfo(
                name=name,
                prototype=prototype_str[:100] if prototype_str else str(method_node)[:100],
                qualifiers=qualifiers,
                return_type=return_type
            )

        except Exception as e:
            print(f"Error extracting method: {e}")
            return None
