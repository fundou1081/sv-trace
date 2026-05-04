"""
This/Super Handle Parser - 使用正确的 AST 遍历

提取 this/super 引用：
- ThisHandle
- SuperHandle

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
class ThisSuperHandle:
    handle_type: str = ""  # this or super


class ThisSuperExtractor:
    def __init__(self):
        self.handles: List[ThisSuperHandle] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ThisHandle':
                h = ThisSuperHandle()
                h.handle_type = 'this'
                self.handles.append(h)
            
            elif kind_name == 'SuperHandle':
                h = ThisSuperHandle()
                h.handle_type = 'super'
                self.handles.append(h)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> Dict:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        
        this_count = sum(1 for h in self.handles if h.handle_type == 'this')
        super_count = sum(1 for h in self.handles if h.handle_type == 'super')
        
        return {'this': this_count, 'super': super_count}


def extract_this_super(code: str) -> Dict:
    return ThisSuperExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
class MyClass;
    function new();
        super.new();
        this.data = 1;
    endfunction
endclass
'''
    result = extract_this_super(test_code)
    print(f"this: {result['this']}, super: {result['super']}")
