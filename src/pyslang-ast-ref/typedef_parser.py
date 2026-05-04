"""
Typedef Parser - 使用正确的 AST 遍历

提取 typedef 声明：
- 结构体 typedef
- 枚举 typedef
- 联合体 typedef
- 其他类型别名

注意：此文件不包含任何正则表达式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict, Optional
import pyslang
from pyslang import SyntaxKind


@dataclass
class TypedefDecl:
    name: str = ""
    base_type: str = ""  # struct, enum, union, or other
    underlying_type: str = ""  # 实际类型


class TypedefExtractor:
    def __init__(self):
        self.typedefs: List[TypedefDecl] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'TypedefDeclaration':
                td = TypedefDecl()
                if hasattr(node, 'name') and node.name:
                    td.name = str(node.name)
                
                # 检查底层类型
                for child in node:
                    if not child:
                        continue
                    try:
                        child_kind = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
                    except:
                        continue
                    
                    if child_kind == 'StructUnion':
                        td.base_type = 'struct_union'
                        if hasattr(child, 'keyword') and child.keyword:
                            td.underlying_type = str(child.keyword).lower()
                    elif child_kind == 'EnumDeclaration':
                        td.base_type = 'enum'
                    elif child_kind == 'Identifier':
                        td.underlying_type = str(child)
                
                if td.name:
                    self.typedefs.append(td)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': td.name, 'base_type': td.base_type, 'underlying': td.underlying_type} for td in self.typedefs]


def extract_typedefs(code: str) -> List[Dict]:
    return TypedefExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
module test;
    typedef struct packed {
        logic [7:0] addr;
        logic [7:0] data;
    } my_struct_t;
    
    typedef enum {A, B, C} state_t;
    
    typedef union packed {
        logic [31:0] d32;
        logic [15:0] d16;
    } my_union_t;
endmodule
'''
    result = extract_typedefs(test_code)
    for item in result:
        print(f"Typedef: {item['name']} ({item['base_type']})")
