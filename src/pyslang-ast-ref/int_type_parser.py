"""
Int Type Parser - 使用正确的 AST 遍历

提取整数类型：
- IntType

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class IntType:
    keyword: str = "int"
    signedness: str = ""


class IntTypeExtractor:
    def __init__(self):
        self.types: List[IntType] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'IntType':
                it = IntType()
                if hasattr(node, 'keyword') and node.keyword:
                    it.keyword = str(node.keyword).lower()
                if hasattr(node, 'signed') and node.signed:
                    it.signedness = 'signed'
                elif hasattr(node, 'unsigned') and node.unsigned:
                    it.signedness = 'unsigned'
                self.types.append(it)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'keyword': t.keyword, 'signedness': t.signedness} for t in self.types]


def extract_int_types(code: str) -> List[Dict]:
    return IntTypeExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
int a;
integer b;
end
'''
    result = extract_int_types(test_code)
    print(f"Int types: {len(result)}")
