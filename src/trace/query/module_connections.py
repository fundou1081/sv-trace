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
    
    def _extract_modules(self, root) -> None:
        current_module = ""
        
        def visitor(node):
            nonlocal current_module
            kind_name = node.kind.name if hasattr(node.kind, 'name') else ''
            
            if kind_name == 'ModuleDeclaration':
                current_module = self._get_module_name(node)
                if current_module:
                    self._modules[current_module] = {'ports': {}}
            
            # 两种端口声明语法:
            # 1. AnsiPortDeclaration: input clk; output [7:0] data;
            elif kind_name == 'AnsiPortDeclaration' and current_module:
                port_info = self._extract_port(node)
                if port_info:
                    self._modules[current_module]['ports'][port_info['name']] = port_info
            
            # 2. PortDeclaration (in port list): input clk; 
            elif kind_name == 'PortDeclaration' and current_module:
                port_info = self._extract_port(node)
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
        try:
            port_name = None
            direction = 'input'
            
            for child in node:
                ckind = child.kind.name if hasattr(child.kind, 'name') else ''
                
                if ckind == 'PortDirection':
                    dir_text = str(child).strip().lower()
                    if 'out' in dir_text:
                        direction = 'output'
                    elif 'inout' in dir_text:
                        direction = 'inout'
                
                elif ckind == 'IdentifierName':
                    port_name = str(child).strip()
                
                elif ckind == 'VariableDeclarator':
                    # 处理 data_in[7:0] 这样的声明
                    decl_name = str(child).strip()
                    if '[' in decl_name:
                        port_name = decl_name.split('[')[0].strip()
                    else:
                        port_name = decl_name
            
            if port_name:
                return {'name': port_name, 'direction': direction, 'signal': port_name}
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
