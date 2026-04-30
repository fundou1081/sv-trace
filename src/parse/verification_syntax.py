"""
验证语法解析器 - 使用 pyslang AST (P0-P1)

核心验证语法提取:
- sequence / property
- assert property / expect property / cover property
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
class AssertProperty:
    kind: str = ""  # assert / expect / cover
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
        self.assertions = []
        self.virtual_methods = []
        self.wait_orders = []
        
        if parser:
            self._extract_all()
    
    def _extract_all(self):
        for key, tree in getattr(self.parser, 'trees', {}).items():
            if tree and hasattr(tree, 'root') and tree.root:
                self._extract_from_tree(tree.root)
    
    def _extract_from_tree(self, root):
        def collect(node):
            self._process_node(node)
            return pyslang.VisitAction.Advancee
        
        root.visit(collect)
    
    def _process_node(self, node):
        kn = node.kind.name
        
        # SequenceDeclaration
        if kn == 'SequenceDeclaration':
            seq = SequenceDef()
            if hasattr(node, 'name') and node.name:
                seq.name = str(node.name).strip()
            if hasattr(node, 'items'):
                parts = [str(i).strip() for i in node.items if i and str(i).strip() != ';']
                seq.expr = '; '.join(parts)
            if seq.name:
                self.sequences.append(seq)
        
        # PropertyDeclaration - 属性定义
        elif kn == 'PropertyDeclaration':
            # 检查是否在断言语句中
            if hasattr(node, 'parent') and node.parent:
                parent_str = str(node.parent)
                if 'assert' in parent_str or 'expect' in parent_str or 'cover' in parent_str:
                    return  # Skip assertions
            
            # 这是属性定义
            prop = PropertyDef()
            if hasattr(node, 'name') and node.name:
                prop.name = str(node.name).strip()
            if hasattr(node, 'propertySpec') and node.propertySpec:
                prop.expr = str(node.propertySpec).strip()
            if prop.name:
                self.properties.append(prop)
        
        # AssertPropertyStatement ✅
        elif kn == 'AssertPropertyStatement':
            stmt = str(node).strip()
            
            assertion_kind = 'assert'
            if stmt.startswith('expect'):
                assertion_kind = 'expect'
            elif stmt.startswith('cover'):
                assertion_kind = 'cover'
            
            prop_expr = ''
            if hasattr(node, 'propertySpec') and node.propertySpec:
                prop_expr = str(node.propertySpec).strip()
            elif hasattr(node, 'expression') and node.expression:
                prop_expr = str(node.expression).strip()
            
            if prop_expr:
                self.assertions.append(AssertProperty(kind=assertion_kind, expr=prop_expr))
        
        # CoverPropertyStatement ✅
        elif kn == 'CoverPropertyStatement':
            stmt = str(node).strip()
            prop_expr = ''
            
            if hasattr(node, 'propertySpec') and node.propertySpec:
                prop_expr = str(node.propertySpec).strip()
            
            if prop_expr:
                self.assertions.append(AssertProperty(kind='cover', expr=prop_expr))
        
        # HierarchyInstantiation - wait order ✅
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
            'assertions': self.assertions,
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
    
    // 断言语句
    expect property (req |-> resp);
    assert property (a |-> b) else $display("fail");
    cover property (c |-> d);
    
    wait order (a, b, c);
    
    class test;
        virtual function bit [7:0] get();
        pure virtual task reset();
    endclass
endmodule'''
    
    result = extract_verification_syntax(test_code)
    
    print("=== 验证语法 (P0-P1) ===")
    print(f"\n✅ Sequences: {len(result['sequences'])} - {[s.name for s in result['sequences']]}")
    print(f"✅ Properties: {len(result['properties'])} - {[p.name for p in result['properties']]}")
    
    print(f"\n✅ Assertions ({len(result['assertions'])}):")
    for a in result['assertions']:
        print(f"   {a.kind}: {a.expr}")
    
    print(f"\n✅ Wait Orders: {len(result['wait_orders'])}")
    for w in result['wait_orders']:
        print(f"   {w.names}")
    
    print(f"\n✅ Virtual Methods: {len(result['virtual_methods'])}")
    for m in result['virtual_methods']:
        print(f"   {m.qualifiers} {m.kind} {m.name}")
