"""
Disable Iff Parser - 使用正确的 AST 遍历

提取 disable iff 语句：
- DisableIff

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class DisableIff:
    condition: str = ""


class DisableIffExtractor:
    def __init__(self):
        self.items: List[DisableIff] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['DisableIff', 'DisableIffConstruct']:
                di = DisableIff()
                if hasattr(node, 'condition') and node.condition:
                    di.condition = str(node.condition)[:40]
                elif hasattr(node, 'expr') and node.expr:
                    di.condition = str(node.expr)[:40]
                self.items.append(di)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'cond': i.condition[:40]} for i in self.items]


def extract_disable_iff(code: str) -> List[Dict]:
    return DisableIffExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
default disable iff (rst);
'''
    result = extract_disable_iff(test_code)
    print(f"Disable iff: {len(result)}")
