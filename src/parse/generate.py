"""
Generate 解析器 - generate 块提取

SystemVerilog 条件编译:
- generate...endgenerate
- if-gen, case-gen, for-gen
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, List
from dataclasses import dataclass, field
import pyslang
from pyslang import SyntaxKind


@dataclass
class GenerateItem:
    kind: str = ""
    condition: str = ""
    body: List[str] = field(default_factory=list)


@dataclass
class GenerateBlock:
    name: str = ""
    items: List[GenerateItem] = field(default_factory=list)


class GenerateExtractor:
    def __init__(self, parser=None):
        self.parser = parser
        self.blocks: List[GenerateBlock] = []
        
        if parser:
            self._extract_all()
    
    def _extract_all(self):
        for key, tree in getattr(self.parser, 'trees', {}).items():
            if tree and hasattr(tree, 'root') and tree.root:
                self._extract_from_tree(tree)
    
    def _extract_from_tree(self, tree):
        def collect(node):
            kn = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            
            if kn in ['IfGenerate', 'LoopGenerate', 'CaseGenerate', 'IfGenerateRegion', 'CaseGenerateRegion', 'GenerateRegion']:
                self._extract_generate(node)
            
            return pyslang.VisitAction.Advance
        
        tree.root.visit(collect)
    
    def _extract_generate(self, node):
        item = GenerateItem()
        item.kind = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
        
        # condition
        if hasattr(node, 'condition') and node.condition:
            item.condition = str(node.condition).strip()
        elif hasattr(node, 'expression') and node.expression:
            item.condition = str(node.expression).strip()
        
        # body - members 或 block
        members = None
        if hasattr(node, 'members'):
            members = node.members
        elif hasattr(node, 'block'):
            members = node.block
        
        if members:
            for child in members:
                if not child:
                    continue
                decl = str(child).strip().rstrip(';')
                if decl:
                    item.body.append(decl)
        
        if item.kind or item.body:
            self.blocks.append(GenerateBlock(items=[item]))
    
    def get_blocks(self) -> List[GenerateBlock]:
        return self.blocks


def extract_generates(code: str) -> List[GenerateBlock]:
    tree = pyslang.SyntaxTree.fromText(code)
    extractor = GenerateExtractor(None)
    extractor._extract_from_tree(tree)
    return extractor.blocks


if __name__ == "__main__":
    test_code = '''
module tb;
    generate
        if (1) begin : GEN_IF
            logic [7:0] data;
        end
    endgenerate
    
    for (genvar i = 0; i < 8; i++) begin : GEN_FOR
        logic [i:0] bits;
    end
    
    case (1)
        1: begin
            logic a;
        end
    endcase
endmodule
'''
    
    result = extract_generates(test_code)
    print("=== Generate 提取测试 ===")
    print(f"Found {len(result)} items")
    for blk in result:
        for item in blk.items:
            print(f"  {item.kind}")
            if item.condition:
                print(f"    condition: {item.condition}")
            for b in item.body[:3]:
                print(f"    {b}")
