"""
Generate 解析器 - 使用 pyslang AST

Generate 块提取 (if/for/case)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import List
from dataclasses import dataclass, field
import pyslang
from pyslang import SyntaxKind, TokenKind


@dataclass
class GenerateItem:
    """generate item: if/case/for"""
    kind: str = ""
    condition: str = ""
    label: str = ""
    body: List[str] = field(default_factory=list)


@dataclass  
class GenerateBlock:
    """generate 块"""
    name: str = ""
    items: List[GenerateItem] = field(default_factory=list)


class GenerateExtractor:
    def __init__(self, parser=None):
        self.parser = parser
        self.blocks = []
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
            # 已经是 root 或者其他类型,直接使用
        
        def collect(node):
            kn = node.kind.name
            
            if kn in ['IfGenerate', 'LoopGenerate', 'CaseGenerate']:
                self._extract_gen_item(node)
            
            return pyslang.VisitAction.Advancee
        
        tree.root.visit(collect)
    
    def _extract_gen_item(self, node):
        item = GenerateItem()
        item.kind = node.kind.name
        
        # condition - 使用 pyslang AST
        if hasattr(node, 'condition') and node.condition:
            item.condition = str(node.condition).strip()
        
        # label - block.begin
        if hasattr(node, 'block') and node.block:
            if hasattr(node.block, 'begin') and node.block.begin:
                item.label = str(node.block.begin).strip()
        
        # body - 从 members 或 block 获取
        if hasattr(node, 'members') and node.members:
            for m in node.members:
                if m:
                    decl = str(m).strip().rstrip(';')
                    if decl:
                        item.body.append(decl)
        
        # 如果 body 为空，尝试从 block 获取
        if not item.body and hasattr(node, 'block') and node.block:
            if hasattr(node.block, 'members') and node.block.members:
                for m in node.block.members:
                    if m:
                        decl = str(m).strip().rstrip(';')
                        if decl:
                            item.body.append(decl)
        
        if item.kind:
            self.blocks.append(GenerateBlock(items=[item]))
    
    def get_blocks(self):
        return self.blocks


def extract_generates(code):
    tree = pyslang.SyntaxTree.fromText(code)
    extractor = GenerateExtractor(None)
    extractor._extract_from_tree(tree)
    return extractor.blocks


if __name__ == "__main__":
    test_code = '''module tb;
    generate
        if (1) begin : GEN_IF
            logic [7:0] data;
        end
    endgenerate
    
    for (genvar i = 0; i < 8; i++) begin : GEN_FOR
        logic [i:0] bits;
    end
    
    case (sel)
        1: begin
            logic a;
        end
    endcase
endmodule'''
    
    result = extract_generates(test_code)
    print("=== Generate ===")
    for blk in result:
        for item in blk.items:
            print(f"\n{item.kind}")
            if item.condition:
                print(f"  condition: {item.condition}")
            if item.label:
                print(f"  label: {item.label}")
            for b in item.body[:3]:
                print(f"  body: {b}")
