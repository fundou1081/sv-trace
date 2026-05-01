"""
pyslang Helper - SystemVerilog AST 解析辅助工具
基于 pyslang 提供常用的解析功能

增强版: 添加解析警告，显式打印不支持的语法结构
"""

import pyslang
from pyslang import SyntaxKind
from typing import List, Dict, Optional, Callable, Set
from dataclasses import dataclass, field
import re

# 导入解析警告模块
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
try:
    from trace.parse_warn import (
        ParseWarningHandler,
        warn_unsupported,
        warn_error,
        WarningLevel
    )
except ImportError:
    class ParseWarningHandler:
        def __init__(self, verbose=True, component="pyslang_helper"):
            self.verbose = verbose
            self.component = component
        def warn_unsupported(self, node_kind, context="", suggestion="", component=None):
            if self.verbose:
                print(f"⚠️ [WARN][{component or self.component}] <{node_kind}> {suggestion} @ {context}")
        def warn_error(self, operation, exc, context="", component=None):
            if self.verbose:
                print(f"❌ [ERROR][{component or self.component}] {operation}: {exc} @ {context}")
        def get_report(self):
            return ""


# =============================================================================
# 数据类定义
# =============================================================================

@dataclass
class PortInfo:
    """端口信息"""
    name: str
    direction: str
    width: int = 1
    data_type: str = "logic"


@dataclass
class MemberInfo:
    """类成员信息"""
    name: str
    data_type: str
    width: int = 1
    qualifiers: str = ""


@dataclass
class ConstraintInfo:
    """约束信息"""
    name: str
    class_name: str = ""
    expr: str = ""


@dataclass
class MethodInfo:
    """方法信息"""
    name: str
    kind: str = "function"
    return_type: str = ""


@dataclass
class ClassInfo:
    """类信息"""
    name: str
    members: List[MemberInfo] = field(default_factory=list)
    methods: List[MethodInfo] = field(default_factory=list)
    constraints: List[ConstraintInfo] = field(default_factory=list)


@dataclass
class ModuleInfo:
    """模块信息"""
    name: str
    ports: List[PortInfo] = field(default_factory=list)
    parameters: List[Dict] = field(default_factory=list)


@dataclass
class FunctionInfo:
    """函数/任务信息"""
    name: str
    kind: str = "function"
    return_type: str = ""
    parameters: List[str] = field(default_factory=list)


# =============================================================================
# 解析器类
# =============================================================================

