"""
Checker 解析器 - 使用 pyslang AST

支持:
- CheckerDeclaration
- CheckerInstance
- CheckerDataDeclaration
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List
import pyslang
from pyslang import SyntaxKind


@dataclass
class CheckerProperty:
    """checker 内 property"""
    name: str = ""
    expression: str = ""


@dataclass
class CheckerDef:
    """checker 定义"""
    name: str = ""
    properties: List[CheckerProperty] = field(default_factory=list)
    variables: List[str] = field(default_factory=list)
    instances: List[str] = field(default_factory=list)


class CheckerExtractor:
    def __init__(self, parser=None):
        self.parser = parser
        self.checkers = {}
        
        if parser:
            self._extract_all()
    
    def _extract_all(self):
        for key, tree in getattr(self.parser, 'trees', {}).items():
            root = tree.root if hasattr(tree, 'root') else tree
            self._extract_from_tree(root)
    
    def _extract_from_tree(self, root):
        def collect(node):
            kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            
            if kind_name == 'CheckerDeclaration':
                self._extract_checker(node)
            elif kind_name == 'CheckerInstantiation':
                self._extract_instance(node)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _extract_checker(self, node):
        checker = CheckerDef()
        
        if hasattr(node, 'name') and node.name:
            checker.name = str(node.name)
        
        # properties
        if hasattr(node, 'properties') and node.properties:
            for prop in node.properties:
                if prop:
                    cp = CheckerProperty()
                    if hasattr(prop, 'name'):
                        cp.name = str(prop.name)
                    if hasattr(prop, 'propertySpec'):
                        cp.expression = str(prop.propertySpec)
                    checker.properties.append(cp)
        
        # data declarations
        if hasattr(node, 'dataDeclarations') and node.dataDeclarations:
            for decl in node.dataDeclarations:
                if decl:
                    checker.variables.append(str(decl))
        
        if checker.name:
            self.checkers[checker.name] = checker
    
    def _extract_instance(self, node):
        # 从字符串提取 checker 实例
        node_str = str(node)
        if 'checker' in node_str.lower():
            # 这是 checker 实例引用，记录但不创建新 checker
            pass
    
    def get_checkers(self):
        return self.checkers


def extract_checkers(code):
    tree = pyslang.SyntaxTree.fromText(code)
    extractor = CheckerExtractor(None)
    extractor._extract_from_tree(tree)
    return extractor.checkers


if __name__ == "__main__":
    test_code = '''
module test;
    checker mem_checker(logic [7:0] addr, data);
        property addr_valid;
            @(posedge clk) disable iff (rst) addr != data;
        endproperty
        
        property data_check;
            data |-> ##1 ack;
        endproperty
    endchecker
endmodule
'''
    
    result = extract_checkers(test_code)
    print("=== Checker Extraction ===")
    for name, chk in result.items():
        print(f"\n{name}:")
        print(f"  properties: {len(chk.properties)}")
        print(f"  variables: {len(chk.variables)}")
