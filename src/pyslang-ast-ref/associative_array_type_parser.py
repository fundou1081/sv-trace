"""
Associative Array Type Parser - 使用正确的 AST 遍历

提取关联数组类型：
- AssociativeArrayType

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class AssociativeArrayType:
    data_type: str = ""
    index_type: str = ""


class AssociativeArrayTypeExtractor:
    def __init__(self):
        self.types: List[AssociativeArrayType] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'AssociativeArrayType':
                aat = AssociativeArrayType()
                if hasattr(node, 'dataType') and node.dataType:
                    aat.data_type = str(node.dataType)[:20]
                if hasattr(node, 'indexType') and node.indexType:
                    aat.index_type = str(node.indexType)[:20]
                self.types.append(aat)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'data': a.data_type[:20], 'index': a.index_type[:20]} for a in self.types]


def extract_assoc_array_types(code: str) -> List[Dict]:
    return AssociativeArrayTypeExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
int associative_array[string];
'''
    result = extract_assoc_array_types(test_code)
    print(f"Associative array types: {len(result)}")
