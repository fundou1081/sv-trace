"""
While Loop Parser - 使用正确的 AST 遍历

提取 while 和 do-while 循环：
- WhileLoop
- DoWhileLoop

注意：此文件不包含任何正则表达式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang
from pyslang import SyntaxKind


@dataclass
class WhileLoop:
    condition: str = ""
    body: str = ""


@dataclass
class DoWhileLoop:
    body: str = ""
    condition: str = ""


class WhileLoopExtractor:
    def __init__(self):
        self.while_loops: List[WhileLoop] = []
        self.do_while_loops: List[DoWhileLoop] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'WhileLoop':
                wl = WhileLoop()
                if hasattr(node, 'condition') and node.condition:
                    wl.condition = str(node.condition)
                if hasattr(node, 'body') and node.body:
                    wl.body = str(node.body)[:50]
                self.while_loops.append(wl)
            
            elif kind_name == 'DoWhileLoop':
                dw = DoWhileLoop()
                if hasattr(node, 'body') and node.body:
                    dw.body = str(node.body)[:50]
                if hasattr(node, 'condition') and node.condition:
                    dw.condition = str(node.condition)
                self.do_while_loops.append(dw)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> Dict:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return {
            'while_loops': [{'cond': w.condition[:30]} for w in self.while_loops],
            'do_while_loops': [{'cond': w.condition[:30]} for w in self.do_while_loops]
        }


def extract_while_loops(code: str) -> Dict:
    return WhileLoopExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
while (i < 10) begin
    i++;
end

do begin
    j++;
end while (j < 20);
'''
    result = extract_while_loops(test_code)
    print(f"While: {len(result['while_loops'])}, Do-while: {len(result['do_while_loops'])}")
