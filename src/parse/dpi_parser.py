"""
DPI 解析器 - 使用 pyslang AST

支持:
- DPI import
- DPI export
- C 函数映射
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Optional
import pyslang
from pyslang import SyntaxKind


@dataclass
class DPIFunction:
    """DPI 函数"""
    name: str = ""
    return_type: str = ""
    arguments: List[str] = field(default_factory=list)
    kind: str = ""  # import or export
    c_name: str = ""


class DPIExtractor:
    def __init__(self, parser=None):
        self.parser = parser
        self.functions = []
        
        if parser:
            self._extract_all()
    
    def _extract_all(self):
        for key, tree in getattr(self.parser, 'trees', {}).items():
            root = tree.root if hasattr(tree, 'root') else tree
            self._extract_from_tree(root)
    
    def _extract_from_tree(self, root):
        def collect(node):
            kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            
            if kind_name == 'DPIImport':
                self._extract_dpi(node, 'import')
            elif kind_name == 'DPIExport':
                self._extract_dpi(node, 'export')
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _extract_dpi(self, node, kind):
        dpi = DPIFunction()
        dpi.kind = kind
        
        # 名称
        if hasattr(node, 'name') and node.name:
            dpi.name = str(node.name)
        
        # 返回类型
        if hasattr(node, 'returnType') and node.returnType:
            dpi.return_type = str(node.returnType)
        
        # C 名称 (从 stringLiteral 获取)
        if hasattr(node, 'cName') and node.cName:
            dpi.c_name = str(node.cName)
        else:
            # 尝试从 stringLiteral 获取
            node_str = str(node)
            import re
            match = re.search(r'\"([^\"]+)\"', node_str)
            if match:
                dpi.c_name = match.group(1)
        
        # 参数
        if hasattr(node, 'ports') and node.ports:
            for port in node.ports:
                if port:
                    dpi.arguments.append(str(port))
        
        self.functions.append(dpi)
    
    def get_functions(self):
        return self.functions


def extract_dpi(code):
    tree = pyslang.SyntaxTree.fromText(code)
    extractor = DPIExtractor(None)
    extractor._extract_from_tree(tree)
    return extractor.functions


if __name__ == "__main__":
    test_code = '''
module test;
    import "DPI" function void put_value(input int data);
    import "DPI" function int get_value();
    export "DPI" function my_c_func;
endmodule
'''
    
    result = extract_dpi(test_code)
    print("=== DPI Extraction ===")
    for dpi in result:
        print(f"{dpi.kind}: {dpi.name} -> {dpi.c_name}")
