"""
Class Members Parser - 使用 pyslang AST

支持:
- ClassPropertyDeclaration (类属性)
- ClassMethodDeclaration (类方法/任务)
- ClassMethodPrototype (方法原型)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import pyslang
from pyslang import SyntaxKind


@dataclass
class ClassProperty:
    """类属性信息"""
    name: str = ""
    data_type: str = ""
    direction: str = ""  # local, protected, public
    rand_mode: str = ""  # rand, randc
    qualifiers: List[str] = field(default_factory=list)
    width: str = ""
    default_value: str = ""


@dataclass
class ClassMethod:
    """类方法信息"""
    name: str = ""
    kind: str = ""  # function, task
    return_type: str = ""
    arguments: List[Dict] = field(default_factory=list)
    qualifiers: List[str] = field(default_factory=list)
    is_virtual: bool = False
    is_extern: bool = False


@dataclass
class ClassMember:
    """类成员 (属性或方法)"""
    name: str = ""
    member_type: str = ""  # property, method
    data: any = None


class ClassMembersExtractor:
    """从 SystemVerilog 代码中提取类成员"""
    
    def __init__(self):
        self.properties: List[ClassProperty] = []
        self.methods: List[ClassMethod] = []
    
    def _extract_from_tree(self, root) -> List[ClassMember]:
        members = []
        
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ClassPropertyDeclaration':
                member = self._extract_property(node)
                if member:
                    members.append(member)
                    self.properties.append(member)
            
            elif kind_name == 'ClassMethodDeclaration':
                member = self._extract_method(node)
                if member:
                    members.append(member)
                    self.methods.append(member)
            
            elif kind_name == 'MethodPrototype':
                member = self._extract_method(node, is_prototype=True)
                if member:
                    members.append(member)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
        return members
    
    def _extract_property(self, node) -> Optional[ClassMember]:
        """提取类属性"""
        prop = ClassProperty()
        prop.member_type = 'property'
        
        # 属性名
        if hasattr(node, 'declarators') and node.declarators:
            for decl in node.declarators:
                if hasattr(decl, 'name') and decl.name:
                    prop.name = str(decl.name)
                    break
                elif hasattr(decl, 'value') and decl.value:
                    prop.name = str(decl.value)
                    break
        
        # 检查 rand/randc 修饰符
        if hasattr(node, 'keyword') and node.keyword:
            kw = str(node.keyword).lower()
            if 'randc' in kw:
                prop.rand_mode = 'randc'
            elif 'rand' in kw:
                prop.rand_mode = 'rand'
        
        # 访问修饰符
        if hasattr(node, 'keyword'):
            kw = str(node.keyword).lower()
            if 'local' in kw:
                prop.direction = 'local'
            elif 'protected' in kw:
                prop.direction = 'protected'
        
        # 数据类型
        if hasattr(node, 'dataType') and node.dataType:
            prop.data_type = str(node.dataType)
        
        # 默认值
        if hasattr(node, 'value') and node.value:
            prop.default_value = str(node.value)
        
        # 宽度
        if hasattr(node, 'dimensions') and node.dimensions:
            prop.width = str(node.dimensions)
        
        return ClassMember(name=prop.name, member_type='property', data=prop)
    
    def _extract_method(self, node, is_prototype=False) -> Optional[ClassMember]:
        """提取类方法"""
        method = ClassMethod()
        method.member_type = 'method'
        
        # 方法名
        if hasattr(node, 'name') and node.name:
            method.name = str(node.name)
        
        # 确定是 function 还是 task
        if hasattr(node, 'keyword'):
            kw = str(node.keyword).lower()
            if 'task' in kw:
                method.kind = 'task'
            elif 'function' in kw:
                method.kind = 'function'
        
        # 返回类型 (function)
        if hasattr(node, 'returnType') and node.returnType:
            method.return_type = str(node.returnType)
        
        # 虚拟/外部修饰符
        if hasattr(node, 'qualifier'):
            q = str(node.qualifier).lower()
            method.is_virtual = 'virtual' in q
            method.is_extern = 'extern' in q
        
        # 收集参数
        if hasattr(node, 'portList') and node.portList:
            for port in node.portList:
                arg = {}
                if hasattr(port, 'name') and port.name:
                    arg['name'] = str(port.name)
                if hasattr(port, 'dataType') and port.dataType:
                    arg['type'] = str(port.dataType)
                if arg:
                    method.arguments.append(arg)
        
        return ClassMember(name=method.name, member_type='method', data=method)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[ClassMember]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        return self._extract_from_tree(tree.root)
    
    def get_members(self) -> List[ClassMember]:
        return self.properties + self.methods
    
    def get_properties(self) -> List[ClassProperty]:
        return self.properties
    
    def get_methods(self) -> List[ClassMethod]:
        return self.methods


# ============================================================================
# 便捷函数
# ============================================================================

def extract_class_properties(code: str) -> List[Dict]:
    """从代码提取类属性"""
    extractor = ClassMembersExtractor()
    members = extractor.extract_from_text(code)
    properties = [m for m in members if m.member_type == 'property']
    
    return [
        {
            'name': p.name,
            'data_type': p.data_type,
            'direction': p.direction,
            'rand_mode': p.rand_mode,
            'width': p.width,
            'default_value': p.default_value
        }
        for p in [m.data for m in properties]
    ]


def extract_class_methods(code: str) -> List[Dict]:
    """从代码提取类方法"""
    extractor = ClassMembersExtractor()
    members = extractor.extract_from_text(code)
    methods = [m for m in members if m.member_type == 'method']
    
    return [
        {
            'name': m.name,
            'kind': m.kind,
            'return_type': m.return_type,
            'arguments': m.arguments,
            'qualifiers': m.qualifiers,
            'is_virtual': m.is_virtual,
            'is_extern': m.is_extern
        }
        for m in [m.data for m in methods]
    ]


def extract_class_members(code: str) -> Dict[str, List]:
    """一次性提取类属性和方法"""
    extractor = ClassMembersExtractor()
    members = extractor.extract_from_text(code)
    
    properties = [m.data for m in members if m.member_type == 'property']
    methods = [m.data for m in members if m.member_type == 'method']
    
    return {
        'properties': [
            {
                'name': p.name,
                'data_type': p.data_type,
                'direction': p.direction,
                'rand_mode': p.rand_mode,
                'width': p.width
            }
            for p in properties
        ],
        'methods': [
            {
                'name': m.name,
                'kind': m.kind,
                'return_type': m.return_type,
                'arguments': m.arguments,
                'is_virtual': m.is_virtual
            }
            for m in methods
        ],
        'property_count': len(properties),
        'method_count': len(methods)
    }


if __name__ == "__main__":
    test_code = '''
class packet extends base;
    rand int data;
    randc bit [7:0] cmd;
    local int local_var;
    protected bit [15:0] prot_var;
    
    // Function
    function int get_data();
        return data;
    endfunction
    
    // Task
    task send_packet(input [31:0] d);
        $display("Sending: %h", d);
    endtask
    
    // Virtual function
    virtual function void reset();
        data = 0;
    endfunction
    
    // Extern method
    extern function int calc();
endclass
'''
    
    print("=== Class Members Extraction ===\n")
    
    result = extract_class_members(test_code)
    
    print(f"Properties ({result['property_count']}):")
    for p in result['properties']:
        rand_str = f", randMode={p['rand_mode']}" if p['rand_mode'] else ""
        dir_str = f", direction={p['direction']}" if p['direction'] else ""
        print(f"  {p['name']}: {p['data_type']}{rand_str}{dir_str}")
    
    print(f"\nMethods ({result['method_count']}):")
    for m in result['methods']:
        virt_str = "virtual " if m['is_virtual'] else ""
        ret_str = f"{m['return_type']} " if m['return_type'] else ""
        print(f"  {virt_str}{m['kind']} {ret_str}{m['name']}({len(m['arguments'])} args)")
