"""
Generate 解析器 - 使用 pyslang AST

Generate 块提取 (不使用正则)
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
    body: List[str] = field(default_factory=list)


@dataclass  
class GenerateBlock:
    """generate 块"""
    name: str = ""
    items: List[GenerateItem] = field(default_factory=list)


def _collect_nodes(node):
    nodes = []
    def collect(n):
        nodes.append(n)
        return pyslang.VisitAction.Advance
    node.visit(collect)
    return nodes


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
        def collect(node):
            kn = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            
            if kn in ['IfGenerate', 'LoopGenerate', 'CaseGenerate', 'GenerateRegion', 'GenerateBlock']:
                self._extract_gen_item(node)
            
            return pyslang.VisitAction.Advance
        
        tree.root.visit(collect)
    
    def _extract_gen_item(self, node):
        item = GenerateItem()
        item.kind = node.kind.name
        
        all_nodes = _collect_nodes(node)
        
        # 条件/表达式 - 从字符串提取
        str_repr = str(node).strip()
        
        if item.kind == 'IfGenerate':
            import re
            m = re.search(r'if\s*\(([^)]+)\)', str_repr)
            if m:
                item.condition = m.group(1)
        
        elif item.kind == 'LoopGenerate':
            import re
            m = re.search(r'for\s*\(([^)]+)\)', str_repr)
            if m:
                item.condition = m.group(1)
        
        elif item.kind == 'CaseGenerate':
            import re
            m = re.search(r'case\s*\(([^)]+)\)', str_repr)
            if m:
                item.condition = m.group(1)
        
        # body - 提取内部声明
        for m in node.members if hasattr(node, 'members') else []:
            if m and hasattr(m, 'kind') and 'Declaration' in m.kind.name:
                decl = str(m).strip()
                if decl:
                    item.body.append(decl)
        
        # GenerateBlock 有 label
        if hasattr(node, 'begin') and node.begin:
            item.condition = str(node.begin).strip()
        
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
    print("=== Generate 提取测试 ===")
    print(f"Found {len(result)} blocks")
    for blk in result:
        for item in blk.items:
            print(f"  {item.kind}")
            if item.condition:
                print(f"    condition: {item.condition}")
            for b in item.body[:3]:
                print(f"    {b}")
