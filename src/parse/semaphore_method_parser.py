"""
Semaphore Method Parser - 使用正确的 AST 遍历

提取信号量方法调用：
- get, put, try_get

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
class SemaphoreMethod:
    name: str = ""
    method: str = ""  # get, put, try_get
    value: str = ""


class SemaphoreMethodExtractor:
    def __init__(self):
        self.methods: List[SemaphoreMethod] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'SemaphoreMethodCall':
                sm = SemaphoreMethod()
                if hasattr(node, 'name') and node.name:
                    sm.name = str(node.name)
                if hasattr(node, 'method') and node.method:
                    sm.method = str(node.method)
                if hasattr(node, 'value') and node.value:
                    sm.value = str(node.value)
                self.methods.append(sm)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': m.name, 'method': m.method, 'value': m.value} for m in self.methods]


def extract_semaphore_methods(code: str) -> List[Dict]:
    return SemaphoreMethodExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
semaphore sm;
initial begin
    sm.get(1);
    sm.put(1);
    sm.try_get(1);
end
'''
    result = extract_semaphore_methods(test_code)
    print(f"Semaphore methods: {len(result)}")
