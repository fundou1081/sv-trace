"""
Final Block Parser - 使用 pyslang AST

支持:
- FinalBlock (final ... end)
- InitialBlock (initial ... end)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import pyslang
from pyslang import SyntaxKind


@dataclass
class InitialBlock:
    """initial block 信息"""
    name: str = ""
    statements: List[str] = field(default_factory=list)
    source_range: str = ""


@dataclass
class FinalBlock:
    """final block 信息"""
    name: str = ""
    statements: List[str] = field(default_factory=list)
    source_range: str = ""


class InitialBlockExtractor:
    """从 SystemVerilog 代码中提取 initial 块"""
    
    def __init__(self):
        self.blocks: List[InitialBlock] = []
    
    def _extract_from_tree(self, root) -> List[InitialBlock]:
        self.blocks = []
        
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'InitialBlock':
                self._extract_initial(node)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
        return self.blocks
    
    def _extract_initial(self, node):
        """提取单个 initial 块"""
        block = InitialBlock()
        
        # 名称
        if hasattr(node, 'label') and node.label:
            block.name = str(node.label)
        
        # 提取语句 - InitialBlock 结构包含 StatementList
        statements = self._get_statements(node)
        block.statements = statements
        
        self.blocks.append(block)
    
    def _get_statements(self, node) -> List[str]:
        """从块节点提取语句列表"""
        statements = []
        
        # 遍历节点查找 StatementList 或 statements
        for child in node:
            child_kind = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            
            if 'Statement' in child_kind or child_kind == 'StatementList':
                if hasattr(child, 'statements'):
                    for stmt in child.statements:
                        if stmt:
                            statements.append(str(stmt))
                elif hasattr(child, 'items'):
                    for item in child.items:
                        if item:
                            statements.append(str(item))
                elif hasattr(child, '__iter__'):
                    for item in child:
                        if item:
                            statements.append(str(item))
                else:
                    statements.append(str(child))
        
        return statements
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[InitialBlock]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        return self._extract_from_tree(tree.root)
    
    def get_blocks(self) -> List[InitialBlock]:
        return self.blocks


class FinalBlockExtractor:
    """从 SystemVerilog 代码中提取 final 块"""
    
    def __init__(self):
        self.blocks: List[FinalBlock] = []
    
    def _extract_from_tree(self, root) -> List[FinalBlock]:
        self.blocks = []
        
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'FinalBlock':
                self._extract_final(node)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
        return self.blocks
    
    def _extract_final(self, node):
        """提取单个 final 块"""
        block = FinalBlock()
        
        # 名称
        if hasattr(node, 'label') and node.label:
            block.name = str(node.label)
        
        # 提取语句
        statements = self._get_statements(node)
        block.statements = statements
        
        self.blocks.append(block)
    
    def _get_statements(self, node) -> List[str]:
        """从块节点提取语句列表"""
        statements = []
        
        for child in node:
            child_kind = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            
            if 'Statement' in child_kind or child_kind == 'StatementList':
                if hasattr(child, 'statements'):
                    for stmt in child.statements:
                        if stmt:
                            statements.append(str(stmt))
                elif hasattr(child, 'items'):
                    for item in child.items:
                        if item:
                            statements.append(str(item))
                elif hasattr(child, '__iter__'):
                    for item in child:
                        if item:
                            statements.append(str(item))
                else:
                    statements.append(str(child))
        
        return statements
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[FinalBlock]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        return self._extract_from_tree(tree.root)
    
    def get_blocks(self) -> List[FinalBlock]:
        return self.blocks


class InitialFinalExtractor:
    """Combined extractor for Initial and Final blocks"""
    
    def __init__(self):
        self.initial_blocks: List[InitialBlock] = []
        self.final_blocks: List[FinalBlock] = []
    
    def extract_from_text(self, code: str, source: str = "<text>") -> Dict:
        """提取 initial 和 final 块"""
        tree = pyslang.SyntaxTree.fromText(code, source)
        root = tree.root
        
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'InitialBlock':
                self._extract_initial(node)
            elif kind_name == 'FinalBlock':
                self._extract_final(node)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
        
        return {
            'initial': [
                {'name': b.name, 'statements': b.statements, 'count': len(b.statements)}
                for b in self.initial_blocks
            ],
            'final': [
                {'name': b.name, 'statements': b.statements, 'count': len(b.statements)}
                for b in self.final_blocks
            ]
        }
    
    def _extract_initial(self, node):
        block = InitialBlock()
        if hasattr(node, 'label') and node.label:
            block.name = str(node.label)
        block.statements = self._get_statements(node)
        self.initial_blocks.append(block)
    
    def _extract_final(self, node):
        block = FinalBlock()
        if hasattr(node, 'label') and node.label:
            block.name = str(node.label)
        block.statements = self._get_statements(node)
        self.final_blocks.append(block)
    
    def _get_statements(self, node) -> List[str]:
        statements = []
        for child in node:
            child_kind = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            if 'Statement' in child_kind or child_kind == 'StatementList':
                if hasattr(child, 'statements'):
                    for stmt in child.statements:
                        if stmt:
                            statements.append(str(stmt))
                elif hasattr(child, '__iter__'):
                    for item in child:
                        if item:
                            statements.append(str(item))
        return statements


# ============================================================================
# 便捷函数
# ============================================================================

def extract_initial_blocks(code: str) -> List[Dict]:
    """从 SystemVerilog 代码提取 initial 块"""
    extractor = InitialBlockExtractor()
    blocks = extractor.extract_from_text(code)
    return [{'name': b.name, 'statements': b.statements, 'count': len(b.statements)} for b in blocks]


def extract_final_blocks(code: str) -> List[Dict]:
    """从 SystemVerilog 代码提取 final 块"""
    extractor = FinalBlockExtractor()
    blocks = extractor.extract_from_text(code)
    return [{'name': b.name, 'statements': b.statements, 'count': len(b.statements)} for b in blocks]


def extract_initial_final(code: str) -> Dict:
    """从 SystemVerilog 代码提取 initial 和 final 块"""
    extractor = InitialFinalExtractor()
    return extractor.extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
module test;
    initial begin
        $display("Start at %0t", $time);
        #10;
    end
    
    initial
        $display("Init simple");
    
    final $finish($time);
    
    final begin
        $display("Cleanup at %0t", $time);
        $finish;
    end
endmodule
'''
    
    print("=== Initial/Final Block Extraction ===\n")
    
    print("--- extract_initial_blocks ---")
    initial_blocks = extract_initial_blocks(test_code)
    print(f"Found {len(initial_blocks)} initial blocks")
    
    print("\n--- extract_final_blocks ---")
    final_blocks = extract_final_blocks(test_code)
    print(f"Found {len(final_blocks)} final blocks")
    
    print("\n--- extract_initial_final (combined) ---")
    combined = extract_initial_final(test_code)
    print(f"Initial: {len(combined['initial'])}, Final: {len(combined['final'])}")
    
    for block in final_blocks:
        print(f"\nFinal block: {block['name'] or '(anonymous)'}")
        for stmt in block['statements']:
            print(f"  {stmt[:60]}...")
