"""
Module Declaration Parser - 使用正确的 AST 遍历

提取 module 声明：
- ModuleDeclaration
- 模块名称
- 端口
- 参数

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
class ModulePort:
    name: str = ""
    direction: str = ""
    width: str = ""


@dataclass
class ModuleParameter:
    name: str = ""
    default_value: str = ""


@dataclass
class ModuleDeclaration:
    name: str = ""
    ports: List[ModulePort] = field(default_factory=list)
    parameters: List[ModuleParameter] = field(default_factory=list)


class ModuleDeclarationExtractor:
    def __init__(self):
        self.modules: List[ModuleDeclaration] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ModuleDeclaration':
                mod = self._extract_module(node)
                if mod:
                    self.modules.append(mod)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _extract_module(self, node) -> ModuleDeclaration:
        mod = ModuleDeclaration()
        
        if hasattr(node, 'name') and node.name:
            mod.name = str(node.name)
        
        # 提取端口和参数
        for child in node:
            if not child:
                continue
            try:
                child_kind = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            except:
                continue
            
            # 端口
            if child_kind in ['AnsiPortDeclaration', 'NonAnsiPortDeclaration', 'PortDeclaration']:
                p = ModulePort()
                if hasattr(child, 'name') and child.name:
                    p.name = str(child.name)
                if hasattr(child, 'direction') and child.direction:
                    p.direction = str(child.direction).lower()
                if p.name:
                    mod.ports.append(p)
            
            # 参数
            elif child_kind in ['ParameterDeclaration', 'LocalParameterDeclaration']:
                p = ModuleParameter()
                if hasattr(child, 'name') and child.name:
                    p.name = str(child.name)
                if hasattr(child, 'defaultValue') and child.defaultValue:
                    p.default_value = str(child.defaultValue)
                mod.parameters.append(p)
        
        return mod if mod.name else None
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        
        return [
            {
                'name': m.name,
                'ports': [{'name': p.name, 'dir': p.direction} for p in m.ports],
                'parameters': [{'name': p.name, 'default': p.default_value} for p in m.parameters]
            }
            for m in self.modules
        ]
    
    def extract_from_file(self, filepath: str) -> List[Dict]:
        with open(filepath, 'r') as f:
            code = f.read()
        return self.extract_from_text(code, filepath)


def extract_modules(code: str) -> List[Dict]:
    return ModuleDeclarationExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
module test #(
    parameter WIDTH = 8,
    parameter DEPTH = 16
) (
    input clk,
    input [WIDTH-1:0] data,
    output [WIDTH-1:0] q
);
endmodule
'''
    result = extract_modules(test_code)
    for m in result:
        print(f"Module: {m['name']}, ports: {len(m['ports'])}, params: {len(m['parameters'])}")
