"""
Assertion 解析器 - assertion/sequence/property 提取
"""
import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class AssertionBlock:
    name: str = ""
    kind: str = ""
    property_expr: str = ""


@dataclass
class SequenceDef:
    name: str = ""
    args: List[str] = None
    body: str = ""
    
    def __init__(self):
        self.args = []


@dataclass
class PropertyDef:
    name: str = ""
    args: List[str] = None
    body: str = ""
    
    def __init__(self):
        self.args = []


class AssertionExtractor:
    def __init__(self, parser):
        self.parser = parser
        self.assertions: List[AssertionBlock] = []
        self.sequences: Dict[str, SequenceDef] = {}
        self.properties: Dict[str, PropertyDef] = {}
        self._extract_all()
    
    def _extract_all(self):
        for key, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root') or not tree.root:
                continue
            
            root = tree.root
            
            if hasattr(root, 'members') and root.members:
                for m in root.members:
                    self._process_member(m)
    
    def _process_member(self, member):
        type_name = str(type(member))
        node_str = str(member)
        
        # Concurrent assertion
        if 'ConcurrentAssertion' in type_name or 'Assert' in type_name:
            block = self._parse_assertion(node_str, member)
            if block:
                self.assertions.append(block)
        
        # Sequence
        elif 'SequenceDeclaration' in type_name:
            seq = self._parse_sequence(node_str)
            if seq:
                self.sequences[seq.name] = seq
        
        # Property
        elif 'PropertyDeclaration' in type_name:
            prop = self._parse_property(node_str)
            if prop:
                self.properties[prop.name] = prop
        
        # 递归
        for attr in ['members', 'body', 'items']:
            if hasattr(member, attr):
                child = getattr(member, attr)
                if child:
                    if isinstance(child, list):
                        for c in child:
                            self._process_member(c)
                    else:
                        self._process_member(child)
    
    def _parse_assertion(self, node_str: str, node) -> Optional[AssertionBlock]:
        block = AssertionBlock()
        
        kind_match = re.search(r'\b(assert|assume|cover)\b', node_str)
        if kind_match:
            block.kind = kind_match.group(1)
        
        name_match = re.search(rf'{block.kind}\s+(\w+)\s*\(', node_str)
        if name_match:
            block.name = name_match.group(1)
        else:
            block.name = f"anon_{len(self.assertions)}"
        
        block.property_expr = node_str
        return block
    
    def _parse_sequence(self, node_str: str) -> Optional[SequenceDef]:
        seq = SequenceDef()
        match = re.search(r'sequence\s+(\w+)', node_str)
        if match:
            seq.name = match.group(1)
        return seq if seq.name else None
    
    def _parse_property(self, node_str: str) -> Optional[PropertyDef]:
        prop = PropertyDef()
        match = re.search(r'property\s+(\w+)', node_str)
        if match:
            prop.name = match.group(1)
        return prop if prop.name else None
    
    def get_all_assertions(self) -> List[AssertionBlock]:
        return self.assertions
    
    def get_all_sequences(self) -> Dict[str, SequenceDef]:
        return self.sequences
    
    def get_all_properties(self) -> Dict[str, PropertyDef]:
        return self.properties


def extract_assertions_from_text(code: str) -> List[dict]:
    """从源码文本提取 assertions/sequences/properties (使用 pyslang)"""
    import pyslang
    from pyslang import SyntaxKind
    
    results = []
    
    # 主要的 assertion 相关声明类型
    target_kinds = {
        'SequenceDeclaration',
        'PropertyDeclaration',
        'AssertPropertyStatement',
        'AssumePropertyStatement', 
        'CoverPropertyStatement',
    }
    
    def collect(node):
        kind_name = node.kind.name
        
        if kind_name in target_kinds:
            name = str(getattr(node, 'name', '')).strip()
            expr = str(node)[:100].replace('\n', ' ').strip()
            
            results.append({
                'name': name,
                'kind': kind_name,
                'expr': expr
            })
        
        return pyslang.VisitAction.Advancee
    
    try:
        tree = pyslang.SyntaxTree.fromText(code)
        tree.root.visit(collect)
    except Exception as e:
        pass
    
    return results