class SVParser:
    """
    SystemVerilog 解析器
    使用 pyslang AST 解析 SystemVerilog 代码
    
    增强版: 添加解析警告，显式打印不支持的语法结构
    """
    
    # 不支持的语法类型
    UNSUPPORTED_TYPES: Dict[str, str] = {
        'CovergroupDeclaration': '覆盖率group不支持提取',
        'PropertyDeclaration': 'property声明暂不支持',
        'SequenceDeclaration': 'sequence声明暂不支持',
        'InterfaceDeclaration': 'interface声明暂不支持提取',
        'PackageDeclaration': 'package声明暂不支持',
        'ProgramDeclaration': 'program块暂不支持',
        'ClockingBlock': 'clocking block暂不支持',
        'ModportItem': 'modport声明暂不支持',
        'ConstraintBlock': 'constraint块建议使用专用方法提取',
        'RandSequenceExpression': 'rand sequence暂不支持',
    }
    
    def __init__(self, code: str = "", verbose: bool = True):
        self.code = code
        self.tree = None
        self.root = None
        self.verbose = verbose
        self.warn_handler = ParseWarningHandler(
            verbose=verbose,
            component="SVParser"
        )
        self._unsupported_encountered: Set[str] = set()
        
        if code:
            self.parse(code)
    
    def parse(self, code: str) -> 'SVParser':
        """解析代码"""
        self.code = code
        try:
            self.tree = pyslang.SyntaxTree.fromText(code)
            self.root = self.tree.root
        except Exception as e:
            self.warn_handler.warn_error(
                "SyntaxTreeParsing",
                e,
                context="parse",
                component="SVParser"
            )
            raise
        return self
    
    def _check_unsupported_node(self, node, source: str = ""):
        """检查不支持的节点类型"""
        kind_name = str(node.kind) if hasattr(node, 'kind') else type(node).__name__
        
        if kind_name in self.UNSUPPORTED_TYPES:
            if kind_name not in self._unsupported_encountered:
                self.warn_handler.warn_unsupported(
                    kind_name,
                    context=source,
                    suggestion=self.UNSUPPORTED_TYPES[kind_name],
                    component="SVParser"
                )
                self._unsupported_encountered.add(kind_name)
        elif 'Declaration' in kind_name or 'Block' in kind_name:
            if kind_name not in self._unsupported_encountered and kind_name not in ['ModuleDeclaration', 'ClassDeclaration', 'CompilationUnit']:
                self.warn_handler.warn_unsupported(
                    kind_name,
                    context=source,
                    suggestion="可能影响解析完整性",
                    component="SVParser"
                )
                self._unsupported_encountered.add(kind_name)
    
    def find_nodes(self, kind_filter: Callable[[str], bool]) -> List:
        """查找所有匹配 kind_filter 的节点"""
        results = []
        
        def collect(node):
            try:
                if kind_filter(node.kind.name):
                    results.append(node)
            except Exception as e:
                self.warn_handler.warn_error(
                    "NodeFiltering",
                    e,
                    context="find_nodes",
                    component="SVParser"
                )
            return pyslang.VisitAction.Advance
        
        if self.root:
            self.root.visit(collect)
        return results
    
    def find_by_kind(self, kind_name: str) -> List:
        """查找指定 kind 的所有节点"""
        return self.find_nodes(lambda k: kind_name in k)
    
    def extract_modules(self) -> List[ModuleInfo]:
        """提取所有模块"""
        results = []
        
        def collect(node):
            try:
                if node.kind == SyntaxKind.ModuleDeclaration:
                    mod = ModuleInfo(name=str(node.header.name).strip())
                    
                    port_list = getattr(node.header, 'ports', None)
                    if port_list and hasattr(port_list, 'ports'):
                        port_list = port_list.ports
                    
                    if port_list:
                        for port in port_list:
                            if port is None:
                                continue
                            if not hasattr(port, 'declarator'):
                                continue
                            port_info = _extract_port(port, self.warn_handler)
                            if port_info:
                                mod.ports.append(port_info)
                    
                    results.append(mod)
                else:
                    self._check_unsupported_node(node, "extract_modules")
                    
            except Exception as e:
                self.warn_handler.warn_error(
                    "ModuleExtraction",
                    e,
                    context="extract_modules",
                    component="SVParser"
                )
            
            return pyslang.VisitAction.Advance
        
        if self.root:
            # 检查 root 本身是否是 ModuleDeclaration
            if self.root.kind == SyntaxKind.ModuleDeclaration:
                collect(self.root)
            else:
                # 遍历查找
                self.root.visit(collect)
        return results
    
    def extract_classes(self) -> List[ClassInfo]:
        """提取所有类"""
        results = []
        
        def collect(node):
            try:
                if node.kind == SyntaxKind.ClassDeclaration:
                    cls = self._extract_single_class(node, "")
                    if cls:
                        results.append(cls)
                else:
                    self._check_unsupported_node(node, "extract_classes")
                    
            except Exception as e:
                self.warn_handler.warn_error(
                    "ClassExtraction",
                    e,
                    context="extract_classes",
                    component="SVParser"
                )
            
            return pyslang.VisitAction.Advance
        
        if self.root:
            # 检查 root 本身是否是 ClassDeclaration
            if self.root.kind == SyntaxKind.ClassDeclaration:
                cls = self._extract_single_class(self.root, "")
                if cls:
                    results.append(cls)
            else:
                # 遍历查找
                self.root.visit(collect)
        return results
    
    def _extract_single_class(self, node, source: str = "") -> Optional[ClassInfo]:
        """提取单个类"""
        try:
            name = ""
            if hasattr(node, 'name') and node.name:
                name = str(node.name).strip()
            
            if not name:
                self.warn_handler.warn_unsupported(
                    "UnnamedClass",
                    context=source,
                    suggestion="class名为空",
                    component="SVParser"
                )
                return None
            
            cls = ClassInfo(name=name)
            
            # 提取 items
            if hasattr(node, 'items') and node.items:
                for item in node.items:
                    if item is None:
                        continue
                    kn = item.kind.name if hasattr(item.kind, 'name') else str(item.kind)
                    
                    try:
                        if 'Property' in kn or 'Rand' in kn:
                            mem = _extract_member(item, self.warn_handler)
                            if mem:
                                cls.members.append(mem)
                        elif 'Method' in kn and 'Declaration' in kn:
                            met = _extract_method(item, self.warn_handler)
                            if met:
                                cls.methods.append(met)
                        elif 'Constraint' in kn:
                            con = _extract_constraint(item, self.warn_handler)
                            if con:
                                cls.constraints.append(con)
                        else:
                            self._check_unsupported_node(item, f"class::{name}")
                    except Exception as e:
                        self.warn_handler.warn_error(
                            "ClassItemExtraction",
                            e,
                            context=f"class::{name}",
                            component="SVParser"
                        )
            
            return cls
        except Exception as e:
            self.warn_handler.warn_error(
                "SingleClassExtraction",
                e,
                context=f"class={source}",
                component="SVParser"
            )
            return None
    
    def extract_constraints(self) -> List[ConstraintInfo]:
        """提取所有约束"""
        results = []
        
        def collect(node):
            try:
                if node.kind == SyntaxKind.ConstraintDeclaration:
                    con = ConstraintInfo(
                        name=str(node.name).strip() if hasattr(node, 'name') else 'unknown',
                        expr=str(node)[:80].replace('\n', ' ').strip()
                    )
                    results.append(con)
            except Exception as e:
                self.warn_handler.warn_error(
                    "ConstraintExtraction",
                    e,
                    context="extract_constraints",
                    component="SVParser"
                )
            
            return pyslang.VisitAction.Advance
        
        if self.root:
            if self.root.kind == SyntaxKind.ConstraintDeclaration:
                collect(self.root)
            else:
                self.root.visit(collect)
        return results
    
    def extract_functions(self) -> List[FunctionInfo]:
        """提取所有函数/任务"""
        results = []
        
        def collect(node):
            try:
                kn = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
                if 'Function' in kn or 'Task' in kn:
                    if 'Declaration' in kn:
                        proto = getattr(node, 'prototype', None)
                        if proto:
                            name = str(proto.name).strip() if hasattr(proto, 'name') else 'unknown'
                            ret_type = str(proto.returnType).strip() if hasattr(proto, 'returnType') else ''
                            results.append(FunctionInfo(
                                name=name,
                                kind='task' if 'Task' in kn else 'function',
                                return_type=ret_type
                            ))
            except Exception as e:
                self.warn_handler.warn_error(
                    "FunctionExtraction",
                    e,
                    context="extract_functions",
                    component="SVParser"
                )
            
            return pyslang.VisitAction.Advance
        
        if self.root:
            self.root.visit(collect)
        return results
    
    def extract_clock_signals(self) -> List[Dict]:
        """提取时钟信号"""
        results = []
        
        def collect(node):
            try:
                kn = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
                
                if kn == 'ImplicitAnsiPort':
                    header = getattr(node, 'header', None)
                    if header:
                        direction = getattr(header, 'direction', None)
                        if direction and 'Input' in direction.kind.name:
                            decl = getattr(node, 'declarator', None)
                            if decl:
                                name = str(decl.name).strip()
                                if 'clk' in name.lower() or 'clock' in name.lower():
                                    results.append({'name': name, 'kind': 'clock_input'})
                
                elif kn == 'EventControlWithExpression':
                    clock_name = ''
                    edge = 'posedge'
                    
                    for child in node:
                        if child.kind.name == 'ParenthesizedEventExpression':
                            for c2 in child:
                                if c2.kind.name == 'SignalEventExpression':
                                    for c3 in c2:
                                        if 'Edge' in c3.kind.name:
                                            edge = 'posedge' if 'Pos' in c3.kind.name else 'negedge'
                                        if c3.kind.name == 'IdentifierName':
                                            clock_name = str(c3).strip()
                    
                    if clock_name:
                        results.append({'name': clock_name, 'kind': 'ff_clock', 'edge': edge})
                            
            except Exception as e:
                self.warn_handler.warn_error(
                    "ClockSignalExtraction",
                    e,
                    context="extract_clock_signals",
                    component="SVParser"
                )
            
            return pyslang.VisitAction.Advance
        
        if self.root:
            self.root.visit(collect)
        return results
    
    def extract_reset_signals(self) -> List[Dict]:
        """提取复位信号"""
        results = []
        
        def collect(node):
            try:
                kn = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
                
                if kn == 'ImplicitAnsiPort':
                    header = getattr(node, 'header', None)
                    if header:
                        direction = getattr(header, 'direction', None)
                        if direction and 'Input' in direction.kind.name:
                            decl = getattr(node, 'declarator', None)
                            if decl:
                                name = str(decl.name).strip()
                                if 'rst' in name.lower() or 'reset' in name.lower():
                                    results.append({'name': name, 'kind': 'reset_input'})
                            
            except Exception as e:
                self.warn_handler.warn_error(
                    "ResetSignalExtraction",
                    e,
                    context="extract_reset_signals",
                    component="SVParser"
                )
            
            return pyslang.VisitAction.Advance
        
        if self.root:
            self.root.visit(collect)
        return results
    
    def get_warning_report(self) -> str:
        """获取警告报告"""
        return self.warn_handler.get_report()
    
    def print_warning_report(self):
        """打印警告报告"""
        if self.verbose:
            report = self.get_warning_report()
            if report:
                print(report)


