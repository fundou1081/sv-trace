"""
Type Parser - 使用 pyslang AST

支持:
- Array/Multi-dimensional arrays
- String types
- Dynamic types (queue, mailbox, semaphotre)
- User-defined types
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Optional
import pyslang
from pyslang import SyntaxKind


@dataclass
class ArrayType:
    """数组类型"""
    base_type: str = ""
    dimensions: List[str] = field(default_factory=list)
    is_dynamic: bool = False
    dynamic_kind: str = ""  # queue, mailbox, semaphore


@dataclass
class TypeDef:
    """类型定义 (typedef)"""
    name: str = ""
    base_type: str = ""
    kind: str = ""  # struct, union, enum, class


class TypeParser:
    def __init__(self, parser=None):
        self.parser = parser
        self.arrays = []
        self.type_defs = []
        
        if parser:
            self._extract_all()
    
    def _extract_all(self):
        for key, tree in getattr(self.parser, 'trees', {}).items():
            root = tree.root if hasattr(tree, 'root') else tree
            self._extract_from_tree(root)
    
    def _extract_from_tree(self, root):
        def collect(node):
            kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            
            # 数组类型
            if kind_name == 'VariableDimensionList' or 'QueueDimension' in kind_name:
                self._extract_array(node)
            
            # typedef
            elif kind_name == 'TypeDeclaration':
                self._extract_typedef(node)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _extract_array(self, node):
        arr = ArrayType()
        node_str = str(node)
        
        # 判断动态类型
        if 'queue' in node_str:
            arr.is_dynamic = True
            arr.dynamic_kind = 'queue'
        elif 'mailbox' in node_str:
            arr.is_dynamic = True
            arr.dynamic_kind = 'mailbox'
        elif 'semaphore' in node_str:
            arr.is_dynamic = True
            arr.dynamic_kind = 'semaphore'
        
        # 提取维度
        if hasattr(node, 'dimensions') and node.dimensions:
            for dim in node.dimensions:
                if dim:
                    arr.dimensions.append(str(dim))
        elif hasattr(node, 'selector') and node.selector:
            arr.dimensions.append(str(node.selector))
        
        self.arrays.append(arr)
    
    def _extract_typedef(self, node):
        td = TypeDef()
        
        # 名称
        if hasattr(node, 'name') and node.name:
            td.name = str(node.name)
        
        # 类型种类
        node_str = str(node)
        if 'struct' in node_str:
            td.kind = 'struct'
        elif 'union' in node_str:
            td.kind = 'union'
        elif 'enum' in node_str:
            td.kind = 'enum'
        elif 'class' in node_str:
            td.kind = 'class'
        
        # 基类型
        if hasattr(node, 'type') and node.type:
            td.base_type = str(node.type)
        
        self.type_defs.append(td)
    
    def get_arrays(self):
        return self.arrays
    
    def get_type_defs(self):
        return self.type_defs


def extract_types(code):
    tree = pyslang.SyntaxTree.fromText(code)
    extractor = TypeParser(None)
    extractor._extract_from_tree(tree)
    return extractor


if __name__ == "__main__":
    test_code = '''
module test;
    bit [7:0] arr [10];
    int queue [$];
    mailbox #(byte) mb;
    string str;
    
    typedef struct {
        bit [7:0] addr;
        bit [31:0] data;
    } packet_t;
    
    typedef enum {IDLE, RUN, DONE} state_t;
endmodule
'''
    
    result = extract_types(test_code)
    print("=== Type Extraction ===")
    print(f"arrays: {len(result.arrays)}")
    for arr in result.arrays[:5]:
        print(f"  {arr.dimensions}")
    print(f"typedefs: {len(result.type_defs)}")
    for td in result.type_defs:
        print(f"  {td.name} ({td.kind})")
