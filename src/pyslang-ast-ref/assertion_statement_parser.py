"""
Assertion Statement Parser - 使用正确的 AST 遍历

提取断言语句：
- assert property
- assume property
- cover property
- immediate assertions

注意：此文件不包含任何正则表达式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import pyslang
from pyslang import SyntaxKind


@dataclass
class AssertionStatement:
    """断言语句"""
    stmt_type: str = ""  # assert, assume, cover, assertNoClock
    property_expr: str = ""
    action_block: str = ""  # then/else 分支


@dataclass
class ImmediateAssertion:
    """立即断言"""
    expr: str = ""
    then_stmt: str = ""
    else_stmt: str = ""


class AssertionStatementExtractor:
    """提取断言语句"""
    
    def __init__(self):
        self.assertions: List[AssertionStatement] = []
        self.immediate_assertions: List[ImmediateAssertion] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            # 延迟断言
            if kind_name == 'AssertPropertyStatement':
                a = AssertionStatement()
                a.stmt_type = 'assert'
                if hasattr(node, 'property') and node.property:
                    a.property_expr = str(node.property)
                if hasattr(node, 'action') and node.action:
                    a.action_block = str(node.action)
                self.assertions.append(a)
            
            elif kind_name == 'AssumePropertyStatement':
                a = AssertionStatement()
                a.stmt_type = 'assume'
                if hasattr(node, 'property') and node.property:
                    a.property_expr = str(node.property)
                self.assertions.append(a)
            
            elif kind_name == 'CoverPropertyStatement':
                a = AssertionStatement()
                a.stmt_type = 'cover'
                if hasattr(node, 'property') and node.property:
                    a.property_expr = str(node.property)
                self.assertions.append(a)
            
            # 即时断言
            elif kind_name == 'ImmediateAssertStatement':
                ia = ImmediateAssertion()
                if hasattr(node, 'expression') and node.expression:
                    ia.expr = str(node.expression)
                if hasattr(node, 'thenStatement') and node.thenStatement:
                    ia.then_stmt = str(node.thenStatement)
                if hasattr(node, 'elseStatement') and node.elseStatement:
                    ia.else_stmt = str(node.elseStatement)
                self.immediate_assertions.append(ia)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> Dict:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        
        return {
            'assert_property': [a.property_expr for a in self.assertions if a.stmt_type == 'assert'],
            'assume_property': [a.property_expr for a in self.assertions if a.stmt_type == 'assume'],
            'cover_property': [a.property_expr for a in self.assertions if a.stmt_type == 'cover'],
            'immediate_assertions': [
                {
                    'expr': ia.expr[:50],
                    'has_then': bool(ia.then_stmt),
                    'has_else': bool(ia.else_stmt)
                }
                for ia in self.immediate_assertions
            ]
        }
    
    def extract_from_file(self, filepath: str) -> Dict:
        with open(filepath, 'r') as f:
            code = f.read()
        return self.extract_from_text(code, filepath)


def extract_assertion_statements(code: str) -> Dict:
    """便捷函数"""
    return AssertionStatementExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
module test;
    // 延迟断言
    assert property (@(posedge clk) req |-> ack);
    assume property (@(posedge clk) valid |-> ##[1:3] ready);
    cover property (@(posedge clk) start |-> ##1 done);
    
    // 即时断言
    always @(posedge clk) begin
        assert (data >= 0) else $error("Negative data");
    end
endmodule
'''
    
    print("=== Assertion Statement Extraction ===\n")
    result = extract_assertion_statements(test_code)
    
    print("Assert Property:")
    for p in result['assert_property']:
        print(f"  - {p[:60]}...")
    
    print(f"\nAssume Property: {len(result['assume_property'])}")
    print(f"Cover Property: {len(result['cover_property'])}")
    print(f"Immediate Assertions: {len(result['immediate_assertions'])}")