# =============================================================================
# 辅助函数
# =============================================================================

def _extract_port(port, warn_handler: ParseWarningHandler = None) -> Optional[PortInfo]:
    """从端口节点提取信息"""
    try:
        header = getattr(port, 'header', None)
        decl = getattr(port, 'declarator', None)
        
        if not header:
            return None
        
        direction = getattr(header, 'direction', None)
        dir_str = 'unknown'
        if direction:
            dn = direction.kind.name if hasattr(direction.kind, 'name') else str(direction.kind)
            if 'Input' in dn:
                dir_str = 'input'
            elif 'Output' in dn:
                dir_str = 'output'
            elif 'Inout' in dn:
                dir_str = 'inout'
        
        name = str(decl.name).strip() if decl and hasattr(decl, 'name') else ''
        if not name:
            return None
        
        width = 1
        data_type = "logic"
        
        if decl:
            if hasattr(decl, 'dimensions') and decl.dimensions:
                dim_str = str(decl.dimensions)
                m = re.search(r'\[(\d+):0\]', dim_str)
                if m:
                    width = int(m.group(1)) + 1
        
        return PortInfo(name=name, direction=dir_str, width=width, data_type=data_type)
    
    except Exception as e:
        if warn_handler:
            warn_handler.warn_error("PortExtraction", e, context="_extract_port", component="pyslang_helper")
        return None


