"""
Assertion Parser - 使用正确的 AST 遍历

断言、序列、属性提取

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
class SequenceExpr:
    name: str = ""
    type: str = ""


@dataclass
class PropertyExpr:
    name: str = ""
    type: str = ""


@dataclass
class AssertionStmt:
    statement_type: str = ""  # assert, assume, cover
    severity: str = ""


class AssertionExtractor:
    """提取断言相关 - 使用正确的 AST 遍历"""
    
    def __init__(self):
        self.sequences: List[SequenceExpr] = []
        self.properties: List[PropertyExpr] = []
        self.assertions: List[AssertionStmt] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            # 序列声明
            if kind_name == 'SequenceDeclaration':
                seq = SequenceExpr()
                if hasattr(node, 'name') and node.name:
                    seq.name = str(node.name)
                self.sequences.append(seq)
            
            # 属性声明
            elif kind_name == 'PropertyDeclaration':
                prop = PropertyExpr()
                if hasattr(node, 'name') and node.name:
                    prop.name = str(node.name)
                self.properties.append(prop)
            
            # 断言语句
            elif kind_name in ['AssertPropertyStatement', 'AssumePropertyStatement', 
                              'CoverPropertyStatement', 'ImmediateAssertStatement']:
                stmt = AssertionStmt()
                if 'Assert' in kind_name:
                    stmt.statement_type = 'assert'
                elif 'Assume' in kind_name:
                    stmt.statement_type = 'assume'
                elif 'Cover' in kind_name:
                    stmt.statement_type = 'cover'
                
                self.assertions.append(stmt)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>"):
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return {
            'sequences': len(self.sequences),
            'properties': len(self.properties),
            'assertions': len(self.assertions)
        }


def extract_assertion_expr(code: str) -> Dict:
    return AssertionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
sequence s1;
    a |-> b;
endsequence

property p1;
    always @ (posedge clk) a |-> b;
endproperty

assert property (p1);
cover property (s1);
'''
    
    result = extract_assertion_expr(test_code)
    print(result)
