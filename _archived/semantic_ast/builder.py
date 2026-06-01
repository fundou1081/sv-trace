"""
semantic_ast.builder - 语义 AST 构建器

核心构建逻辑，将 pyslang SyntaxTree 转换为 SemanticAST。

架构:
1. 遍历模块，建立作用域树
2. 在每个作用域中建立信号节点
3. 遍历 always_ff/always_comb/continuous_assign，建立驱动关系
4. 构建负载关系（信号被谁使用）
5. 处理 generate 块（可选展开）

与旧架构对比:
- 旧: Pass1 ScopeBuilder → Pass2 Extractors (分离)
- 新: 一次性构建，驱动/负载关系直接内聚在节点中
"""

import pyslang
from pyslang import (
    SyntaxTree, SyntaxKind, SyntaxNode,
    Compilation, TokenKind
)
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, field

from semantic_ast.nodes import (
    SemanticNodeKind,
    SemanticSignalNode,
    SemanticDriverRef,
    SemanticLoadRef,
    SemanticScopeNode,
    SemanticAST,
    ConfidenceLevel,
)
from semantic_ast.expr_parser import (
    get_identifier_text,
    collect_expression_identifiers,
    extract_driver_info,
    get_signal_port_direction,
    extract_signal_info_from_declaration,
)


