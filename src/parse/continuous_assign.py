"""
连续赋值 / 线网声明解析器

处理:
- assign lhs = rhs;
- wire/var [width] name = expr;
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import List
from dataclasses import dataclass, field
import pyslang
from pyslang import SyntaxKind


@dataclass
class ContinuousAssign:
    lhs: str = ""
    rhs: str = ""


class AssignExtractor:
    def __init__(self, parser=None):
        self.parser = parser
        self.assigns = []
        if parser:
            self._extract_all()
    
    def _extract_all(self):
        for key, tree in getattr(self.parser, 'trees', {}).items():
            if tree and hasattr(tree, 'root') and tree.root:
                self._extract_from_tree(tree)
    
    def _extract_from_tree(self, tree):
        # 支持 SyntaxTree 或 CompilationUnitSyntax
        root = tree.root if hasattr(tree, 'root') else tree
        
        def collect(node):
            kn = node.kind.name
            
            if kn == 'ContinuousAssign':
                self._extract_continuous_assign(node)
            elif kn == 'NetDeclaration' or kn == 'VariableDeclaration':
                self._extract_decl_assign(node)
            
            return pyslang.VisitAction.Advance
        
        (tree.root if hasattr(tree, "root") else tree).visit(collect)
    
    def _extract_continuous_assign(self, node):
        full = str(node).strip()
        if 'assign' in full:
            import re
            match = re.search(r'assign\s+(.+?)\s*=\s*(.+?)\s*;', full)
            if match:
                lhs = match.group(1).strip()
                rhs = match.group(2).strip()
                self.assigns.append(ContinuousAssign(lhs=lhs, rhs=rhs))
    
    def _extract_decl_assign(self, node):
        """处理 wire/var 初始化"""
        full = str(node).strip()
        
        # 移除类型前缀
        import re
        # wire [7:0] a = b;
        match = re.search(r'(?:wire|var|logic|reg)\s*(?:\[[^\]]+\])?\s*(\w+)\s*=\s*([^;]+)', full)
        if match:
            lhs = match.group(1).strip()
            rhs = match.group(2).strip()
            self.assigns.append(ContinuousAssign(lhs=lhs, rhs=rhs))
    
    def get_assigns(self):
        return self.assigns


def extract_assigns(code):
    tree = pyslang.SyntaxTree.fromText(code)
    extractor = AssignExtractor(None)
    extractor._extract_from_tree(tree)
    return extractor.assigns


if __name__ == "__main__":
    test_code = '''module m;
    logic [7:0] a, b, c, d;
    assign a = b & c;
    wire [7:0] d = a;
    wire e = 1'b0;
endmodule'''

    result = extract_assigns(test_code)
    print("=== 连续赋值/wire 测试 ===")
    print(f"Found {len(result)} assigns")
    for a in result:
        print(f"  {a.lhs} = {a.rhs}")
