"""
Fork/Join Parser - 使用正确的 AST 遍历

提取 fork-join 块：
- fork
- join, join_any, join_none
- 并行进程

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
class ForkJoinBlock:
    """Fork/Join 块"""
    join_type: str = ""  # join, join_any, join_none
    statements: List[str] = field(default_factory=list)


class ForkJoinExtractor:
    def __init__(self):
        self.blocks: List[ForkJoinBlock] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ForkStatement':
                fjb = ForkJoinBlock()
                fjb.join_type = 'join'
                
                if hasattr(node, 'keyword') and node.keyword:
                    kw = str(node.keyword).lower()
                    if 'join_any' in kw:
                        fjb.join_type = 'join_any'
                    elif 'join_none' in kw:
                        fjb.join_type = 'join_none'
                
                # 子进程
                if hasattr(node, 'statements') and node.statements:
                    for stmt in node.statements:
                        if stmt:
                            fjb.statements.append(str(stmt)[:50])
                elif hasattr(node, 'body') and node.body:
                    fjb.statements.append(str(node.body)[:50])
                
                self.blocks.append(fjb)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [
            {'join_type': b.join_type, 'statements': len(b.statements)}
            for b in self.blocks
        ]


def extract_fork_join(code: str) -> List[Dict]:
    return ForkJoinExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
initial begin
    fork
        begin
            #10;
        end
        begin
            #20;
        end
    join
end
'''
    result = extract_fork_join(test_code)
    print(f"Fork/Join blocks: {len(result)}")
