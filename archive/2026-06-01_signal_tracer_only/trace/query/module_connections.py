"""ModuleConnectionsQuery - 模块端口连接追踪

场景B: 给定模块，追踪所有端口连接关系
"""

import sys
import os
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from trace.core.interfaces import TraceResult
import pyslang


@dataclass
class PortConnection:
    """端口连接信息"""
    port_name: str
    direction: str
    width: str
    internal_signal: str
    external_module: str = ''
    external_port: str = ''
    confidence: str = "high"
    caveats: List[str] = field(default_factory=list)


@dataclass
class ModuleConnectionsResult:
    """模块连接追踪结果"""
    module: str
    inputs: List[PortConnection] = field(default_factory=list)
    outputs: List[PortConnection] = field(default_factory=list)
    inouts: List[PortConnection] = field(default_factory=list)
    confidence: str = "high"
    caveats: List[str] = field(default_factory=list)


class ModuleConnectionsQuery:
    """模块端口连接追踪查询"""
    
    def __init__(self, parser, verbose: bool = True):
        self.parser = parser
        self.verbose = verbose
        self._modules: Dict[str, Dict] = {}
        self._clock_signals: Set[str] = set()
        self._reset_signals: Set[str] = set()
        
        self._collect_all()
    
    def _collect_all(self) -> None:
        for fname, tree in self.parser.trees.items():
            if not tree or not tree.root:
                continue
            self._extract_modules(tree.root)
            self._extract_clock_reset(tree.root)
    
    def _extract_modules(self, root) -> None:
        """从 AST 提取所有模块及其端口
        
        PortDeclaration 结构:
        - VariablePortHeader: input/output/inout + 类型
          - InputKeyword/OutputKeyword/InoutKeyword
          - ImplicitType: [7:0] 或为空
        - SeparatedList:
          - Declarator:
            - Identifier: 端口名
        """
        current_module = ""
        
        def visitor(node):
            nonlocal current_module
            kind_name = node.kind.name if hasattr(node.kind, 'name') else ''
            
            if kind_name == 'ModuleDeclaration':
                current_module = self._get_module_name(node)
                if current_module:
                    self._modules[current_module] = {'ports': {}}
            
            # PortDeclaration: input [7:0] data_in;
            elif kind_name == 'PortDeclaration' and current_module:
                port_info = self._extract_port(node)
                if port_info:
                    self._modules[current_module]['ports'][port_info['name']] = port_info
            
            # ImplicitAnsiPort: input clk (在 ImplicitAnsiPortList 中)
            elif kind_name == 'ImplicitAnsiPort' and current_module:
                port_info = self._extract_ansi_port(node)
                if port_info:
                    self._modules[current_module]['ports'][port_info['name']] = port_info
            
            return pyslang.VisitAction.Advance
        
        root.visit(visitor)
    
    def _get_module_name(self, node) -> Optional[str]:
        try:
            if hasattr(node, 'header') and hasattr(node.header, 'name'):
                name = node.header.name
                if hasattr(name, 'text'):
                    return name.text.strip()
                return str(name).strip()
        except:
            pass
        return None
    
    def _extract_port(self, node) -> Optional[Dict]:
        """从 PortDeclaration 提取端口信息
        
        PortDeclaration 结构:
        - VariablePortHeader: input/output/inout + 类型
          - InputKeyword/OutputKeyword/InoutKeyword
          - ImplicitType: [7:0] 或空
        - SeparatedList:
          - Declarator: 端口名
            - Identifier: 端口名
        """
        try:
            port_name = None
            direction = 'input'
            width = ''
            
            def find_in_children(n, kind_list):
                """递归查找指定类型的节点"""
                for child in n:
                    ckind = child.kind.name if hasattr(child.kind, 'name') else ''
                    if ckind in kind_list:
                        return child
                return None
            
            for child in node:
                ckind = child.kind.name if hasattr(child.kind, 'name') else ''
                
                # 方向关键字在 VariablePortHeader -> InputKeyword/OutputKeyword
                if ckind == 'VariablePortHeader':
                    dir_node = find_in_children(child, ('InputKeyword', 'OutputKeyword', 'InoutKeyword', 'InputKeyword'))
                    if dir_node:
                        dir_str = str(dir_node).strip()
                        # 使用精确匹配避免 'Output' 匹配到 'Input'
                        if dir_str == 'output':
                            direction = 'output'
                        elif dir_str == 'inout':
                            direction = 'inout'
                        else:
                            direction = 'input'
                    
                    # 宽度在 ImplicitType
                    type_node = find_in_children(child, ('ImplicitType',))
                    if type_node:
                        type_str = str(type_node)
                        if '[' in type_str:
                            start = type_str.find('[')
                            end = type_str.find(']')
                            if start != -1 and end != -1:
                                width = type_str[start+1:end]
                
                # 端口名在 SeparatedList -> Declarator -> Identifier
                elif ckind == 'SeparatedList':
                    decl_node = find_in_children(child, ('Declarator',))
                    if decl_node:
                        id_node = find_in_children(decl_node, ('Identifier',))
                        if id_node:
                            port_name = str(id_node).strip()
            
            if port_name:
                return {
                    'name': port_name,
                    'direction': direction,
                    'width': width,
                    'signal': port_name
                }
        except:
            pass
        return None
    
    def _extract_clock_reset(self, root) -> None:
        """从 always_ff @(posedge clk or negedge rst_n) 提取时钟和复位
        
        结构:
        - AlwaysFFBlock
          - TimingControlStatement
            - EventControlWithExpression
              - ParenthesizedEventExpression
                - BinaryEventExpression: posedge clk or negedge rst_n
                  - SignalEventExpression: posedge clk
                  - SignalEventExpression: negedge rst_n
        
        常用时钟/复位命名:
        - 时钟: clk, clock, sys_clk, core_clk, ref_clk
        - 复位: rst_n, reset_n, rst, reset, async_rst_n
        """
        common_clocks = {'clk', 'clock', 'sys_clk', 'core_clk', 'ref_clk', 'clk_i'}
        common_resets = {'rst_n', 'reset_n', 'rst', 'reset', 'async_rst_n', 'rst_ni'}
        
        def extract_signal_from_event(node):
            """从事件表达式中提取信号名"""
            sigs = []
            kn = node.kind.name if hasattr(node.kind, 'name') else ''
            
            if kn == 'SignalEventExpression':
                node_str = str(node)
                for prefix in ['posedge ', 'negedge ']:
                    if prefix in node_str:
                        sig = node_str.replace(prefix, '').strip()
                        if sig:
                            sigs.append(sig)
                        break
            
            elif kn in ('BinaryEventExpression', 'ParenthesizedEventExpression'):
                for child in node:
                    sigs.extend(extract_signal_from_event(child))
            
            return sigs
        
        def visitor(node):
            kn = node.kind.name if hasattr(node.kind, 'name') else ''
            
            if kn == 'AlwaysFFBlock':
                # 找到 TimingControlStatement
                for child in node:
                    ckn = child.kind.name if hasattr(child.kind, 'name') else ''
                    if ckn == 'TimingControlStatement':
                        for subchild in child:
                            skn = subchild.kind.name if hasattr(subchild.kind, 'name') else ''
                            if skn == 'EventControlWithExpression':
                                for subsubchild in subchild:
                                    sskn = subsubchild.kind.name if hasattr(subsubchild.kind, 'name') else ''
                                    if sskn == 'ParenthesizedEventExpression':
                                        signals = extract_signal_from_event(subsubchild)
                                        for sig in signals:
                                            if sig in common_clocks:
                                                self._clock_signals.add(sig)
                                            if sig in common_resets:
                                                self._reset_signals.add(sig)
            
            return pyslang.VisitAction.Advance
        
        root.visit(visitor)
    
    def _extract_ansi_port(self, node) -> Optional[Dict]:
        """从 ImplicitAnsiPort 提取端口信息
        
        ImplicitAnsiPort 结构:
        - VariablePortHeader:
          - InputKeyword/OutputKeyword/InoutKeyword
          - ImplicitType: [7:0] 或空
        - SimplePortDeclarator: 端口名
        """
        try:
            port_name = None
            direction = 'input'
            width = ''
            
            def find_in_children(n, kind_list):
                for child in n:
                    ckind = child.kind.name if hasattr(child.kind, 'name') else ''
                    if ckind in kind_list:
                        return child
                return None
            
            for child in node:
                ckind = child.kind.name if hasattr(child.kind, 'name') else ''
                
                if ckind == 'VariablePortHeader':
                    dir_node = find_in_children(child, ('InputKeyword', 'OutputKeyword', 'InoutKeyword'))
                    if dir_node:
                        dir_str = str(dir_node).strip()
                        if dir_str == 'output':
                            direction = 'output'
                        elif dir_str == 'inout':
                            direction = 'inout'
                        else:
                            direction = 'input'
                    
                    type_node = find_in_children(child, ('ImplicitType',))
                    if type_node:
                        type_str = str(type_node)
                        if '[' in type_str:
                            start = type_str.find('[')
                            end = type_str.find(']')
                            if start != -1 and end != -1:
                                width = type_str[start+1:end]
                
                elif ckind == 'SimplePortDeclarator':
                    port_name = str(child).strip()
                elif ckind == 'Declarator':
                    # 处理 Declarator 形式
                    for decl_child in child:
                        dkn = decl_child.kind.name if hasattr(decl_child.kind, 'name') else ''
                        if dkn == 'Identifier':
                            port_name = str(decl_child).strip()
            
            if port_name:
                return {
                    'name': port_name,
                    'direction': direction,
                    'width': width,
                    'signal': port_name
                }
        except:
            pass
        return None
    
    def trace(self, module_name: str) -> TraceResult:
        if module_name not in self._modules:
            return TraceResult.uncertain(data=None, reason=f"Module '{module_name}' not found")
        
        inputs, outputs, inouts = [], [], []
        ports = self._modules[module_name].get('ports', {})
        
        for name, info in ports.items():
            conn = PortConnection(
                port_name=name,
                direction=info['direction'],
                width='',
                internal_signal=info['signal'],
            )
            if info['direction'] == 'input':
                inputs.append(conn)
            elif info['direction'] == 'output':
                outputs.append(conn)
            else:
                inouts.append(conn)
        
        confidence = "high"
        caveats = []
        if not inputs and not outputs:
            caveats.append("No ports found")
            confidence = "uncertain"
        
        return TraceResult(
            data=ModuleConnectionsResult(
                module=module_name,
                inputs=inputs, outputs=outputs, inouts=inouts,
                confidence=confidence, caveats=caveats
            ),
            confidence=confidence, caveats=caveats
        )
