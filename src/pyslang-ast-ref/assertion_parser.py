"""
Assertion 和 Sequence Parser - 使用 pyslang AST

支持:
- SequenceDeclaration (序列声明)
- PropertyDeclaration (属性声明)
- SimpleSequenceExpr (简单序列表达式)
- SimplePropertyExpr (简单属性表达式)
- ConcurrentAssertionStatement (并发断言)
- ImmediateAssertStatement (立即断言)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import pyslang
from pyslang import SyntaxKind


@dataclass
class SequenceInfo:
    """序列信息"""
    name: str = ""
    arguments: List[Dict] = field(default_factory=list)
    clocking: str = ""
    expressions: List[str] = field(default_factory=list)


@dataclass
class PropertyInfo:
    """属性信息"""
    name: str = ""
    sequence_name: str = ""  # 关联的序列
    property_type: str = ""  # always, eventually, await
    clocking: str = ""
    action: str = ""  # pass/fail action


@dataclass
class AssertionInfo:
    """断言信息"""
    name: str = ""
    assertion_type: str = ""  # assert, assume, cover
    sequence: str = ""
    action_block: str = ""
    clocking: str = ""


class AssertionExtractor:
    """从 SystemVerilog 代码中提取断言相关"""
    
    def __init__(self):
        self.sequences: List[SequenceInfo] = []
        self.properties: List[PropertyInfo] = []
        self.assertions: List[AssertionInfo] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            # SequenceDeclaration
            if kind_name == 'SequenceDeclaration':
                seq = self._extract_sequence(node)
                if seq:
                    self.sequences.append(seq)
            
            # PropertyDeclaration
            elif kind_name == 'PropertyDeclaration':
                prop = self._extract_property(node)
                if prop:
                    self.properties.append(prop)
            
            # Assertion statements
            elif kind_name in ['ConcurrentAssertionStatement', 'ImmediateAssertStatement', 
                             'AssertPropertyStatement', 'AssumePropertyStatement', 'CoverPropertyStatement']:
                assertion = self._extract_assertion(node)
                if assertion:
                    self.assertions.append(assertion)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
        return self.sequences + self.properties + self.assertions
    
    def _extract_sequence(self, node) -> Optional[SequenceInfo]:
        """提取序列"""
        seq = SequenceInfo()
        
        # 序列名
        if hasattr(node, 'name') and node.name:
            seq.name = str(node.name)
        
        # 参数
        if hasattr(node, 'argumentList') and node.argumentList:
            for arg in node.argumentList:
                if hasattr(arg, 'name') and arg.name:
                    seq.arguments.append({'name': str(arg.name)})
        
        return seq
    
    def _extract_property(self, node) -> Optional[PropertyInfo]:
        """提取属性"""
        prop = PropertyInfo()
        
        # 属性名
        if hasattr(node, 'name') and node.name:
            prop.name = str(node.name)
        
        # 属性类型
        if hasattr(node, 'keyword'):
            kw = str(node.keyword).lower()
            if 'always' in kw:
                prop.property_type = 'always'
            elif 'eventually' in kw:
                prop.property_type = 'eventually'
            elif 'await' in kw:
                prop.property_type = 'await'
        
        return prop
    
    def _extract_assertion(self, node) -> Optional[AssertionInfo]:
        """提取断言"""
        assertion = AssertionInfo()
        
        # 断言类型
        kind_name = node.kind.name if hasattr(node.kind, 'name') else ''
        
        if 'Assert' in kind_name:
            assertion.assertion_type = 'assert'
        elif 'Assume' in kind_name:
            assertion.assertion_type = 'assume'
        elif 'Cover' in kind_name:
            assertion.assertion_type = 'cover'
        
        return assertion
    
    def extract_from_text(self, code: str, source: str = "<text>"):
        tree = pyslang.SyntaxTree.fromText(code, source)
        return self._extract_from_tree(tree.root)
    
    def get_sequences(self) -> List[SequenceInfo]:
        return self.sequences
    
    def get_properties(self) -> List[PropertyInfo]:
        return self.properties
    
    def get_assertions(self) -> List[AssertionInfo]:
        return self.assertions


# ============================================================================
# 便捷函数
# ============================================================================

def extract_sequences(code: str) -> List[Dict]:
    """从代码提取序列"""
    extractor = AssertionExtractor()
    extractor.extract_from_text(code)
    
    return [
        {'name': s.name, 'arguments': len(s.arguments)}
        for s in extractor.sequences
    ]


def extract_properties(code: str) -> List[Dict]:
    """从代码提取属性"""
    extractor = AssertionExtractor()
    extractor.extract_from_text(code)
    
    return [
        {'name': p.name, 'type': p.property_type}
        for p in extractor.properties
    ]


def extract_assertions(code: str) -> List[Dict]:
    """从代码提取断言"""
    extractor = AssertionExtractor()
    extractor.extract_from_text(code)
    
    return [
        {'type': a.assertion_type}
        for a in extractor.assertions
    ]


def extract_assertion_elements(code: str) -> Dict[str, List]:
    """一次性提取所有断言元素"""
    extractor = AssertionExtractor()
    extractor.extract_from_text(code)
    
    return {
        'sequences': [
            {'name': s.name, 'argument_count': len(s.arguments)}
            for s in extractor.sequences
        ],
        'properties': [
            {'name': p.name, 'type': p.property_type}
            for p in extractor.properties
        ],
        'assertions': [
            {'type': a.assertion_type}
            for a in extractor.assertions
        ],
        'sequence_count': len(extractor.sequences),
        'property_count': len(extractor.properties),
        'assertion_count': len(extractor.assertions)
    }


if __name__ == "__main__":
    test_code = '''
module test;
    // Sequence declaration
    sequence simple_seq;
        @(posedge clk) a || b;
    endsequence
    
    // Property declaration
    property prop1;
        always @(posedge clk) a |-> b;
    endproperty
    
    // Immediate assertion
    assert property (@(posedge clk) a == b);
    
    // Concurrent assertion
    assert property (prop1);
    
    // Cover statement
    cover property (simple_seq);
endmodule
'''
    
    print("=== Assertion Extraction ===\n")
    
    result = extract_assertion_elements(test_code)
    print(f"Sequences: {result['sequence_count']}")
    print(f"Properties: {result['property_count']}")
    print(f"Assertions: {result['assertion_count']}")
    
    for s in result['sequences']:
        print(f"  Sequence: {s['name']}")
    for p in result['properties']:
        print(f"  Property: {p['name']} ({p['type']})")
    for a in result['assertions']:
        print(f"  Assertion: {a['type']}")
