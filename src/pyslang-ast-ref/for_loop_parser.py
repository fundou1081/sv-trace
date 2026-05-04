"""
For Loop Parser - 使用正确的 AST 遍历

提取 for 循环：
- 初始化
- 条件
- 步进
- 循环体

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
class ForLoop:
    variable: str = ""
    init: str = ""
    condition: str = ""
    step: str = ""
    body: str = ""


class ForLoopExtractor:
    def __init__(self):
        self.loops: List[ForLoop] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ForLoop':
                fl = ForLoop()
                
                if hasattr(node, 'variable') and node.variable:
                    fl.variable = str(node.variable)
                if hasattr(node, 'initial') and node.initial:
                    fl.init = str(node.initial)
                if hasattr(node, 'condition') and node.condition:
                    fl.condition = str(node.condition)
                if hasattr(node, 'step') and node.step:
                    fl.step = str(node.step)
                if hasattr(node, 'body') and node.body:
                    fl.body = str(node.body)[:50]
                
                self.loops.append(fl)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        
        return [
            {
                'var': fl.variable,
                'init': fl.init[:20],
                'cond': fl.condition[:20],
                'step': fl.step[:20]
            }
            for fl in self.loops
        ]


def extract_for_loops(code: str) -> List[Dict]:
    return ForLoopExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
for (int i = 0; i < 10; i++) begin
    $display(i);
end
'''
    result = extract_for_loops(test_code)
    print(f"For loops: {len(result)}")
