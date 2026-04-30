"""
Package 解析器 - 使用 pyslang AST

Package/Program 提取 (不使用正则)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, List
from dataclasses import dataclass, field
import pyslang
from pyslang import SyntaxKind, TokenKind


@dataclass
class PackageItem:
    """package 内的 item"""
    kind: str = ""
    name: str = ""
    declaration: str = ""


@dataclass
class PackageDef:
    """package 定义"""
    name: str = ""
    items: List[PackageItem] = field(default_factory=list)


@dataclass
class ProgramDef:
    """program 定义"""
    name: str = ""
    ports: List[str] = field(default_factory=list)
    items: List[str] = field(default_factory=list)


def _collect_nodes(node):
    nodes = []
    def collect(n):
        nodes.append(n)
        return pyslang.VisitAction.Advance
    node.visit(collect)
    return nodes


def _get_kind(n):
    if hasattr(n, 'kind'):
        return n.kind
    return None


class PackageExtractor:
    def __init__(self, parser=None):
        self.parser = parser
        self.packages = {}
        self.programs = {}
        if parser:
            self._extract_all()
    
    def _extract_all(self):
        for key, tree in getattr(self.parser, 'trees', {}).items():
            if tree and hasattr(tree, 'root') and tree.root:
                self._extract_from_tree(tree)
    
    def _extract_from_tree(self, tree):
        # 支持传入 tree 或 root
        if hasattr(tree, 'root') and not hasattr(tree, 'visit'):
            tree = tree.root
        elif not hasattr(tree, 'visit'):
            pass  # 已经是 root,直接使用
        
        root = tree.root if hasattr(tree, "root") else tree
        
        def collect(node):
            kn = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            
            if kn == 'PackageDeclaration':
                self._extract_package(node)
            elif kn == 'ProgramDeclaration':
                self._extract_program(node)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _extract_package(self, node):
        pkg = PackageDef()
        
        # name from header
        if node.header and node.header.name:
            pkg.name = str(node.header.name.valueText)
        
        # members
        if node.members:
            # 遍历 members
            for m in node.members:
                if not m:
                    continue
                
                item = PackageItem()
                item.kind = m.kind.name if hasattr(m.kind, 'name') else str(m.kind)
                item.declaration = str(m).strip().rstrip(';')
                
                # 函数/任务名称
                if item.kind == 'FunctionDeclaration' or item.kind == 'TaskDeclaration':
                    # 从 FunctionPrototype 获取名称
                    if hasattr(m, 'prototype') and m.prototype:
                        for child in m.prototype:
                            if child.kind.name == 'IdentifierName':
                                item.name = str(child)
                                break
                    # 备选：从 declaration 字符串提取
                    if not item.name:
                        decl = item.declaration
                        # function NAME(...);
                        import re
                        match = re.search(r'(function|task)\s+(?:(?:virtual|static|automatic)\s+)?(\w+(?:\s+\w+)*?)\s+(\w+)', decl)
                        if match:
                            rets = match.group(1)
                            item.name = match.group(3)
                
                # class 名称
                elif item.kind == 'ClassDeclaration':
                    if hasattr(m, 'name') and m.name:
                        item.name = str(m.name)
                
                # parameter 名称
                elif item.kind == 'ParameterDeclarationStatement' or item.kind == 'ParameterDeclaration':
                    # 从 Declarator 获取
                    for child in m:
                        if child.kind.name == 'Declarator':
                            for c in child:
                                if c.kind.name == 'IdentifierName':
                                    item.name = str(c)
                                    break
                
                if item.declaration:
                    pkg.items.append(item)
        
        if pkg.name:
            self.packages[pkg.name] = pkg
        
        return pkg
    
    def _extract_program(self, node):
        prog = ProgramDef()
        
        # name from header
        if node.header and node.header.name:
            prog.name = str(node.header.name.valueText)
        
        # ports from header
        if node.header and node.header.ports:
            for p in node.header.ports:
                prog.ports.append(str(p).strip())
        
        # members
        if node.members:
            for m in node.members:
                if m and hasattr(m, 'kind'):
                    decl = str(m).strip()
                    if decl:
                        prog.items.append(decl)
        
        if prog.name:
            self.programs[prog.name] = prog
        
        return prog
    
    def get_packages(self):
        return self.packages
    
    def get_programs(self):
        return self.programs


def extract_packages(code):
    tree = pyslang.SyntaxTree.fromText(code)
    extractor = PackageExtractor(None)
    extractor._extract_from_tree(tree)
    return extractor.packages


def extract_programs(code):
    tree = pyslang.SyntaxTree.fromText(code)
    extractor = PackageExtractor(None)
    extractor._extract_from_tree(tree)
    return extractor.programs


if __name__ == "__main__":
    test_code = '''package my_pkg;
    parameter int P1 = 8;
    
    function bit [7:0] add(input bit [7:0] a, b);
        return a + b;
    endfunction
    
    class packet;
        rand bit [7:0] data;
    endclass
endpackage'''

    result = extract_packages(test_code)
    print("=== Package 提取测试 ===")
    for name, pkg in result.items():
        print(f"\nPackage: {name}")
        print(f"  items: {len(pkg.items)}")
        for item in pkg.items[:5]:
            print(f"    {item.kind}: {item.name or item.declaration[:30]}")
    
    # Program
    test_prog = '''program test_prog (input clk, output [7:0] data);
    initial begin
        data = 0;
    end
endprogram'''

    ep = extract_programs(test_prog)
    print("\n=== Program 提取测试 ===")
    for name, prog in ep.items():
        print(f"\nProgram: {name}")
        print(f"  ports: {prog.ports[:2]}")
        print(f"  items: {len(prog.items)}")
