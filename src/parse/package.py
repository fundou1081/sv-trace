"""
Package 解析器 - package/program 提取

SystemVerilog 编译单元:
- package...endpackage
- program...endprogram
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, List
from dataclasses import dataclass, field
import pyslang
from pyslang import SyntaxKind


@dataclass
class PackageItem:
    """package 内 item"""
    kind: str = ""  # Function, Task, Class, Parameter 等
    declaration: str = ""


@dataclass
class PackageDef:
    """package 定义"""
    name: str = ""
    items: List[PackageItem] = field(default_factory=list)
    
    def __post_init__(self):
        self.items = self.items or []


@dataclass
class ProgramDef:
    """program 定义"""
    name: str = ""
    ports: List[str] = field(default_factory=list)
    items: List[str] = field(default_factory=list)


class PackageExtractor:
    def __init__(self, parser=None):
        self.parser = parser
        self.packages: Dict[str, PackageDef] = {}
        self.programs: Dict[str, ProgramDef] = {}
        
        if parser:
            self._extract_all()
    
    def _extract_all(self):
        for key, tree in getattr(self.parser, 'trees', {}).items():
            if tree and hasattr(tree, 'root') and tree.root:
                self._extract_from_tree(tree)
    
    def _extract_from_tree(self, tree):
        def collect(node):
            kn = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            
            if kn == 'PackageDeclaration':
                self._extract_package(node)
            elif kn == 'ProgramDeclaration':
                self._extract_program(node)
            
            return pyslang.VisitAction.Advance
        
        tree.root.visit(collect)
    
    def _extract_package(self, node) -> PackageDef:
        pkg = PackageDef()
        
        # name
        if hasattr(node, 'header') and node.header:
            pkg.name = str(node.header.name).strip() if hasattr(node.header, 'name') else str(node.header)
        
        # items
        if hasattr(node, 'members') and node.members:
            for child in node.members:
                if not child:
                    continue
                kind_name = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
                
                if kind_name != 'SyntaxList':
                    decl = str(child).strip().rstrip(';')
                    if decl:
                        item = PackageItem(kind=kind_name, declaration=decl)
                        pkg.items.append(item)
        
        if pkg.name:
            self.packages[pkg.name] = pkg
        
        return pkg
    
    def _extract_program(self, node) -> ProgramDef:
        prog = ProgramDef()
        
        # name
        if hasattr(node, 'header') and node.header:
            if hasattr(node.header, 'name'):
                prog.name = str(node.header.name).strip()
            prog.ports = [str(p).strip() for p in node.header.ports] if hasattr(node.header, 'ports') else []
        
        # items
        if hasattr(node, 'members') and node.members:
            for child in node.members:
                if child and hasattr(child, 'kind'):
                    decl = str(child).strip().rstrip(';')
                    if decl:
                        prog.items.append(decl)
        
        if prog.name:
            self.programs[prog.name] = prog
        
        return prog
    
    def get_packages(self) -> Dict[str, PackageDef]:
        return self.packages
    
    def get_programs(self) -> Dict[str, ProgramDef]:
        return self.programs


def extract_packages(code: str) -> Dict[str, PackageDef]:
    tree = pyslang.SyntaxTree.fromText(code)
    extractor = PackageExtractor(None)
    extractor._extract_from_tree(tree)
    return extractor.packages


def extract_programs(code: str) -> Dict[str, ProgramDef]:
    tree = pyslang.SyntaxTree.fromText(code)
    extractor = PackageExtractor(None)
    extractor._extract_from_tree(tree)
    return extractor.programs


if __name__ == "__main__":
    test_code = '''
package my_pkg;
    parameter int P1 = 8;
    
    function automatic bit [7:0] add(input bit [7:0] a, b);
        return a + b;
    endfunction
    
    class packet;
        rand bit [7:0] data;
    endclass
endpackage
'''
    
    result = extract_packages(test_code)
    print("=== Package 提取测试 ===")
    for name, pkg in result.items():
        print(f"\nPackage: {name}")
        print(f"  items: {len(pkg.items)}")
        for item in pkg.items:
            print(f"    {item.kind}: {item.declaration[:40]}")


# Program 测试
test_program = '''
program test_prog (
    input clk,
    output [7:0] data
);
    initial begin
        data = 0;
    end
endprogram
'''

ep = extract_programs(test_program)
print("\n=== Program 提取测试 ===")
for name, prog in ep.items():
    print(f"\nProgram: {name}")
    print(f"  ports: {prog.ports}")
    print(f"  items: {len(prog.items)}")
