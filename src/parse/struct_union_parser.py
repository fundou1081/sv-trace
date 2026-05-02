"""
Struct/Union Parser - 使用正确的 AST 遍历

提取 struct 和 union 声明：
- StructDeclaration
- UnionDeclaration

注意：此文件不包含任何正则表达式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import pyslang
from pyslang import SyntaxKind


@dataclass
class StructUnionMember:
    name: str = ""
    type_name: str = ""


@dataclass
class StructUnionDecl:
    name: str = ""
    kind: str = ""  # struct or union
    is_packed: bool = False
    members: List[StructUnionMember] = field(default_factory=list)


class StructUnionExtractor:
    def __init__(self):
        self.decls: List[StructUnionDecl] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            # StructDeclaration, UnionDeclaration
            if kind_name == 'StructDeclaration':
                su = self._extract_decl(node, 'struct')
                if su:
                    self.decls.append(su)
            
            elif kind_name == 'UnionDeclaration':
                su = self._extract_decl(node, 'union')
                if su:
                    self.decls.append(su)
            
            # 也处理 StructUnion 类型
            elif kind_name == 'StructUnion':
                su = self._extract_struct_union(node)
                if su:
                    self.decls.append(su)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _extract_decl(self, node, kind) -> Optional[StructUnionDecl]:
        su = StructUnionDecl()
        su.kind = kind
        
        if hasattr(node, 'name') and node.name:
            su.name = str(node.name)
        
        if hasattr(node, 'packed') and node.packed:
            su.is_packed = bool(node.packed)
        
        # 成员
        for child in node:
            if not child:
                continue
            try:
                child_kind = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            except:
                continue
            
            if child_kind in ['DataDeclaration', 'StructMember']:
                m = StructUnionMember()
                if hasattr(child, 'name') and child.name:
                    m.name = str(child.name)
                su.members.append(m)
        
        return su if su.name or su.members else None
    
    def _extract_struct_union(self, node) -> Optional[StructUnionDecl]:
        su = StructUnionDecl()
        
        if hasattr(node, 'keyword') and node.keyword:
            kw = str(node.keyword).lower()
            su.kind = 'struct' if 'struct' in kw else 'union'
        
        if hasattr(node, 'name') and node.name:
            su.name = str(node.name)
        
        return su if su.name else None
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        
        return [
            {
                'name': su.name,
                'kind': su.kind,
                'packed': su.is_packed,
                'members': [{'name': m.name} for m in su.members]
            }
            for su in self.decls
        ]


def extract_struct_union(code: str) -> List[Dict]:
    return StructUnionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
module test;
    typedef struct packed { logic [7:0] addr; } s1_t;
    typedef union packed { logic [31:0] data; } u1_t;
endmodule
'''
    result = extract_struct_union(test_code)
    for item in result:
        print(f"{item['kind']}: {item['name']}")
