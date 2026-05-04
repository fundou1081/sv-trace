"""
Parallel Block Statement Parser - 使用正确的 AST 遍历

提取并行块语句：
- ParallelBlockStatement
- ForkStatement

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ParallelBlock:
    name: str = ""
    statements: int = 0


class ParallelBlockExtractor:
    def __init__(self):
        self.blocks: List[ParallelBlock] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['ParallelBlockStatement', 'ForkStatement', 'JoinAnyStatement', 'JoinNoneStatement']:
                pb = ParallelBlock()
                if hasattr(node, 'name') and node.name:
                    pb.name = str(node.name)
                
                count = 0
                def count_stmts(n, c=[0]):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'Statement' in kn or 'Block' in kn:
                        c[0] += 1
                    return pyslang.VisitAction.Advance
                node.visit(count_stmts)
                pb.statements = count
                
                self.blocks.append(pb)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': b.name or '(anonymous)', 'statements': b.statements} for b in self.blocks]


def extract_parallel_blocks(code: str) -> List[Dict]:
    return ParallelBlockExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
fork
    begin
        #10;
    end
    begin
        #20;
    end
join_any
'''
    result = extract_parallel_blocks(test_code)
    print(f"Parallel blocks: {len(result)}")
