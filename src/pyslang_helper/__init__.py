"""
pyslang Helper - SystemVerilog AST 解析辅助工具
基于 pyslang 提供常用的解析功能
"""

import pyslang
from pyslang import SyntaxKind
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field


# =============================================================================
# 数据类定义
# =============================================================================

@dataclass
class PortInfo:
    """端口信息"""
    name: str
    direction: str  # input, output, inout
    width: int = 1
    data_type: str = "logic"
    
    def __str__(self):
        return f"{self.direction} [{self.width-1}:0] {self.name}"


@dataclass
class MemberInfo:
    """类成员信息"""
    name: str
    data_type: str
    width: int = 1
    qualifiers: str = ""  # rand, randc


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
    kind: str = "function"  # function, task
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
    """
    
    def __init__(self, code: str = ""):
        self.code = code
        self.tree = None
        self.root = None
        
        if code:
            self.parse(code)
    
    def parse(self, code: str) -> 'SVParser':
        """解析代码"""
        self.code = code
        self.tree = pyslang.SyntaxTree.fromText(code)
        self.root = self.tree.root
        return self
    
    def find_nodes(self, kind_filter: Callable[[str], bool]) -> List:
        """查找所有匹配 kind_filter 的节点"""
        results = []
        
        def collect(node):
            if kind_filter(node.kind.name):
                results.append(node)
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
            if node.kind == SyntaxKind.ModuleDeclaration:
                mod = ModuleInfo(name=str(node.header.name).strip())
                
                # 提取端口
                port_list = getattr(node.header, 'ports', None)
                if port_list and hasattr(port_list, 'ports'):
                    port_list = port_list.ports
                
                if port_list:
                    for port in port_list:
                        if port is None:
                            continue
                        if not hasattr(port, 'declarator'):
                            continue
                        port_info = _extract_port(port)
                        if port_info:
                            mod.ports.append(port_info)
                
                results.append(mod)
            
            return pyslang.VisitAction.Advance
        
        if self.root:
            self.root.visit(collect)
        return results
    
    def extract_classes(self) -> List[ClassInfo]:
        """提取所有类"""
        results = []
        
        def collect(node):
            if node.kind == SyntaxKind.ClassDeclaration:
                cls = ClassInfo(name=str(node.name).strip())
                
                # 提取成员、方法、约束
                for item in getattr(node, 'items', []):
                    kn = item.kind.name
                    
                    if 'Property' in kn or 'Rand' in kn:
                        mem = _extract_member(item)
                        if mem:
                            cls.members.append(mem)
                    
                    elif 'Method' in kn and 'Declaration' in kn:
                        met = _extract_method(item)
                        if met:
                            cls.methods.append(met)
                    
                    elif 'Constraint' in kn:
                        con = _extract_constraint(item)
                        if con:
                            cls.constraints.append(con)
                
                results.append(cls)
            
            return pyslang.VisitAction.Advance
        
        if self.root:
            self.root.visit(collect)
        return results
    
    def extract_constraints(self) -> List[ConstraintInfo]:
        """提取所有约束"""
        results = []
        
        def collect(node):
            if node.kind == SyntaxKind.ConstraintDeclaration:
                con = ConstraintInfo(
                    name=str(node.name).strip() if hasattr(node, 'name') else 'unknown',
                    expr=str(node)[:80].replace('\n', ' ').strip()
                )
                results.append(con)
            
            return pyslang.VisitAction.Advance
        
        if self.root:
            self.root.visit(collect)
        return results
    
    def extract_functions(self) -> List[FunctionInfo]:
        """提取所有函数/任务"""
        results = []
        
        def collect(node):
            kn = node.kind.name
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
            
            return pyslang.VisitAction.Advance
        
        if self.root:
            self.root.visit(collect)
        return results
    
    def extract_clock_signals(self) -> List[Dict]:
        """提取时钟信号"""
        results = []
        
        def collect(node):
            kn = node.kind.name
            
            # 时钟输入端口
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
            
            # always_ff 时钟
            elif kn == 'EventControlWithExpression':
                edge = 'posedge'
                clock_name = ''
                
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
            
            return pyslang.VisitAction.Advance
        
        if self.root:
            self.root.visit(collect)
        return results
    
    def extract_reset_signals(self) -> List[Dict]:
        """提取复位信号"""
        results = []
        
        def collect(node):
            kn = node.kind.name
            
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
            
            return pyslang.VisitAction.Advance
        
        if self.root:
            self.root.visit(collect)
        return results


# =============================================================================
# 辅助函数
# =============================================================================

def _extract_port(port) -> Optional[PortInfo]:
    """从端口节点提取信息"""
    try:
        header = getattr(port, 'header', None)
        decl = getattr(port, 'declarator', None)
        
        if not header:
            return None
        
        # 方向
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
        
        # 名字
        name = str(decl.name).strip() if decl and hasattr(decl, 'name') else ''
        
        # 宽度 - 优先从 declarator 获取，否则从 header.dataType 获取
        width = 1
        data_type = "logic"
        
        # 先尝试从 declarator 获取
        if decl:
            if hasattr(decl, 'dimensions') and decl.dimensions:
                dim_str = str(decl.dimensions)
                import re
                m = re.search(r'\[(\d+):0\]', dim_str)
                if m:
                    width = int(m.group(1)) + 1
        
        # 如果 declarator 没有宽度，从 header.dataType 获取
        if width == 1:
            data_type_obj = getattr(header, 'dataType', None)
            if data_type_obj:
                dt_str = str(data_type_obj)
                import re
                m = re.search(r'\[(\d+):0\]', dt_str)
                if m:
                    width = int(m.group(1)) + 1
                # 提取类型名
                type_match = re.match(r'(\w+)', dt_str)
                if type_match:
                    data_type = type_match.group(1)
        
        return PortInfo(name=name, direction=dir_str, width=width, data_type=data_type)
    
    except Exception:
        return None


def _extract_member(item) -> Optional[MemberInfo]:
    """从类成员节点提取信息"""
    try:
        qualifiers = str(getattr(item, 'qualifiers', '')).strip()
        decl = str(getattr(item, 'declaration', '')).strip().rstrip(';')
        
        # 解析 "bit [7:0] data" 格式
        import re
        match = re.match(r'(\w+)\s*\[(\d+):0\]\s*(\w+)', decl)
        if match:
            data_type = match.group(1)
            width = int(match.group(2)) + 1
            name = match.group(3)
        else:
            parts = decl.split()
            data_type = parts[0] if parts else 'logic'
            name = parts[1] if len(parts) > 1 else ''
            width = 1
        
        return MemberInfo(name=name, data_type=data_type, width=width, qualifiers=qualifiers)
    
    except Exception:
        return None


def _extract_method(item) -> Optional[MethodInfo]:
    """从方法节点提取信息"""
    try:
        decl = str(getattr(item, 'declaration', '')).strip()
        kn = item.kind.name
        
        import re
        match = re.search(r'(function|task)\s+[\w\s\[\]:]*\s*(\w+)\s*\(', decl)
        if match:
            kind = match.group(1)
            name = match.group(2)
            return MethodInfo(name=name, kind=kind)
        
        return None
    
    except Exception:
        return None


def _extract_constraint(item) -> Optional[ConstraintInfo]:
    """从约束节点提取信息"""
    try:
        name = str(getattr(item, 'name', '')).strip()
        return ConstraintInfo(name=name, expr=str(item)[:80])
    except Exception:
        return None


# =============================================================================
# 便捷函数
# =============================================================================

def parse(code: str) -> SVParser:
    """创建解析器并解析代码"""
    return SVParser(code)


def extract_all(code: str) -> Dict:
    """提取所有信息"""
    parser = SVParser(code)
    
    return {
        'modules': parser.extract_modules(),
        'classes': parser.extract_classes(),
        'constraints': parser.extract_constraints(),
        'functions': parser.extract_functions(),
        'clocks': parser.extract_clock_signals(),
        'resets': parser.extract_reset_signals(),
    }


# =============================================================================
# 示例
# =============================================================================

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
    
    print("=== Modules ===")
    for m in result['modules']:
        print(f"  {m.name}: {len(m.ports)} ports")
    
    print("\n=== Classes ===")
    for c in result['classes']:
        print(f"  {c.name}: {len(c.members)} members, {len(c.constraints)} constraints")
    
    print("\n=== Clocks ===")
    for c in result['clocks']:
        print(f"  {c}")
