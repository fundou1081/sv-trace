"""
Enum Type Parser - 使用正确的 AST 遍历

提取枚举类型：
- EnumType
- EnumName
- EnumLiteral

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class EnumTypeInfo:
    base_type: str = ""
    names: List[str] = None
    
    def __post_init__(self):
        if self.names is None:
            self.names = []


class EnumTypeExtractor:
    def __init__(self):
        self.enums: List[EnumTypeInfo] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'EnumType':
                et = EnumTypeInfo()
                if hasattr(node, 'baseType') and node.baseType:
                    et.base_type = str(node.baseType)[:20]
                
                names = []
                def get_enum_names(n):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if kn in ['EnumName', 'EnumLiteral']:
                        names.append(str(n))
                    return pyslang.VisitAction.Advance
                
                node.visit(get_enum_names)
                et.names = names[:10]
                self.enums.append(et)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'base': e.base_type[:20], 'names': e.names[:5]} for e in self.enums]


def extract_enum_types(code: str) -> List[Dict]:
    return EnumTypeExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
typedef enum { RED, GREEN, BLUE } color_e;
'''
    result = extract_enum_types(test_code)
    print(f"Enum types: {len(result)}")