def _extract_member(item, warn_handler: ParseWarningHandler = None) -> Optional[MemberInfo]:
    """从类成员节点提取信息"""
    try:
        qualifiers = str(getattr(item, 'qualifiers', '')).strip()
        decl = str(getattr(item, 'declaration', '')).strip().rstrip(';')
        
        match = re.match(r'(\w+)\s*\[(\d+):0\]\s*(\w+)', decl)
        if match:
            return MemberInfo(
                name=match.group(3),
                data_type=match.group(1),
                width=int(match.group(2)) + 1,
                qualifiers=qualifiers
            )
        
        parts = decl.split()
        if len(parts) >= 2:
            return MemberInfo(
                name=parts[-1],
                data_type=parts[0],
                width=1,
                qualifiers=qualifiers
            )
        
        return None
    except Exception as e:
        if warn_handler:
            warn_handler.warn_error("MemberExtraction", e, context="_extract_member", component="pyslang_helper")
        return None


def _extract_method(item, warn_handler: ParseWarningHandler = None) -> Optional[MethodInfo]:
    """从方法节点提取信息"""
    try:
        decl = str(getattr(item, 'declaration', '')).strip()
        kn = item.kind.name if hasattr(item.kind, 'name') else str(item.kind)
        
        match = re.search(r'(function|task)\s+[\w\s\[\]:]*\s*(\w+)\s*\(', decl)
        if match:
            return MethodInfo(
                name=match.group(2),
                kind=match.group(1),
                return_type=""
            )
        return None
    except Exception as e:
        if warn_handler:
            warn_handler.warn_error("MethodExtraction", e, context="_extract_method", component="pyslang_helper")
        return None


def _extract_constraint(item, warn_handler: ParseWarningHandler = None) -> Optional[ConstraintInfo]:
    """从约束节点提取信息"""
    try:
        name = str(getattr(item, 'name', '')).strip() or 'anonymous'
        return ConstraintInfo(name=name, expr=str(item)[:80])
    except Exception as e:
        if warn_handler:
            warn_handler.warn_error("ConstraintExtraction", e, context="_extract_constraint", component="pyslang_helper")
        return None


# =============================================================================
# 便捷函数
# =============================================================================

def parse(code: str, verbose: bool = True) -> SVParser:
    """创建解析器并解析代码"""
    return SVParser(code, verbose=verbose)


def extract_all(code: str, verbose: bool = True) -> Dict:
    """提取所有信息"""
    parser = SVParser(code, verbose=verbose)
    
    return {
        'modules': parser.extract_modules(),
        'classes': parser.extract_classes(),
        'constraints': parser.extract_constraints(),
        'functions': parser.extract_functions(),
        'clocks': parser.extract_clock_signals(),
        'resets': parser.extract_reset_signals(),
    }


if __name__ == '__main__':
    code = '''
    module test;
        input clk, rst_n;
        output [7:0] data;
        always_ff @(posedge clk) begin
            if (!rst_n)
                data <= 0;
        end
    endmodule
    
    class packet;
        rand bit [7:0] data;
        constraint c_data { data > 0; }
    endclass
    '''
    
    result = extract_all(code)
    print("Modules:", len(result['modules']))
    print("Classes:", len(result['classes']))
    print("Clocks:", result['clocks'])
