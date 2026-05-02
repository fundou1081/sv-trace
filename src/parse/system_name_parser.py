"""
System Name Parser - 使用正确的 AST 遍历

提取系统任务/函数调用：
- SystemName
- SystemIdentifier
- SystemMethodCall

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
class SystemCall:
    name: str = ""
    arguments: str = ""


class SystemNameExtractor:
    def __init__(self):
        self.system_calls: List[SystemCall] = []
        self.system_functions: List[SystemCall] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'SystemName':
                sc = SystemCall()
                sc.name = str(node)
                if hasattr(node, 'arguments') and node.arguments:
                    sc.arguments = str(node.arguments)
                self.system_calls.append(sc)
            
            elif kind_name == 'SystemIdentifier':
                sc = SystemCall()
                sc.name = str(node)
                self.system_calls.append(sc)
            
            elif kind_name == 'SystemMethodCall':
                sc = SystemCall()
                if hasattr(node, 'method') and node.method:
                    sc.name = str(node.method)
                if hasattr(node, 'arguments') and node.arguments:
                    sc.arguments = str(node.arguments)
                self.system_functions.append(sc)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> Dict:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return {
            'system_calls': [{'name': sc.name} for sc in self.system_calls[:20]],
            'system_functions': [{'name': sf.name, 'args': sf.arguments[:30]} for sf in self.system_functions[:20]]
        }


def extract_system_names(code: str) -> Dict:
    return SystemNameExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
initial begin
    $display("Hello");
    $finish;
    $time();
end
'''
    result = extract_system_names(test_code)
    print(f"System calls: {len(result['system_calls'])}")
