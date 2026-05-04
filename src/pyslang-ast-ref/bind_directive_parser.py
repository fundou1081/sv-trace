"""
Bind Directive Parser - 使用正确的 AST 遍历

提取 bind 指令：
- bind 绑定
- target scope
- instance list

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
class BindDirective:
    target: str = ""
    instance: str = ""
    module: str = ""


class BindDirectiveExtractor:
    def __init__(self):
        self.binds: List[BindDirective] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'BindDirective':
                bd = BindDirective()
                
                if hasattr(node, 'target') and node.target:
                    bd.target = str(node.target)
                if hasattr(node, 'instance') and node.instance:
                    bd.instance = str(node.instance)
                if hasattr(node, 'module') and node.module:
                    bd.module = str(node.module)
                
                self.binds.append(bd)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'target': b.target, 'instance': b.instance} for b in self.binds]


def extract_binds(code: str) -> List[Dict]:
    return BindDirectiveExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
bind uvm_scoreboard coverage_collector #(.WIDTH(8)) cov_inst;
'''
    result = extract_binds(test_code)
    print(f"Binds: {len(result)}")
