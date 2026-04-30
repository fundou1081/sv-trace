"""
Constraint 解析器 - 使用 pyslang AST
"""
import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import List
from dataclasses import dataclass, field
import pyslang
from pyslang import SyntaxKind


@dataclass
class ConstraintInfo:
    name: str = ""
    class_name: str = ""
    expr: str = ""


class ConstraintExtractor:
    def __init__(self, parser=None):
        self.parser = parser
        self.constraints = []
        
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
            if node.kind == SyntaxKind.ConstraintDeclaration:
                self._extract_constraint(node)
            return pyslang.VisitAction.Advance
        
        (tree.root if hasattr(tree, "root") else tree).visit(collect)
    
    def _extract_constraint(self, node):
        # name
        name = str(node.name) if node.name else ""
        
        # expr - 从 block
        expr = ""
        if node.block:
            expr = str(node.block).strip()
        
        # 备选: 从字符串
        if not expr:
            str_repr = str(node).strip()
            # constraint NAME { EXPR }
            match = re.search(r'constraint\s+\w+\s*\{([^}]+)\}', str_repr)
            if match:
                expr = match.group(1).strip()
            else:
                # constraint NAME EXPR;
                match = re.search(r'constraint\s+\w+\s+([^;]+)', str_repr)
                if match:
                    expr = match.group(1).strip()
        
        if name:
            self.constraints.append(ConstraintInfo(name=name, expr=expr))
    
    def get_constraints(self):
        return self.constraints
    
    def extract_from_text(self, code: str) -> List[ConstraintInfo]:
        """从文本提取约束 (备用方法)"""
        # class 块
        class_pattern = r'class\s+(\w+)[^{]*\{([\s\S]*?)\s*endclass'
        
        for class_m in re.finditer(class_pattern, code, re.DOTALL):
            class_name = class_m.group(1).strip()
            class_body = class_m.group(2)
            
            # constraint { expr }
            for m in re.finditer(r'constraint\s+(\w+)\s*\{([^}]+)\}', class_body):
                self.constraints.append(ConstraintInfo(
                    name=m.group(1).strip(),
                    class_name=class_name,
                    expr=m.group(2).strip()
                ))
            
            # constraint expr;
            for m in re.finditer(r'constraint\s+(\w+)\s+([^;]+);', class_body):
                self.constraints.append(ConstraintInfo(
                    name=m.group(1).strip(),
                    class_name=class_name,
                    expr=m.group(2).strip()
                ))
        
        return self.constraints


def extract_constraints(code):
    tree = pyslang.SyntaxTree.fromText(code)
    extractor = ConstraintExtractor(None)
    extractor._extract_from_tree(tree)
    return extractor.constraints


if __name__ == "__main__":
    test_code = '''class packet;
    rand bit [7:0] data;
    
    constraint c1 { data < 256; }
    constraint c2 { data > 0; }
    constraint c3 { data dist {0:=1, [1:255]:=9}; }
endclass'''

    result = extract_constraints(test_code)
    print("=== Constraint ===")
    for c in result:
        print(f"  {c.name}: {c.expr[:30]}")
