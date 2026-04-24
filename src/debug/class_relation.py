"""Class relationship and method call graph extractor."""

import sys
import re
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field

from .class_info import ClassInfo
from .class_extractor import ClassExtractor


@dataclass
class MethodCallInfo:
    """Information about a method call."""
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
    """Information about relationship between classes."""
    from_class: str
    to_class: str
    relation_type: str
    details: str = ""
    line_number: int = 0
    is_instantiated: bool = False  # True if new() called
    instantiation_context: str = ""


@dataclass
class MethodDefinition:
    """Information about a method definition."""
    class_name: str
    name: str
    is_function: bool = True
    is_virtual: bool = False
    is_pure: bool = False
    is_static: bool = False
    return_type: str = ""
    arguments: str = ""


class ClassRelationExtractor:
    """Extract class relationships and method call graphs."""

    def __init__(self, parser, class_extractor: ClassExtractor):
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
        for fname, tree in self.parser.trees.items():
            self._extract_from_tree(tree, fname)

    def _extract_from_tree(self, tree, filename: str):
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
        if hasattr(module_node, 'header') and module_node.header:
            header = module_node.header
            if hasattr(header, 'name') and header.name:
                name = header.name
                if hasattr(name, 'value'):
                    return str(name.value).strip()
                return str(name).strip()
        return ""

    def _get_name(self, name_node) -> str:
        if not name_node:
            return ""
        if hasattr(name_node, 'value'):
            return str(name_node.value).strip()
        return str(name_node).strip()

    def _process_module_members(self, module_node, filename: str, 
                                current_class: Optional[str], current_module: str):
        if not hasattr(module_node, 'members') or not module_node.members:
            return
        
        for i in range(len(module_node.members)):
            stmt = module_node.members[i]
            stmt_type = type(stmt).__name__
            
            if 'DataDeclaration' in stmt_type:
                self._extract_data_declaration_relations(
                    stmt, current_module, filename
                )
            elif 'FunctionDeclaration' in stmt_type:
                self._extract_global_function(stmt, current_module, filename)
            elif 'TaskDeclaration' in stmt_type:
                self._extract_global_task(stmt, current_module, filename)
            elif 'ProceduralBlock' in stmt_type:
                self._analyze_procedural_block(
                    stmt, current_class, current_module, filename
                )

    def _process_class_items(self, items, class_name: str, filename: str):
        if not items:
            return
        
        for i in range(len(items)):
            item = items[i]
            item_type = type(item).__name__
            
            if 'ClassMethod' in item_type or 'Method' in item_type:
                self._extract_method_definition(item, class_name, filename)
                self._analyze_class_method_body(item, class_name, filename)
            elif 'Constraint' in item_type:
                self._analyze_constraint_block(item, class_name, filename)

    def _extract_method_definition(self, method_node, class_name: str, filename: str):
        try:
            name = ""
            is_function = True
            is_virtual = False
            is_pure = False
            return_type = "void"
            arguments = ""
            
            decl = None
            if hasattr(method_node, 'declaration') and method_node.declaration:
                decl = method_node.declaration
            elif hasattr(method_node, 'prototype') and method_node.prototype:
                decl = method_node
            
            if decl is None:
                return
            
            proto = None
            if hasattr(decl, 'prototype') and decl.prototype:
                proto = decl.prototype
            
            if proto is None:
                return
            
            if hasattr(proto, 'name') and proto.name:
                name = str(proto.name).strip()
            
            if hasattr(proto, 'keyword') and proto.keyword:
                kw = str(proto.keyword).strip().lower()
                if 'task' in kw:
                    is_function = False
            
            if hasattr(proto, 'specifiers') and proto.specifiers:
                specs = str(proto.specifiers).lower()
                if 'virtual' in specs:
                    is_virtual = True
                if 'pure' in specs:
                    is_pure = True
            
            if hasattr(proto, 'returnType') and proto.returnType:
                return_type = str(proto.returnType).strip()
            
            if hasattr(proto, 'portList') and proto.portList:
                arguments = str(proto.portList)
            
            if not name:
                return
            
            method_def = MethodDefinition(
                class_name=class_name,
                name=name,
                is_function=is_function,
                is_virtual=is_virtual,
                is_pure=is_pure,
                return_type=return_type,
                arguments=arguments
            )
            
            if class_name in self.method_definitions:
                self.method_definitions[class_name].append(method_def)
            else:
                self.method_definitions[class_name] = [method_def]
                
        except Exception as e:
            print(f"Error extracting method definition: {e}")

    def _extract_class_relations(self, class_node, class_name: str, filename: str):
        try:
            line_number = 0
            try:
                if hasattr(class_node, 'getFirstToken') and class_node.getFirstToken():
                    line_number = class_node.getFirstToken().location.line
            except:
                pass
            
            if hasattr(class_node, 'extendsClause') and class_node.extendsClause:
                extends_str = str(class_node.extendsClause).strip()
                if extends_str.startswith('extends '):
                    parent_class = extends_str[8:].strip()
                    if '#' in parent_class:
                        parent_class = parent_class.split('#')[0].strip()
                    
                    relation = ClassRelationInfo(
                        from_class=class_name,
                        to_class=parent_class,
                        relation_type="extends",
                        line_number=line_number
                    )
                    self.relations.append(relation)
            
            if hasattr(class_node, 'parameters') and class_node.parameters:
                params = class_node.parameters
                if hasattr(params, 'declarations'):
                    decls = params.declarations
                    for j in range(len(decls)):
                        decl = decls[j]
                        decl_type = type(decl).__name__
                        
                        if 'TypeParameterDeclaration' in decl_type:
                            if hasattr(decl, 'declarators'):
                                declrs = decl.declarators
                                if hasattr(declrs, '__iter__') and not isinstance(declrs, str):
                                    for d in declrs:
                                        if hasattr(d, 'name'):
                                            param_name = str(d.name).strip()
                                            default_type = None
                                            if hasattr(d, 'assignment') and d.assignment:
                                                default_type = str(d.assignment).lstrip('= ').strip()
                                            
                                            if default_type and default_type in self.classes:
                                                relation = ClassRelationInfo(
                                                    from_class=class_name,
                                                    to_class=default_type,
                                                    relation_type="parameterized_type",
                                                    details=f"type {param_name}",
                                                    line_number=line_number
                                                )
                                                self.relations.append(relation)
            
            if hasattr(class_node, 'items') and class_node.items:
                for j in range(len(class_node.items)):
                    item = class_node.items[j]
                    item_type = type(item).__name__
                    
                    if 'ClassProperty' in item_type:
                        self._extract_property_class_relation(item, class_name, line_number)
                        
        except Exception as e:
            print(f"Error extracting class relations: {e}")

    def _extract_property_class_relation(self, prop_node, class_name: str, line_number: int):
        try:
            decl = None
            if hasattr(prop_node, 'declaration') and prop_node.declaration:
                decl = prop_node.declaration
            elif hasattr(prop_node, 'type') and prop_node.type:
                prop_type = str(prop_node.type).strip()
            else:
                return
            
            if decl is None:
                return
            
            prop_type = None
            if hasattr(decl, 'type') and decl.type:
                prop_type = str(decl.type).strip()
            
            if not prop_type:
                return
            
            if prop_type in self.classes:
                relation = ClassRelationInfo(
                    from_class=class_name,
                    to_class=prop_type,
                    relation_type="composition",
                    details="property",
                    line_number=line_number
                )
                self.relations.append(relation)
            
            if '[' in prop_type and ']' in prop_type:
                base_match = re.match(r'(\w+)\s*[\[\$:\*]', prop_type)
                if base_match:
                    base_type = base_match.group(1)
                    if base_type in self.classes:
                        relation = ClassRelationInfo(
                            from_class=class_name,
                            to_class=base_type,
                            relation_type="composition",
                            details="property (array)",
                            line_number=line_number
                        )
                        self.relations.append(relation)
                        
        except Exception as e:
            print(f"Error extracting property class relation: {e}")

    def _extract_data_declaration_relations(self, decl_node, module_name: str, filename: str):
        try:
            if not hasattr(decl_node, 'type') or not decl_node.type:
                return
            
            type_str = str(decl_node.type).strip()
            
            if type_str not in self.classes:
                base_type = type_str.split('#')[0].split('[')[0].strip()
                if base_type not in self.classes:
                    return
            
            if hasattr(decl_node, 'declarators') and decl_node.declarators:
                declrs = decl_node.declarators
                for i in range(len(declrs)):
                    dec = declrs[i]
                    var_name = self._get_name(dec.name)
                    if var_name:
                        # Check if new() instantiation
                        is_instantiated = False
                        if hasattr(dec, 'initializer') and dec.initializer:
                            init_str = str(dec.initializer).strip()
                            if 'new' in init_str.lower():
                                is_instantiated = True
                        
                        relation = ClassRelationInfo(
                            from_class=module_name,
                            to_class=type_str,
                            relation_type="instantiation",
                            details=f"variable {var_name}",
                            is_instantiated=is_instantiated,
                            instantiation_context="module"
                        )
                        self.relations.append(relation)
                    
        except Exception as e:
            print(f"Error extracting data declaration: {e}")

    def _analyze_class_method_body(self, method_node, class_name: str, filename: str):
        try:
            decl = None
            if hasattr(method_node, 'declaration') and method_node.declaration:
                decl = method_node.declaration
            
            if decl is None:
                return
            
            if hasattr(decl, 'items') and decl.items:
                for item in decl.items:
                    self._analyze_statement_recursive(item, class_name, None, filename)
                    self._track_new_instantiation(item, class_name, filename)
                    
        except Exception as e:
            print(f"Error analyzing class method: {e}")

    def _track_new_instantiation(self, stmt, class_name: str, filename: str):
        if stmt is None:
            return
        
        stmt_str = str(stmt)
        new_pattern = r'(\w+)\s*=\s*new\('
        matches = re.findall(new_pattern, stmt_str)
        
        if matches:
            line_number = 0
            try:
                if hasattr(stmt, 'getFirstToken') and stmt.getFirstToken():
                    line_number = stmt.getFirstToken().location.line
            except:
                pass
            
            for handle_name in matches:
                relation = ClassRelationInfo(
                    from_class=class_name,
                    to_class="unknown",
                    relation_type="instantiation",
                    details=f"variable {handle_name}",
                    is_instantiated=True,
                    instantiation_context=f"class_method:{class_name}",
                    line_number=line_number
                )
                self.relations.append(relation)

    def _analyze_constraint_block(self, constraint_node, class_name: str, filename: str):
        try:
            if not hasattr(constraint_node, 'block') or not constraint_node.block:
                return
            
            constraint_name = ""
            if hasattr(constraint_node, 'name') and constraint_node.name:
                constraint_name = str(constraint_node.name)
            
            block = constraint_node.block
            
            if hasattr(block, 'items') and block.items:
                for item in block.items:
                    self._analyze_constraint_item(item, class_name, constraint_name, filename)
                    
        except Exception as e:
            print(f"Error analyzing constraint block: {e}")

    def _analyze_constraint_item(self, item, class_name: str, constraint_name: str, filename: str):
        if item is None:
            return
        
        item_str = str(item)
        method_pattern = r'(\w+)\.(\w+)\s*\('
        matches = re.findall(method_pattern, item_str)
        
        line_number = 0
        try:
            if hasattr(item, 'getFirstToken') and item.getFirstToken():
                line_number = item.getFirstToken().location.line
        except:
            pass
        
        for obj_name, method_name in matches:
            full_call = f"{obj_name}.{method_name}()"
            
            call_info = MethodCallInfo(
                caller_name=obj_name,
                method_name=method_name,
                full_call=full_call,
                line_number=line_number,
                file_name=filename,
                constraint_name=constraint_name
            )
            self.method_calls.append(call_info)

    def _extract_global_function(self, func_node, module_name: str, filename: str):
        try:
            name = ""
            return_type = "void"
            
            if hasattr(func_node, 'name') and func_node.name:
                name = self._get_name(func_node.name)
            
            if hasattr(func_node, 'return_type') and func_node.return_type:
                return_type = str(func_node.return_type)
            
            if name:
                key = f"{module_name}::{name}" if module_name else name
                self.global_functions[key] = return_type
                
        except Exception as e:
            print(f"Error extracting global function: {e}")

    def _extract_global_task(self, task_node, module_name: str, filename: str):
        try:
            name = ""
            
            if hasattr(task_node, 'name') and task_node.name:
                name = self._get_name(task_node.name)
            
            if name:
                key = f"{module_name}::{name}" if module_name else name
                self.global_tasks.add(key)
                
        except Exception as e:
            print(f"Error extracting global task: {e}")

    def _analyze_procedural_block(self, block_node, current_class: Optional[str],
                                  current_module: Optional[str], filename: str):
        if not hasattr(block_node, 'statement') or not block_node.statement:
            return
        
        self._analyze_statement_recursive(
            block_node.statement, current_class, current_module, filename
        )

    def _analyze_statement_recursive(self, stmt, current_class: Optional[str],
                                    current_module: Optional[str], filename: str):
        if stmt is None:
            return
        
        stmt_type = type(stmt).__name__
        
        if 'Block' in stmt_type:
            if hasattr(stmt, 'items') and stmt.items:
                for item in stmt.items:
                    self._analyze_statement_recursive(item, current_class, current_module, filename)
            return
        
        if 'Loop' in stmt_type and 'Generate' not in stmt_type:
            if hasattr(stmt, 'statement') and stmt.statement:
                self._analyze_statement_recursive(stmt.statement, current_class, current_module, filename)
            return
        
        if 'ForLoop' in stmt_type:
            if hasattr(stmt, 'statement') and stmt.statement:
                self._analyze_statement_recursive(stmt.statement, current_class, current_module, filename)
            return
        
        if 'Conditional' in stmt_type:
            if hasattr(stmt, 'statement') and stmt.statement:
                self._analyze_statement_recursive(stmt.statement, current_class, current_module, filename)
            if hasattr(stmt, 'elseClause') and stmt.elseClause:
                if hasattr(stmt.elseClause, 'clause') and stmt.elseClause.clause:
                    self._analyze_statement_recursive(stmt.elseClause.clause, current_class, current_module, filename)
            return
        
        if 'Case' in stmt_type:
            if hasattr(stmt, 'items') and stmt.items:
                for item in stmt.items:
                    if hasattr(item, 'clause') and item.clause:
                        self._analyze_statement_recursive(item.clause, current_class, current_module, filename)
            return
        
        if 'ExpressionStatement' in stmt_type or 'VoidCasted' in stmt_type:
            self._extract_method_calls(stmt, current_class, current_module, filename)
            return
        
        if 'Assignment' in stmt_type:
            if hasattr(stmt, 'right') and stmt.right:
                self._extract_method_calls(stmt.right, current_class, current_module, filename)
            if hasattr(stmt, 'left') and stmt.left:
                self._extract_method_calls(stmt.left, current_class, current_module, filename)

    def _extract_method_calls(self, expr_node, current_class: Optional[str],
                             current_module: Optional[str], filename: str):
        if expr_node is None:
            return
        
        expr_str = str(expr_node)
        
        method_pattern = r'(\w+)\.(\w+)\s*\('
        matches = re.findall(method_pattern, expr_str)
        
        line_number = 0
        try:
            if hasattr(expr_node, 'getFirstToken') and expr_node.getFirstToken():
                line_number = expr_node.getFirstToken().location.line
        except:
            pass
        
        for obj_name, method_name in matches:
            full_call = f"{obj_name}.{method_name}()"
            
            is_internal = False
            is_super_call = obj_name.lower() == 'super'
            is_this_call = obj_name.lower() == 'this'
            
            if current_class:
                is_internal = is_super_call or is_this_call
            
            call_info = MethodCallInfo(
                caller_name=obj_name,
                method_name=method_name,
                full_call=full_call,
                is_internal=is_internal,
                is_super_call=is_super_call,
                is_this_call=is_this_call,
                line_number=line_number,
                file_name=filename
            )
            self.method_calls.append(call_info)
        
        standalone_pattern = r'(?<!\w)(\w+)\s*\('
        standalone_matches = re.findall(standalone_pattern, expr_str)
        
        for func_name in standalone_matches:
            if func_name.lower() in ('if', 'else', 'while', 'for', 'do', 'case', 'return', 'new', 'delete', 'randomize', 'srandom'):
                continue
            
            full_call = f"{func_name}()"
            
            if any(c.full_call == full_call for c in self.method_calls):
                continue
            
            call_info = MethodCallInfo(
                caller_name="<self>",
                method_name=func_name,
                full_call=full_call,
                is_internal=current_class is not None,
                line_number=line_number,
                file_name=filename
            )
            self.method_calls.append(call_info)

    def get_summary(self) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("CLASS RELATIONSHIP AND CALL GRAPH SUMMARY")
        lines.append("=" * 60)
        
        lines.append(f"\nTotal Classes: {len(self.classes)}")
        lines.append(f"Total Relations: {len(self.relations)}")
        lines.append(f"Total Method Calls: {len(self.method_calls)}")
        
        relation_types = {}
        for r in self.relations:
            relation_types[r.relation_type] = relation_types.get(r.relation_type, 0) + 1
        
        lines.append("\nRelations by Type:")
        for rtype, count in sorted(relation_types.items()):
            lines.append(f"  {rtype}: {count}")
        
        return "\n".join(lines)
