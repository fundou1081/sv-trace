"""
Checker 解析器 - 使用 pyslang AST

Checker 提取
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import List
from dataclasses import dataclass, field
import pyslang
from pyslang import SyntaxKind


@dataclass
class CheckerProperty:
    """Checker 内的 property/assert"""
    kind: str = ""
    expression: str = ""


@dataclass
class CheckerDef:
    """checker 定义"""
    name: str = ""
    arguments: List[str] = field(default_factory=list)
    assertions: List[CheckerProperty] = field(default_factory=list)


def _collect_nodes(node):
    nodes = []
    def collect(n):
        nodes.append(n)
        return pyslang.VisitAction.Advancee
    node.visit(collect)
    return nodes


class CheckerExtractor:
    def __init__(self, parser=None):
        self.parser = parser
        self.checkers = {}
        if parser:
            self._extract_all()
    
    def _extract_all(self):
        for key, tree in getattr(self.parser, 'trees', {}).items():
            if tree and hasattr(tree, 'root') and tree.root:
                self._extract_from_tree(tree)
    
    def _extract_from_tree(self, tree):
        def collect(node):
            if node.kind.name == 'CheckerDeclaration':
                self._extract_checker(node)
            return pyslang.VisitAction.Advancee
        
        tree.root.visit(collect)
    
    def _extract_checker(self, node):
        checker = CheckerDef()
        
        # name
        if hasattr(node, 'blockName') and node.blockName:
            checker.name = str(node.blockName).strip()
        
        # arguments
        if hasattr(node, 'parent') and node.parent:
            # header arguments
            pass
        
        # assertions - 从字符串提取
        str_repr = str(node)
        
        # 找 assert property
        import re
        for match in re.finditer(r'assert\s+property\s+(\([^)]+\))', str_repr):
            prop = CheckerProperty(kind='assert', expression=match.group(1))
            checker.assertions.append(prop)
        
        for match in re.finditer(r'assume\s+property\s+(\([^)]+\))', str_repr):
            prop = CheckerProperty(kind='assume', expression=match.group(1))
            checker.assertions.append(prop)
        
        for match in re.finditer(r'cover\s+property\s+(\([^)]+\))', str_repr):
            prop = CheckerProperty(kind='cover', expression=match.group(1))
            checker.assertions.append(prop)
        
        if checker.name:
            self.checkers[checker.name] = checker
    
    def get_checkers(self):
        return self.checkers


def extract_checkers(code):
    tree = pyslang.SyntaxTree.fromText(code)
    extractor = CheckerExtractor(None)
    extractor._extract_from_tree(tree)
    return extractor.checkers


if __name__ == "__main__":
    test_code = '''checker parity_check (input bit [7:0] data, input valid);
    always @(posedge clk) begin
        assert property (!valid |-> $stable(data));
    end
endchecker'''

    result = extract_checkers(test_code)
    print("=== Checker 提取测试 ===")
    for name, checker in result.items():
        print(f"Checker: {name}")
        print(f"  assertions: {len(checker.assertions)}")
        for a in checker.assertions:
            print(f"    {a.kind}: {a.expression}")
