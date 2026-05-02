"""
Context Function Parser - 使用正确的 AST 遍历

提取上下文函数：
- ContextFunction

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
class ContextFunction:
    name: str = ""
    return_type: str = ""


class ContextFunctionExtractor:
    def __init__(self):
        self.functions: List[ContextFunction] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ContextFunction':
                cf = ContextFunction()
                if hasattr(node, 'name') and node.name:
                    cf.name = str(node.name)
                if hasattr(node, 'returnType') and node.returnType:
                    cf.return_type = str(node.returnType)
                self.functions.append(cf)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': f.name, 'return_type': f.return_type} for f in self.functions]


def extract_context_functions(code: str) -> List[Dict]:
    return ContextFunctionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
import "context" function int get_current_task_id();
'''
    result = extract_context_functions(test_code)
    print(f"Context functions: {len(result)}")
