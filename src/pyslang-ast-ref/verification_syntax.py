"""
Verification Syntax Parser - 使用正确的 AST 遍历

验证语法提取 (RandCase, RandSequence, Let等)

注意：此文件不包含任何正则表达式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict
import pyslang
from pyslang import SyntaxKind


@dataclass
class RandCaseItem:
    constraint: str = ""


@dataclass
class RandSequence:
    name: str = ""


@dataclass
class LetDeclaration:
    name: str = ""
    expression: str = ""


class VerificationSyntaxExtractor:
    """提取验证语法"""
    
    def __init__(self):
        self.rand_cases: List[RandCaseItem] = []
        self.rand_sequences: List[RandSequence] = []
        self.let_declarations: List[LetDeclaration] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            # RandCaseStatement
            if kind_name == 'RandCaseStatement':
                item = RandCaseItem()
                if hasattr(node, 'condition') and node.condition:
                    item.constraint = str(node.condition)
                self.rand_cases.append(item)
            
            # RandSequenceStatement
            elif kind_name == 'RandSequenceStatement':
                seq = RandSequence()
                if hasattr(node, 'name') and node.name:
                    seq.name = str(node.name)
                self.rand_sequences.append(seq)
            
            # LetDeclaration
            elif kind_name == 'LetDeclaration':
                let = LetDeclaration()
                if hasattr(node, 'name') and node.name:
                    let.name = str(node.name)
                if hasattr(node, 'expression') and node.expression:
                    let.expression = str(node.expression)
                self.let_declarations.append(let)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> Dict:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return {
            'rand_cases': [{'constraint': c.constraint} for c in self.rand_cases],
            'rand_sequences': [{'name': s.name} for s in self.rand_sequences],
            'let_declarations': [{'name': l.name, 'expr': l.expression[:30]} for l in self.let_declarations]
        }


def extract_verification_syntax(code: str) -> Dict:
    return VerificationSyntaxExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
module test;
    randcase
        1: $display("1");
        2: $display("2");
    endcase
    
    let x = a + b;
endmodule
'''
    result = extract_verification_syntax(test_code)
    print(result)
