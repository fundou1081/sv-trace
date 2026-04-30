"""
验证语法解析器 - 使用 pyslang AST (P0-P1)

核心验证语法提取:
- sequence / property
- expect property (作为 PropertyDeclaration 顶层语句)
- wait_order  
- virtual function/task
"""
import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List
import pyslang
from pyslang import SyntaxKind


@dataclass
class SequenceDef:
    name: str = ""
    expr: str = ""


@dataclass  
class PropertyDef:
    name: str = ""
    expr: str = ""


@dataclass
class ExpectProperty:
    expr: str = ""


@dataclass
class VirtualMethod:
    kind: str = ""
    qualifiers: List[str] = field(default_factory=list)
    return_type: str = ""
    name: str = ""


@dataclass
class WaitOrderBlock:
    names: List[str] = field(default_factory=list)


class VerificationSyntaxExtractor:
    def __init__(self, parser=None):
        self.parser = parser
        self.sequences = []
        self.properties = []
        self.expects = []
        self.virtual_methods = []
        self.wait_orders = []
        
        # 用于跟踪上下文
        self._in_class = False
        
        if parser:
            self._extract_all()
    
    def _extract_all(self):
        for key, tree in getattr(self.parser, 'trees', {}).items():
            if tree and hasattr(tree, 'root') and tree.root:
                self._extract_from_tree(tree.root)
    
    def _extract_from_tree(self, root):
        def collect(node):
            self._process_node(node)
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _process_node(self, node):
        kn = node.kind.name
        
        # SequenceDeclaration ✅
        if kn == 'SequenceDeclaration':
            seq = SequenceDef()
            if hasattr(node, 'name') and node.name:
                seq.name = str(node.name).strip()
            if hasattr(node, 'items'):
                parts = [str(i).strip() for i in node.items if i and str(i).strip() != ';']
                seq.expr = '; '.join(parts)
            if seq.name:
                self.sequences.append(seq)
        
        # PropertyDeclaration - 区分定义 vs expect 语句
        elif kn == 'PropertyDeclaration':
            # 检查是否在 class 里面 (class 内的 Property)
            # 如果是顶层module 的就是定义，如果parent是class的就是定义
            
            # 检查是否在 class 上下文中
            is_inside_class = hasattr(node, 'parent') and node.parent and 'Class' in str(node.parent)
            
            # 直接包含 expect 的就是 expect 语句
            node_str = str(node).strip()
            is_expect_statement = 'expect' in node_str.lower() or node_str.startswith('expect')
            
            if is_expect_statement:
                # 这是	expect property 语句
                exp = ExpectProperty()
                exp.expr = node_str
                self.expects.append(exp)
            elif not is_inside_class:
                # 这是属性定义 (不是 expect 语句)
                prop = PropertyDef()
                if hasattr(node, 'name') and node.name:
                    prop.name = str(node.name).strip()
                if hasattr(node, 'propertySpec') and node.propertySpec:
                    prop.expr = str(node.propertySpec).strip()
                if prop.name:
                    self.properties.append(prop)
        
        # HierarchyInstantiation - check for wait order ✅
        elif kn == 'HierarchyInstantiation':
            call_str = str(node)
            if 'order' in call_str.lower() and '(' in call_str:
                match = re.search(r'order\s*\(([^)]+)\)', call_str)
                if match:
                    wo = WaitOrderBlock()
                    for n in match.group(1).split(','):
                        wo.names.append(n.strip())
                    if wo.names:
                        self.wait_orders.append(wo)
        
        # ClassMethodDeclaration - virtual method ✅
        elif kn == 'ClassMethodDeclaration':
            self._extract_vm(node)
    
    def _extract_vm(self, node):
        method = VirtualMethod()
        method_str = str(node)
        
        method.kind = 'task' if 'task' in method_str[:20] else 'function'
        
        if 'virtual' in method_str.lower():
            method.qualifiers.append('virtual')
        if 'pure' in method_str.lower():
            method.qualifiers.append('pure')
        
        if hasattr(node, 'prototype') and node.prototype:
            for c in node.prototype:
                if hasattr(c, 'name') and c.name:
                    method.name = str(c.name).strip()
        
        if not method.name:
            match = re.search(r'(function|task)\s+(?:virtual\s+)?(?:(\w+)\s+)?(\w+)', method_str)
            if match:
                method.return_type = match.group(2) or ''
                method.name = match.group(3) or ''
        
        if method.name or method.qualifiers:
            self.virtual_methods.append(method)
    
    def get_results(self):
        return {
            'sequences': self.sequences,
            'properties': self.properties,
            'expects': self.expects,
            'virtual_methods': self.virtual_methods,
            'wait_orders': self.wait_orders,
        }


def extract_verification_syntax(code):
    tree = pyslang.SyntaxTree.fromText(code)
    extractor = VerificationSyntaxExtractor(None)
    extractor._extract_from_tree(tree.root)
    return extractor.get_results()


if __name__ == "__main__":
    test_code = '''module m;
    sequence s; data ##1 v; endsequence
    property p; req |-> resp; endproperty
    expect property (req |-> resp);
    wait order (a, b, c);
    
    class test;
        virtual function bit [7:0] get();
        pure virtual task reset();
    endclass
endmodule'''
    
    result = extract_verification_syntax(test_code)
    
    print("=== 验证语法 (P0-P1) ===")
    print(f"✅ Sequences: {len(result['sequences'])} - {[s.name for s in result['sequences']]}")
    print(f"✅ Properties: {len(result['properties'])} - {[p.name for p in result['properties']]}")
    print(f"✅ ExpectProperty: {len(result['expects'])}")
    for e in result['expects']:
        print(f"   {e.expr[:30]}")
    print(f"✅ Wait Orders: {len(result['wait_orders'])}")
    if result['wait_orders']:
        print(f"   {result['wait_orders'][0].names}")
    print(f"✅ Virtual Methods: {len(result['virtual_methods'])}")
    for m in result['virtual_methods']:
        print(f"   {m.qualifiers} {m.kind} {m.name}")
