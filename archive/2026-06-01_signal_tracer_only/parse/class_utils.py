"""
Class Parser - 使用正确的 AST 遍历

class 成员、方法、约束提取

注意：此文件不包含任何正则表达式，所有解析使用直接的 AST 属性访问
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import pyslang
from pyslang import SyntaxKind


@dataclass
class ClassMethod:
    name: str = ""
    kind: str = "function"  # function or task
    return_type: str = ""
    arguments: List[Dict] = field(default_factory=list)
    qualifiers: List[str] = field(default_factory=list)


@dataclass
class ClassMember:
    name: str = ""
    data_type: str = ""
    width: str = ""
    qualifiers: str = ""
    default_value: str = ""


@dataclass
class ClassConstraint:
    name: str = ""
    expression: str = ""


class ClassExtractor:
    """从 SystemVerilog 代码中提取类定义 - 使用正确的 AST 遍历"""
    
    def __init__(self, parser=None, verbose=True):
        self.parser = parser
        self.verbose = verbose
        self.classes: List[Dict] = []
    
    def _extract_from_tree(self, root) -> List[Dict]:
        """使用 AST 遍历提取类"""
        self.classes = []
        
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            # 查找 ClassDeclaration
            if kind_name == 'ClassDeclaration':
                class_info = self._extract_class(node)
                if class_info:
                    self.classes.append(class_info)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
        return self.classes
    
    def _extract_class(self, node) -> Optional[Dict]:
        """提取类 - 使用 AST 属性直接访问"""
        class_info = {
            'name': '',
            'extends': '',
            'members': [],
            'methods': [],
            'constraints': [],
            'properties': []
        }
        
        # 类名 - 直接从 node.name 获取
        if hasattr(node, 'name') and node.name:
            class_info['name'] = str(node.name)
        elif hasattr(node, 'identifier') and node.identifier:
            class_info['name'] = str(node.identifier)
        
        # 父类
        if hasattr(node, 'extending') and node.extending:
            class_info['extends'] = str(node.extending)
        
        # 遍历子节点提取成员
        for child in node:
            if not child:
                continue
            
            try:
                child_kind = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            except:
                continue
            
            # ClassPropertyDeclaration - 类的属性（字段）
            if child_kind == 'ClassPropertyDeclaration':
                prop = self._extract_property(child)
                if prop:
                    class_info['properties'].append(prop)
            
            # ClassMethodDeclaration - 类的方法
            elif child_kind == 'ClassMethodDeclaration':
                method = self._extract_method(child)
                if method:
                    class_info['methods'].append(method)
            
            # ConstraintDeclaration - 约束
            elif child_kind == 'ConstraintDeclaration':
                constraint = self._extract_constraint(child)
                if constraint:
                    class_info['constraints'].append(constraint)
        
        return class_info if class_info['name'] else None
    
    def _extract_property(self, node) -> Optional[Dict]:
        """提取属性 - 使用 AST 属性"""
        prop = {'name': '', 'type': '', 'qualifiers': '', 'width': '', 'default': ''}
        
        # 属性名
        if hasattr(node, 'declarators') and node.declarators:
            for decl in node.declarators:
                if hasattr(decl, 'name') and decl.name:
                    prop['name'] = str(decl.name)
                    break
                elif hasattr(decl, 'identifier') and decl.identifier:
                    prop['name'] = str(decl.identifier)
                    break
        
        # 数据类型
        if hasattr(node, 'dataType') and node.dataType:
            prop['type'] = str(node.dataType)
        elif hasattr(node, 'type') and node.type:
            prop['type'] = str(node.type)
        
        #修饰符 (rand/randc/local/protected)
        if hasattr(node, 'keyword') and node.keyword:
            kw = str(node.keyword).lower()
            if 'rand' in kw:
                prop['qualifiers'] = 'rand'
            elif 'randc' in kw:
                prop['qualifiers'] = 'randc'
        
        # 默认值
        if hasattr(node, 'value') and node.value:
            prop['default'] = str(node.value)
        
        return prop if prop['name'] else None
    
    def _extract_method(self, node) -> Optional[Dict]:
        """提取方法 - 使用 AST 属性"""
        method = {'name': '', 'kind': 'function', 'return_type': '', 'arguments': []}
        
        # 方法名
        if hasattr(node, 'name') and node.name:
            method['name'] = str(node.name)
        
        # 函数/任务 判断
        if hasattr(node, 'keyword') and node.keyword:
            kw = str(node.keyword).lower()
            if 'task' in kw:
                method['kind'] = 'task'
            elif 'function' in kw:
                method['kind'] = 'function'
        
        # 返回类型
        if hasattr(node, 'returnType') and node.returnType:
            method['return_type'] = str(node.returnType)
        
        # 参数列表
        if hasattr(node, 'portList') and node.portList:
            for port in node.portList:
                if not port:
                    continue
                arg = {}
                if hasattr(port, 'name') and port.name:
                    arg['name'] = str(port.name)
                if hasattr(port, 'dataType') and port.dataType:
                    arg['type'] = str(port.dataType)
                if arg:
                    method['arguments'].append(arg)
        
        return method if method['name'] else None
    
    def _extract_constraint(self, node) -> Optional[Dict]:
        """提取约束 - 使用 AST 属性"""
        constraint = {'name': '', 'expression': ''}
        
        if hasattr(node, 'name') and node.name:
            constraint['name'] = str(node.name)
        
        if hasattr(node, 'expression') and node.expression:
            constraint['expression'] = str(node.expression)
        elif hasattr(node, 'condition') and node.condition:
            constraint['expression'] = str(node.condition)
        
        return constraint if constraint['name'] or constraint['expression'] else None
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        """从文本提取"""
        tree = pyslang.SyntaxTree.fromText(code, source)
        return self._extract_from_tree(tree.root)
    
    def get_classes(self) -> List[Dict]:
        return self.classes


# ============================================================================
# 便捷函数
# ============================================================================

def get_classes(code, verbose=True):
    """提取类定义"""
    extractor = ClassExtractor(verbose=verbose)
    return extractor.extract_from_text(code)


def extract_classes_from_text(code):
    """提取类定义 - 兼容接口"""
    return get_classes(code)


if __name__ == "__main__":
    test_code = '''
class packet;
    rand int data;
    randc bit [7:0] cmd;
    local int local_var = 5;
    
    function int get_data();
        return data;
    endfunction
    
    task send(input bit [7:0] d);
        cmd <= d;
    endtask
    
    constraint c1 { data < 256; }
endclass
'''
    
    print("=== Class Extraction ===\n")
    
    result = get_classes(test_code)
    
    print(f"Classes found: {len(result)}")
    
    for cls in result:
        print(f"\nClass: {cls['name']}")
        if cls['extends']:
            print(f"  Extends: {cls['extends']}")
        
        print(f"  Properties ({len(cls['properties'])}):")
        for p in cls['properties']:
            qual = f", {p['qualifiers']}" if p['qualifiers'] else ""
            print(f"    - {p['name']}: {p['type']}{qual}")
        
        print(f"  Methods ({len(cls['methods'])}):")
        for m in cls['methods']:
            ret = f"{m['return_type']} " if m['return_type'] else ""
            print(f"    - {m['kind']} {ret}{m['name']}({len(m['arguments'])} args)")
        
        print(f"  Constraints ({len(cls['constraints'])}):")
        for c in cls['constraints']:
            print(f"    - {c['name']}: {c['expression'][:30]}...")
