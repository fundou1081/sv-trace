"""
Enum Declaration Parser - 使用正确的 AST 遍历

提取 enum 类型声明：
- enum 名称
- 底层类型 (int, byte, bit, logic)
- 枚举值列表

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
class EnumValue:
    """枚举值"""
    name: str = ""
    value: str = ""  # 可选的初始值


@dataclass
class EnumDeclaration:
    """枚举声明"""
    name: str = ""
    base_type: str = ""  # int, byte, bit, logic
    values: List[EnumValue] = field(default_factory=list)


class EnumDeclarationExtractor:
    """提取 enum 声明"""
    
    def __init__(self):
        self.enums: List[EnumDeclaration] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            # EnumDeclaration
            if kind_name == 'EnumDeclaration':
                e = self._extract_enum(node)
                if e:
                    self.enums.append(e)
            
            # 也处理顶层变量声明中的枚举类型
            elif kind_name == 'DataDeclaration':
                self._check_enum_in_data_decl(node)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _extract_enum(self, node) -> Optional[EnumDeclaration]:
        e = EnumDeclaration()
        
        # 名称
        if hasattr(node, 'name') and node.name:
            e.name = str(node.name)
        
        # 底层类型
        if hasattr(node, 'keyword') and node.keyword:
            e.base_type = str(node.keyword)
        
        # 枚举值
        if hasattr(node, 'values') and node.values:
            for v in node.values:
                ev = EnumValue()
                if hasattr(v, 'name') and v.name:
                    ev.name = str(v.name)
                if hasattr(v, 'value') and v.value:
                    ev.value = str(v.value)
                e.values.append(ev)
        
        return e if e.name or e.values else None
    
    def _check_enum_in_data_decl(self, node):
        """检查 DataDeclaration 中的枚举类型"""
        for child in node:
            if not child:
                continue
            try:
                child_kind = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            except:
                continue
            
            if child_kind == 'EnumDeclaration':
                e = self._extract_enum(child)
                if e:
                    self.enums.append(e)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        
        return [
            {
                'name': e.name,
                'base_type': e.base_type,
                'values': [v.name for v in e.values],
                'count': len(e.values)
            }
            for e in self.enums
        ]
    
    def extract_from_file(self, filepath: str) -> List[Dict]:
        with open(filepath, 'r') as f:
            code = f.read()
        return self.extract_from_text(code, filepath)


def extract_enums(code: str) -> List[Dict]:
    """便捷函数"""
    return EnumDeclarationExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
module test;
    typedef enum {IDLE, RUN, DONE} state_t;
    typedef enum bit [3:0] {A=0, B=1, C=2, D=4} cmd_t;
    
    enum {START, STOP, WAIT} status;
    enum logic [1:0] {RED, GREEN, BLUE} color;
endmodule
'''
    
    print("=== Enum Declaration Extraction ===\n")
    result = extract_enums(test_code)
    for item in result:
        print(f"Enum: {item['name']} (base: {item['base_type']}, {item['count']} values)")
        print(f"  Values: {item['values']}")
    print(f"\nTotal: {len(result)} enums")