class SemanticASTBuilder:
    """语义 AST 构建器
    
    将 pyslang SyntaxTree 转换为 SemanticAST。
    
    使用方式:
        builder = SemanticASTBuilder()
        sem_ast = builder.build(tree)
    
    关键设计:
    - 一次性遍历完成所有构建（相比旧架构的 3-Pass）
    - 驱动/负载关系直接内聚在 SemanticSignalNode 中
    - 不再需要分离的 ScopeTree + SymbolTable
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self._sem_ast: Optional[SemanticAST] = None
        self._current_scope_id: str = ""
        self._hierarchy_stack: List[str] = []
        self._scope_counter: Dict[str, int] = {}
        self._signal_refs: Dict[str, List[str]] = {}  # signal → loads 关系
    
    def build(self, tree: SyntaxTree, source_file: str = "") -> SemanticAST:
        """构建语义 AST
        
        Args:
            tree: pyslang SyntaxTree
            source_file: 源文件路径（可选）
        
        Returns:
            SemanticAST: 语义 AST
        """
        self._sem_ast = SemanticAST(source_file=source_file)
        self._scope_counter = {}
        
        # 找到根模块
        root = tree.root
        root_type = root.kind.name if hasattr(root.kind, 'name') else str(root.kind)
        
        if root_type == 'CompilationUnit':
            # CompilationUnit 结构: [0] SyntaxList (modules), [1] EndOfFile
            # 遍历所有成员
            for member in root:
                mtype = member.kind.name if hasattr(member.kind, 'name') else str(member.kind)
                if mtype == 'ModuleDeclaration':
                    self._process_module(member)
                elif mtype == 'SyntaxList':
                    # 模块可能在 SyntaxList 中
                    for sl_child in member:
                        sltype = sl_child.kind.name if hasattr(sl_child.kind, 'name') else str(sl_child.kind)
                        if sltype == 'ModuleDeclaration':
                            self._process_module(sl_child)
        elif root_type == 'ModuleDeclaration':
            self._process_module(root)
        else:
            # 尝试在子节点中找 ModuleDeclaration
            self._find_and_process_modules(root)
        
        # 构建负载关系 (从信号引用建立)
        self._build_load_relations()
        
        return self._sem_ast
    
    def _find_and_process_modules(self, node):
        """递归查找并处理模块节点"""
        kn = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
        
        if kn == 'ModuleDeclaration':
            self._process_module(node)
            return
        
        try:
            for child in node:
                self._find_and_process_modules(child)
        except:
            pass
    
    def _process_module(self, module_node: SyntaxNode):
        """处理模块声明"""
        # 获取模块名
        header = getattr(module_node, 'header', None)
        module_name = ""
        if header and hasattr(header, 'name'):
            ident = getattr(header, 'name', None)
            if ident:
                module_name = getattr(ident, 'valueText', '') or getattr(ident, 'text', '') or ''
        
        if not module_name:
            module_name = "anonymous_module"
        
        # 设置根模块名
        if not self._sem_ast.root_module:
            self._sem_ast.root_module = module_name
        
        # 创建模块作用域
        scope_id = module_name
        scope = SemanticScopeNode(
            scope_id=scope_id,
            kind=SemanticNodeKind.MODULE,
            name=module_name,
            hierarchy_path=module_name,
            _node=module_node,
        )
        
        self._push_scope(scope)
        self._sem_ast.add_scope(scope)
        
        # 处理端口
        self._process_module_ports(header, scope)
        
        # 处理模块成员
        # 模块成员在 SyntaxList 中
        members = getattr(module_node, 'members', None)
        if members is None:
            # 尝试从 SyntaxList 获取
            for child in module_node:
                kn = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
                if kn == 'SyntaxList':
                    # 这个 SyntaxList 包含模块成员
                    for member in child:
                        self._process_module_member(member, scope)
                elif kn in ('DataDeclaration', 'AlwaysFFBlock', 'AlwaysCombBlock', 
                           'ContinuousAssign', 'HierarchyInstantiation', 'GenerateRegion'):
                    self._process_module_member(child, scope)
        else:
            if hasattr(members, '__iter__'):
                for member in members:
                    self._process_module_member(member, scope)
        
        self._pop_scope()
    
    def _process_module_ports(self, header, scope: SemanticScopeNode):
        """处理模块端口"""
        if not header:
            return
        
        # 获取端口列表
        port_list = getattr(header, 'ports', None)
        if not port_list:
            # 尝试从 portList 获取
            port_list = getattr(header, 'portList', None)
        
        if port_list and hasattr(port_list, 'ports'):
            for port in port_list.ports:
                if port is None:
                    continue
                
                port_name = ""
                port_dir = None
                
                # 检查是否是 ImplicitAnsiPort
                if hasattr(port, 'identifier'):
                    ident = getattr(port, 'identifier', None)
                    if ident:
                        port_name = getattr(ident, 'valueText', '') or ''
                
                # 检查方向
                direction = getattr(port, 'direction', None)
                if direction and hasattr(direction, 'name'):
                    dir_name = direction.name
                    if 'Input' in dir_name:
                        port_dir = 'input'
                    elif 'Output' in dir_name:
                        port_dir = 'output'
                    elif 'InOut' in dir_name:
                        port_dir = 'inout'
                
                if port_name:
                    scope.ports_input.append(port_name) if port_dir == 'input' else None
                    scope.ports_output.append(port_name) if port_dir == 'output' else None
                    scope.ports_inout.append(port_name) if port_dir == 'inout' else None
    
    def _process_module_member(self, member: SyntaxNode, scope: SemanticScopeNode):
        """处理模块成员"""
        kn = member.kind.name if hasattr(member.kind, 'name') else str(member.kind)
        
        if kn == 'DataDeclaration':
            self._process_data_declaration(member, scope)
        elif kn == 'AlwaysFFBlock':
            self._process_always_ff(member, scope)
        elif kn == 'AlwaysCombBlock':
            self._process_always_comb(member, scope)
        elif kn == 'AlwaysLatchBlock':
            self._process_always_latch(member, scope)
        elif kn == 'AlwaysBlock':
            self._process_always_block(member, scope)
        elif kn == 'ContinuousAssign':
            self._process_continuous_assign(member, scope)
        elif kn == 'HierarchyInstantiation':
            self._process_hierarchy_instantiation(member, scope)
        elif kn == 'GenerateRegion':
            self._process_generate_region(member, scope)
        elif kn == 'ModuleDeclaration':
            # nested module
            self._process_module(member)
    
    def _process_data_declaration(self, decl: SyntaxNode, scope: SemanticScopeNode):
        """处理数据声明"""
        # 遍历声明符列表
        # DataDeclaration 结构: [SyntaxList, TokenList, LogicType, SeparatedList, Semicolon]
        for child in decl:
            kn = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            
            if kn == 'Declarator':
                sig = self._create_signal_from_declarator(child, scope)
                if sig:
                    scope.add_signal(sig)
                    self._sem_ast.add_global_signal(sig, sig.name)
            elif kn == 'SeparatedList':
                # SeparatedList 包含多个 Declarator
                for item in child:
                    ikn = item.kind.name if hasattr(item.kind, 'name') else str(item.kind)
                    if ikn == 'Declarator':
                        sig = self._create_signal_from_declarator(item, scope)
                        if sig:
                            scope.add_signal(sig)
                            self._sem_ast.add_global_signal(sig, sig.name)
    
    def _create_signal_from_declarator(self, declarator: SyntaxNode, scope: SemanticScopeNode) -> Optional[SemanticSignalNode]:
        """从 Declarator 创建信号节点"""
        ident = getattr(declarator, 'identifier', None)
        if not ident:
            return None
        
        name = getattr(ident, 'valueText', '') or ''
        if not name:
            return None
        
        sig = SemanticSignalNode(
            name=name,
            resolved_name=f"{scope.hierarchy_path}.{name}",
            scope_id=scope.scope_id,
            declaration_line=0,  # TODO: 从 sourceRange 获取
            _node=declarator,
        )
        
        # 检查位宽
        if hasattr(declarator, 'dimensions'):
            for dim in declarator.dimensions:
                dim_text = getattr(dim, 'text', '') or ''
                if '[' in dim_text:
                    # 解析位宽
                    import re
                    m = re.search(r'\[(\d+):0\]', dim_text)
                    if m:
                        sig.width = int(m.group(1)) + 1
        
        return sig
    
    def _process_always_ff(self, node: SyntaxNode, scope: SemanticScopeNode):
        """处理 always_ff 块"""
        # 创建 always_ff 作用域
        scope_id = self._gen_scope_id(scope.scope_id, 'always_ff')
        always_scope = SemanticScopeNode(
            scope_id=scope_id,
            kind=SemanticNodeKind.ALWAYS_FF,
            name=f"{scope.name}.always_ff",
            hierarchy_path=f"{scope.hierarchy_path}.always_ff",
            parent_scope=scope.scope_id,
            _node=node,
        )
        
        self._push_scope(always_scope)
        self._sem_ast.add_scope(always_scope)
        
        # 提取时钟
        clocks = self._extract_clocks(node)
        clock = clocks[0] if clocks else ""
        
        # 提取复位
        resets = self._extract_resets(node)
        reset = resets[0] if resets else ""
        
        # 遍历块内语句
        self._process_block_statements(node, always_scope, 'always_ff', clock, reset)
        
        self._pop_scope()
    
    def _process_always_comb(self, node: SyntaxNode, scope: SemanticScopeNode):
        """处理 always_comb 块"""
        scope_id = self._gen_scope_id(scope.scope_id, 'always_comb')
        always_scope = SemanticScopeNode(
            scope_id=scope_id,
            kind=SemanticNodeKind.ALWAYS_COMB,
            name=f"{scope.name}.always_comb",
            hierarchy_path=f"{scope.hierarchy_path}.always_comb",
            parent_scope=scope.scope_id,
            _node=node,
        )
        
        self._push_scope(always_scope)
        self._sem_ast.add_scope(always_scope)
        
        self._process_block_statements(node, always_scope, 'always_comb', '', '')
        
        self._pop_scope()
    
    def _process_always_latch(self, node: SyntaxNode, scope: SemanticScopeNode):
        """处理 always_latch 块"""
        scope_id = self._gen_scope_id(scope.scope_id, 'always_latch')
        always_scope = SemanticScopeNode(
            scope_id=scope_id,
            kind=SemanticNodeKind.ALWAYS_LATCH,
            name=f"{scope.name}.always_latch",
            hierarchy_path=f"{scope.hierarchy_path}.always_latch",
            parent_scope=scope.scope_id,
            _node=node,
        )
        
        self._push_scope(always_scope)
        self._sem_ast.add_scope(always_scope)
        
        self._process_block_statements(node, always_scope, 'always_latch', '', '')
        
        self._pop_scope()
    
    def _process_always_block(self, node: SyntaxNode, scope: SemanticScopeNode):
        """处理 always 块"""
        scope_id = self._gen_scope_id(scope.scope_id, 'always')
        always_scope = SemanticScopeNode(
            scope_id=scope_id,
            kind=SemanticNodeKind.ALWAYS,
            name=f"{scope.name}.always",
            hierarchy_path=f"{scope.hierarchy_path}.always",
            parent_scope=scope.scope_id,
            _node=node,
        )
        
        self._push_scope(always_scope)
        self._sem_ast.add_scope(always_scope)
        
        self._process_block_statements(node, always_scope, 'always', '', '')
        
        self._pop_scope()
    
    def _process_continuous_assign(self, node: SyntaxNode, scope: SemanticScopeNode):
        """处理 continuous assign"""
        # continuous assign 的驱动关系
        for child in node:
            kn = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            
            if kn == 'SeparatedList':
                for item in child:
                    ikn = item.kind.name if hasattr(item.kind, 'name') else str(item.kind)
                    
                    if ikn == 'AssignmentExpression':
                        self._process_assignment(item, scope, 'continuous')
    
    def _process_hierarchy_instantiation(self, node: SyntaxNode, scope: SemanticScopeNode):
        """处理模块实例化"""
        module_name = getattr(node, 'moduleName', None)
        if module_name:
            module_name = getattr(module_name, 'text', '') or ''
        
        # 获取实例名
        for child in node:
            kn = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            if kn == 'HierarchicalInstance':
                inst_name = getattr(child, 'instanceName', None)
                if inst_name:
                    inst_name = getattr(inst_name, 'text', '') or ''
                    
                    # 创建实例作用域
                    inst_scope_id = f"{scope.scope_id}.{inst_name}"
                    inst_scope = SemanticScopeNode(
                        scope_id=inst_scope_id,
                        kind=SemanticNodeKind.INSTANCE,
                        name=inst_name,
                        hierarchy_path=f"{scope.hierarchy_path}.{inst_name}",
                        instance_of=module_name,
                        instance_name=inst_name,
                        parent_scope=scope.scope_id,
                        _node=node,
                    )
                    
                    self._push_scope(inst_scope)
                    self._sem_ast.add_scope(inst_scope)
                    scope.children.append(inst_scope_id)
                    self._pop_scope()
    
    def _process_generate_region(self, node: SyntaxNode, scope: SemanticScopeNode):
        """处理 generate 块"""
        # GenerateRegion 结构:
        # [0] SyntaxList, [1] GenerateKeyword, [2] SyntaxList, [3] EndGenerateKeyword
        # 需要从 index 2 的 SyntaxList 获取实际内容
        children = list(node)
        content_list = None
        for i, child in enumerate(children):
            kn = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            if kn == 'SyntaxList' and i == 2:
                content_list = child
                break
        
        if content_list is None:
            # Fallback: 遍历找 SyntaxList
            for child in node:
                if hasattr(child, 'kind') and child.kind.name == 'SyntaxList':
                    content_list = child
                    break
        
        if content_list:
            for child in content_list:
                kn = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
                
                if kn == 'IfGenerate':
                    self._process_generate_if(child, scope)
                elif kn == 'LoopGenerate':
                    self._process_generate_for(child, scope)
                elif kn == 'CaseGenerate':
                    self._process_generate_case(child, scope)
                elif kn == 'GenerateBlock':
                    self._process_generate_block(child, scope)
    
    def _process_generate_if(self, node: SyntaxNode, scope: SemanticScopeNode):
        """处理 generate if"""
        cond = getattr(node, 'condition', None)
        cond_text = getattr(cond, 'text', '') if cond else ''
        
        scope_id = self._gen_scope_id(scope.scope_id, 'generate_if')
        gen_scope = SemanticScopeNode(
            scope_id=scope_id,
            kind=SemanticNodeKind.GENERATE_IF,
            name=f"{scope.name}.gen_if",
            hierarchy_path=f"{scope.hierarchy_path}.gen_if",
            parent_scope=scope.scope_id,
            _node=node,
        )
        
        self._push_scope(gen_scope)
        self._sem_ast.add_scope(gen_scope)
        
        # 处理 generate block
        for child in node:
            kn = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            if kn == 'GenerateBlock':
                self._process_generate_block(child, gen_scope)
        
        self._pop_scope()
    
    def _process_generate_for(self, node: SyntaxNode, scope: SemanticScopeNode):
        """处理 generate for"""
        scope_id = self._gen_scope_id(scope.scope_id, 'generate_for')
        gen_scope = SemanticScopeNode(
            scope_id=scope_id,
            kind=SemanticNodeKind.GENERATE_FOR,
            name=f"{scope.name}.gen_for",
            hierarchy_path=f"{scope.hierarchy_path}.gen_for",
            parent_scope=scope.scope_id,
            _node=node,
        )
        
        self._push_scope(gen_scope)
        self._sem_ast.add_scope(gen_scope)
        
        # 处理 generate block
        for child in node:
            kn = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            if kn == 'GenerateBlock':
                self._process_generate_block(child, gen_scope)
        
        self._pop_scope()
    
    def _process_generate_case(self, node: SyntaxNode, scope: SemanticScopeNode):
        """处理 generate case"""
        scope_id = self._gen_scope_id(scope.scope_id, 'generate_case')
        gen_scope = SemanticScopeNode(
            scope_id=scope_id,
            kind=SemanticNodeKind.GENERATE_CASE,
            name=f"{scope.name}.gen_case",
            hierarchy_path=f"{scope.hierarchy_path}.gen_case",
            parent_scope=scope.scope_id,
            _node=node,
        )
        
        self._push_scope(gen_scope)
        self._sem_ast.add_scope(gen_scope)
        
        self._pop_scope()
    
    def _process_generate_block(self, node: SyntaxNode, scope: SemanticScopeNode):
        """处理 generate block"""
        # 获取 generate block 的名称
        block_name = ""
        for child in node:
            kn = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            if kn == 'NamedBlockClause':
                for nc in child:
                    nckn = nc.kind.name if hasattr(nc.kind, 'name') else str(nc.kind)
                    if nckn == 'Identifier':
                        block_name = getattr(nc, 'valueText', '') or getattr(nc, 'text', '') or ''
                        break
        
        # GenerateBlock 结构:
        # [0] SyntaxList, [1] BeginKeyword, [2] NamedBlockClause, [3] SyntaxList(content), [4] EndKeyword
        # 需要从 index 3 的 SyntaxList 获取实际内容
        children = list(node)
        content_list = None
        for i, child in enumerate(children):
            kn = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            if kn == 'SyntaxList' and i == 3:
                content_list = child
                break
        
        if content_list is None:
            # Fallback: 遍历找 SyntaxList
            for child in node:
                if hasattr(child, 'kind') and child.kind.name == 'SyntaxList':
                    content_list = child
                    break
        
        if content_list:
            for child in content_list:
                kn = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
                if kn == 'DataDeclaration':
                    self._process_data_declaration(child, scope)
                elif kn == 'AlwaysFFBlock':
                    self._process_always_ff(child, scope)
                elif kn == 'AlwaysCombBlock':
                    self._process_always_comb(child, scope)
                elif kn == 'AlwaysLatchBlock':
                    self._process_always_latch(child, scope)
                elif kn == 'AlwaysBlock':
                    self._process_always_block(child, scope)
                elif kn == 'ContinuousAssign':
                    self._process_continuous_assign(child, scope)
                elif kn == 'HierarchyInstantiation':
                    self._process_hierarchy_instantiation(child, scope)
                elif kn == 'GenerateRegion':
                    self._process_generate_region(child, scope)
                elif kn == 'GenerateBlock':
                    self._process_generate_block(child, scope)
    
    def _process_block_statements(self, node: SyntaxNode, scope: SemanticScopeNode, kind: str, clock: str, reset: str):
        """处理过程块语句 (always_ff/always_comb 等)"""
        # always_ff 的语句在 TimingControlStatement.statement 中
        # always_comb 直接是 SequentialBlockStatement
        # 先找到实际的语句节点
        statement = getattr(node, 'statement', None)
        if statement is None:
            return
        
        # 检查是否是 TimingControlStatement
        stmt_kind = statement.kind.name if hasattr(statement.kind, 'name') else str(statement.kind)
        if stmt_kind == 'TimingControlStatement':
            # TimingControlStatement.statement 才是实际语句
            actual_stmt = getattr(statement, 'statement', None)
            if actual_stmt:
                self._process_block_statements_inner(actual_stmt, scope, kind, clock, reset)
        else:
            self._process_block_statements_inner(statement, scope, kind, clock, reset)
    
    def _process_block_statements_inner(self, node: SyntaxNode, scope: SemanticScopeNode, kind: str, clock: str, reset: str):
        """实际处理块语句的内部实现"""
        kn = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
        
        if kn == 'SequentialBlockStatement':
            self._process_sequential_block(node, scope, kind, clock, reset)
        elif kn == 'ExpressionStatement':
            self._process_expression_statement(node, scope, kind, clock, reset)
        elif kn == 'ConditionalStatement':
            self._process_conditional_statement(node, scope, kind, clock, reset)
        elif kn == 'TimingControlStatement':
            # 嵌套的 timing control
            actual_stmt = getattr(node, 'timing', None) or getattr(node, 'statement', None)
            if actual_stmt:
                self._process_block_statements_inner(actual_stmt, scope, kind, clock, reset)
    
    def _process_sequential_block(self, node: SyntaxNode, scope: SemanticScopeNode, kind: str, clock: str, reset: str):
        """处理顺序块语句"""
        for child in node:
            kn = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            
            if kn == 'SyntaxList':
                for item in child:
                    ikn = item.kind.name if hasattr(item.kind, 'name') else str(item.kind)
                    
                    if ikn == 'ExpressionStatement':
                        self._process_expression_statement(item, scope, kind, clock, reset)
                    elif ikn == 'ConditionalStatement':
                        self._process_conditional_statement(item, scope, kind, clock, reset)
                    elif ikn == 'SequentialBlockStatement':
                        self._process_sequential_block(item, scope, kind, clock, reset)
    
    def _process_expression_statement(self, node: SyntaxNode, scope: SemanticScopeNode, kind: str, clock: str, reset: str):
        """处理表达式语句"""
        for child in node:
            kn = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            
            if kn in ('NonblockingAssignmentExpression', 'AssignmentExpression'):
                self._process_assignment(child, scope, kind, clock, reset)
    
    def _process_conditional_statement(self, node: SyntaxNode, scope: SemanticScopeNode, kind: str, clock: str, reset: str):
        """处理条件语句"""
        # 检查 if 条件中的复位检测
        sync_reset = reset
        
        # ConditionalStatement 结构:
        # [0] SyntaxList, [1] IfKeyword, [2] OpenParenthesis, 
        # [3] ConditionalPredicate, [4] CloseParenthesis, 
        # [5] SequentialBlockStatement (if true branch), 
        # [6] ElseClause
        
        children = list(node)
        
        for child in children:
            kn = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            
            if kn == 'ConditionalPredicate':
                # 提取条件中的信号，用于检测复位
                predicates = []
                collect_expression_identifiers(child, predicates)
                for pred in predicates:
                    if 'rst' in pred.lower():
                        sync_reset = pred
                        break
            
            elif kn == 'SequentialBlockStatement':
                self._process_sequential_block(child, scope, kind, clock, sync_reset)
            
            elif kn == 'ExpressionStatement':
                self._process_expression_statement(child, scope, kind, clock, sync_reset)
            
            elif kn == 'ElseClause':
                # ElseClause 结构: [0] ElseKeyword, [1] SequentialBlockStatement
                for ec_child in child:
                    eckn = ec_child.kind.name if hasattr(ec_child.kind, 'name') else str(ec_child.kind)
                    if eckn == 'SequentialBlockStatement':
                        self._process_sequential_block(ec_child, scope, kind, clock, sync_reset)
                    elif eckn == 'ExpressionStatement':
                        self._process_expression_statement(ec_child, scope, kind, clock, sync_reset)
                    elif eckn == 'ConditionalStatement':
                        # else if
                        self._process_conditional_statement(ec_child, scope, kind, clock, sync_reset)
            
            elif kn == 'ConditionalStatement':
                # else if - 递归处理
                self._process_conditional_statement(child, scope, kind, clock, sync_reset)
    
    def _process_assignment(self, node: SyntaxNode, scope: SemanticScopeNode, kind: str, clock: str = "", reset: str = ""):
        """处理赋值表达式
        
        这是核心方法，使用实验发现的 .left/.right API。
        """
        # 提取左值
        left = getattr(node, 'left', None)
        lhs_name = get_identifier_text(left)
        
        if not lhs_name:
            return
        
        # 提取右值
        right = getattr(node, 'right', None)
        rhs_identifiers = []
        if right:
            collect_expression_identifiers(right, rhs_identifiers)
        
        # 获取行号 (从 sourceRange.start.offset 估算)
        line = 0
        if hasattr(node, 'sourceRange') and node.sourceRange:
            try:
                line = node.sourceRange.start.offset
            except:
                pass
        
        # 创建或获取信号节点
        sig = scope.get_signal(lhs_name)
        if not sig:
            sig = SemanticSignalNode(
                name=lhs_name,
                resolved_name=f"{scope.hierarchy_path}.{lhs_name}",
                scope_id=scope.scope_id,
                declaration_line=line,
                _node=node,
            )
            scope.add_signal(sig)
            self._sem_ast.add_global_signal(sig, sig.name)
        
        # 创建驱动引用
        driver_ref = SemanticDriverRef(
            source_expr=' '.join(rhs_identifiers),
            source_scope=scope.scope_id,
            kind=kind,
            clock=clock,
            reset=reset,
            line=line,
            confidence=ConfidenceLevel.HIGH,
        )
        sig.add_driver(driver_ref)
        
        # 记录负载关系 (rhs 信号被 lhs 使用)
        for rhs_sig in rhs_identifiers:
            if rhs_sig not in self._signal_refs:
                self._signal_refs[rhs_sig] = []
            self._signal_refs[rhs_sig].append(lhs_name)
    
    def _extract_clocks(self, node: SyntaxNode) -> List[str]:
        """从 always_ff 块提取时钟"""
        clocks = []
        
        # 找到 TimingControlStatement
        timing = getattr(node, 'statement', None)
        if timing and hasattr(timing, 'timing'):
            timing = timing.timing
        
        if not timing:
            return clocks
        
        # 遍历找时钟信号
        def find_clocks(n):
            kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
            
            if kn == 'SignalEventExpression':
                # SignalEventExpression 结构: [0] EdgeKeyword, [1] IdentifierName
                for child in n:
                    ckn = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
                    if ckn == 'IdentifierName':
                        ident = get_identifier_text(child)
                        if ident:
                            clocks.append(ident)
            
            try:
                for child in n:
                    find_clocks(child)
            except:
                pass
        
        find_clocks(timing)
        return list(set(clocks))
    
    def _extract_resets(self, node: SyntaxNode) -> List[str]:
        """从 always_ff 块提取复位"""
        resets = []
        
        timing = getattr(node, 'statement', None)
        if timing and hasattr(timing, 'timing'):
            timing = timing.timing
        
        if not timing:
            return resets
        
        def find_resets(n):
            kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
            
            if kn == 'SignalEventExpression':
                edge = getattr(n, 'edge', None)
                if edge and hasattr(edge, 'kind'):
                    if edge.kind == TokenKind.NegEdgeKeyword:
                        expr = getattr(n, 'expr', None)
                        if expr:
                            ident = get_identifier_text(expr)
                            if ident and 'rst' in ident.lower():
                                resets.append(ident)
            
            try:
                for child in n:
                    find_resets(child)
            except:
                pass
        
        find_resets(timing)
        return list(set(resets))
    
    def _build_load_relations(self):
        """根据记录的引用关系构建负载关系"""
        for rhs_sig, used_in in self._signal_refs.items():
            target_sig = self._sem_ast.get_global_signal(rhs_sig)
            if not target_sig:
                continue
            
            for lhs_sig in used_in:
                load_ref = SemanticLoadRef(
                    load_expr=lhs_sig,
                    load_scope=self._current_scope_id,
                    context='driver_usage',
                    confidence=ConfidenceLevel.HIGH,
                )
                target_sig.add_load(load_ref)
    
    def _gen_scope_id(self, parent: str, kind: str) -> str:
        """生成唯一作用域 ID"""
        key = f"{parent}_{kind}"
        count = self._scope_counter.get(key, 0)
        self._scope_counter[key] = count + 1
        return f"{parent}.{kind}_{count}"
    
    def _push_scope(self, scope: SemanticScopeNode):
        """推入作用域栈"""
        self._hierarchy_stack.append(scope.scope_id)
        self._current_scope_id = scope.scope_id
    
    def _pop_scope(self):
        """弹出作用域栈"""
        if self._hierarchy_stack:
            self._hierarchy_stack.pop()
        self._current_scope_id = self._hierarchy_stack[-1] if self._hierarchy_stack else ""