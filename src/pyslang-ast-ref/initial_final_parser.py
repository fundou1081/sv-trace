"""
Initial Block 和 Final Block Parser - 使用 pyslang AST

支持:
- InitialBlock (initial ... end)
- FinalBlock (final ... end)
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
    name: str = ""  # 可选的 label
    statements: List[str] = field(default_factory=list)
    statements_count: int = 0
    has_begin: bool = False  # 是否有 begin...end 包裹


@dataclass
class FinalBlock:
    """final block 信息"""
    name: str = ""  # 可选的 label
    statements: List[str] = field(default_factory=list)
    statements_count: int = 0
    has_begin: bool = False


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
        
        # 名称 (label)
        if hasattr(node, 'label') and node.label:
            block.name = str(node.label).strip()
        
        # 检测是否有 begin...end
        self._check_begin_block(node)[:20]
        
        # 提取语句
        block.statements = self._extract_statements(node)
        block.statements_count = len(block.statements)
        
        self.blocks.append(block)
    
    def _extract_statements(self, node) -> List[str]:
        """从块节点提取语句"""
        statements = []
        
        def traverse(n, depth=0):
            if depth > 10:  # 防止无限递归
                return
            
            try:
                kind_name = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
            except:
                return
            
            # 跳过高层块节点
            if kind_name in ['InitialBlock', 'SequentialBlockStatement', 'StatementList']:
                if hasattr(n, '__iter__'):
                    for child in n:
                        traverse(child, depth + 1)
                return
            
            # 收集语句
            if 'Statement' in kind_name or kind_name == 'ExpressionStatement':
                stmt_text = str(n).strip()
                if stmt_text and len(stmt_text) > 1:
                    # 过滤纯符号
                    if not all(c in ';,{}' for c in stmt_text):
                        statements.append(stmt_text)
            
            # 继续遍历
            if hasattr(n, '__iter__'):
                for child in n:
                    traverse(child, depth + 1)
        
        traverse(node)
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
        
        # 名称 (label)
        if hasattr(node, 'label') and node.label:
            block.name = str(node.label).strip()
        
        # 检测是否有 begin...end
        self._check_begin_block(node)[:20]
        
        # 提取语句
        block.statements = self._extract_statements(node)
        block.statements_count = len(block.statements)
        
        self.blocks.append(block)
    
    def _extract_statements(self, node) -> List[str]:
        """从块节点提取语句"""
        statements = []
        
        def traverse(n, depth=0):
            if depth > 10:
                return
            
            try:
                kind_name = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
            except:
                return
            
            if kind_name in ['FinalBlock', 'SequentialBlockStatement', 'StatementList']:
                if hasattr(n, '__iter__'):
                    for child in n:
                        traverse(child, depth + 1)
                return
            
            if 'Statement' in kind_name or kind_name == 'ExpressionStatement':
                stmt_text = str(n).strip()
                if stmt_text and len(stmt_text) > 1:
                    if not all(c in ';,{}' for c in stmt_text):
                        statements.append(stmt_text)
            
            if hasattr(n, '__iter__'):
                for child in n:
                    traverse(child, depth + 1)
        
        traverse(node)
        return statements
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[FinalBlock]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        return self._extract_from_tree(tree.root)
    
    def get_blocks(self) -> List[FinalBlock]:
        return self.blocks


# ============================================================================
# 便捷函数
# ============================================================================

def extract_initial_blocks(code: str) -> List[Dict]:
    """从 SystemVerilog 代码提取 initial 块"""
    extractor = InitialBlockExtractor()
    blocks = extractor.extract_from_text(code)
    return [
        {
            'name': b.name,
            'statements': b.statements,
            'statements_count': b.statements_count,
            'has_begin': b.has_begin
        }
        for b in blocks
    ]


def extract_final_blocks(code: str) -> List[Dict]:
    """从 SystemVerilog 代码提取 final 块"""
    extractor = FinalBlockExtractor()
    blocks = extractor.extract_from_text(code)
    return [
        {
            'name': b.name,
            'statements': b.statements,
            'statements_count': b.statements_count,
            'has_begin': b.has_begin
        }
        for b in blocks
    ]


def extract_initial_final(code: str) -> Dict[str, List]:
    """一次性提取 initial 和 final 块"""
    initial_extractor = InitialBlockExtractor()
    final_extractor = FinalBlockExtractor()
    
    tree = pyslang.SyntaxTree.fromText(code)
    
    def collect(node):
        try:
            kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
        except:
            return pyslang.VisitAction.Advance
        
        if kind_name == 'InitialBlock':
            initial_extractor._extract_initial(node)
        elif kind_name == 'FinalBlock':
            final_extractor._extract_final(node)
        
        return pyslang.VisitAction.Advance
    
    tree.root.visit(collect)
    
    return {
        'initial': [b.statements_count for b in initial_extractor.blocks],
        'final': [b.statements_count for b in final_extractor.blocks],
        'initial_details': [
            {'name': b.name, 'statements': b.statements, 'count': b.statements_count}
            for b in initial_extractor.blocks
        ],
        'final_details': [
            {'name': b.name, 'statements': b.statements, 'count': b.statements_count}
            for b in final_extractor.blocks
        ]
    }


if __name__ == "__main__":
    test_code = '''
module test;
    // Single statement initial
    initial $display("Start");
    
    // Multi-statement initial with begin-end
    initial begin : init_block
        int count = 0;
        for (int i = 0; i < 10; i++)
            count++;
        $display("Count = %d", count);
    end
    
    // Final block
    final $fclose(fd);
    
    // Final block with begin-end
    final begin
        $display("Cleanup");
        $finish;
    end
endmodule
'''
    
    print("=== Initial/Final Block Extraction ===\n")
    
    print("--- extract_initial_blocks ---")
    initial_blocks = extract_initial_blocks(test_code)
    print(f"Found {len(initial_blocks)} initial blocks")
    for block in initial_blocks:
        print(f"\n  Block: {block['name'] or '(anonymous)'}")
        print(f"    statements: {block['statements_count']}")
        print(f"    has_begin: {block['has_begin']}")
        if block['statements']:
            print(f"    first statement: {block['statements'][0][:50]}...")
    
    print("\n--- extract_final_blocks ---")
    final_blocks = extract_final_blocks(test_code)
    print(f"Found {len(final_blocks)} final blocks")
    for block in final_blocks:
        print(f"\n  Block: {block['name'] or '(anonymous)'}")
        print(f"    statements: {block['statements_count']}")
        print(f"    has_begin: {block['has_begin']}")
        if block['statements']:
            print(f"    first statement: {block['statements'][0][:50]}...")
    
    print("\n--- extract_initial_final (combined) ---")
    combined = extract_initial_final(test_code)
    print(f"Initial blocks: {len(combined['initial'])}, statements: {combined['initial']}")
    print(f"Final blocks: {len(combined['final'])}, statements: {combined['final']}")

    def _check_begin_block(self, node) -> bool:
        """检查是否有 begin...end 块 - 使用 AST 属性"""
        # 检查子节点中是否有 BeginKeyword
        for child in node:
            if not child:
                continue
            try:
                child_kind = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
                if child_kind in ['BeginKeyword', 'SequentialBlockStatement']:
                    return True
            except:
                pass
        return False
