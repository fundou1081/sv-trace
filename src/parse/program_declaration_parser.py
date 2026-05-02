"""
Program Declaration Parser - 使用正确的 AST 遍历

提取 program 声明：
- program 块
- 端口声明
- 时间控制

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
class ProgramDeclaration:
    name: str = ""
    ports: List[str] = field(default_factory=list)
    members: List[str] = field(default_factory=list)


class ProgramDeclarationExtractor:
    def __init__(self):
        self.programs: List[ProgramDeclaration] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ProgramDeclaration':
                pd = ProgramDeclaration()
                if hasattr(node, 'name') and node.name:
                    pd.name = str(node.name)
                
                # 端口
                for child in node:
                    if not child:
                        continue
                    try:
                        child_kind = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
                    except:
                        continue
                    
                    if child_kind in ['AnsiPortDeclaration', 'NonAnsiPortDeclaration', 'PortDeclaration']:
                        if hasattr(child, 'name') and child.name:
                            pd.ports.append(str(child.name))
                
                self.programs.append(pd)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [
            {'name': pd.name, 'ports': pd.ports, 'port_count': len(pd.ports)}
            for pd in self.programs
        ]


def extract_programs(code: str) -> List[Dict]:
    return ProgramDeclarationExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
program test(input clk, input [7:0] data);
    initial begin
        $display("Hello");
    end
endprogram
'''
    result = extract_programs(test_code)
    print(f"Programs: {len(result)}")
