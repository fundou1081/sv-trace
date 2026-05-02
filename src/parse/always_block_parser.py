"""
Always Block Parser - 使用正确的 AST 遍历

提取 always, always_ff, always_comb, always_latch 块：
- always 块
- always_ff 块
- always_comb 块
- always_latch 块

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
class AlwaysBlock:
    """Always 块"""
    block_type: str = ""  # always, always_ff, always_comb, always_latch
    sensitivity_list: str = ""
    statements: List[str] = field(default_factory=list)


class AlwaysBlockExtractor:
    def __init__(self):
        self.always_blocks: List[AlwaysBlock] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            # AlwaysBlock, AlwaysFFBlock, AlwaysCombBlock, AlwaysLatchBlock
            if kind_name in ['AlwaysBlock', 'AlwaysFFBlock', 'AlwaysCombBlock', 'AlwaysLatchBlock']:
                ab = AlwaysBlock()
                ab.block_type = kind_name.replace('Block', '').lower()
                
                # 敏感性列表
                if hasattr(node, 'control') and node.control:
                    ctrl = node.control
                    if hasattr(ctrl, 'eventExpression') and ctrl.eventExpression:
                        ab.sensitivity_list = str(ctrl.eventExpression)
                    elif hasattr(ctrl, 'sensitivity') and ctrl.sensitivity:
                        ab.sensitivity_list = str(ctrl.sensitivity)
                
                # 语句
                if hasattr(node, 'statement') and node.statement:
                    ab.statements.append(str(node.statement)[:100])
                elif hasattr(node, 'body') and node.body:
                    ab.statements.append(str(node.body)[:100])
                
                self.always_blocks.append(ab)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        
        return [
            {
                'type': ab.block_type,
                'sensitivity': ab.sensitivity_list[:50],
                'statements_count': len(ab.statements)
            }
            for ab in self.always_blocks
        ]


def extract_always_blocks(code: str) -> List[Dict]:
    return AlwaysBlockExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
module test;
    always @(posedge clk) begin
        q <= d;
    end
    
    always_ff @(posedge clk) begin
        if (rst) q <= 0;
    end
    
    always_comb begin
        y = a & b;
    end
    
    always_latch begin
        if (enable) q <= d;
    end
endmodule
'''
    result = extract_always_blocks(test_code)
    for item in result:
        print(f"Always block: {item['type']} ({item['statements_count']} stmts)")
