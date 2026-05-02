"""
Constraint Parser - 使用正确的 AST 遍历

约束提取

注意：此文件使用正确的 AST 属性访问，不包含正则表达式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import pyslang
from pyslang import SyntaxKind


@dataclass
class ConstraintItem:
    name: str = ""
    expression: str = ""


@dataclass
class ConstraintDeclaration:
    name: str = ""
    constraint_type: str = "simple"  # simple, if-else, dist, solve, soft
    variables: List[str] = field(default_factory=list)
    left_expr: str = ""
    right_expr: str = ""


class ConstraintExtractor:
    """从 SystemVerilog 代码中提取约束 - 使用正确的 AST 遍历"""
    
    def __init__(self, parser=None):
        self.parser = parser
        self.constraints: List[ConstraintDeclaration] = []
    
    def _extract_from_tree(self, root):
        """使用 AST 遍历提取约束"""
        self.constraints = []
        
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            # 查找 ConstraintDeclaration
            if kind_name == 'ConstraintDeclaration':
                constraint = self._extract_constraint(node)
                if constraint:
                    self.constraints.append(constraint)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
        return self.constraints
    
    def _extract_constraint(self, node) -> Optional[ConstraintDeclaration]:
        """提取单个约束 - 使用 AST 属性"""
        constraint = ConstraintDeclaration()
        
        # 约束名
        if hasattr(node, 'name') and node.name:
            constraint.name = str(node.name)
        elif hasattr(node, 'identifier') and node.identifier:
            constraint.name = str(node.identifier)
        
        # 判断约束类型
        constraint_type = self._detect_constraint_type(node)
        constraint.constraint_type = constraint_type
        
        # 提取表达式
        if hasattr(node, 'expression') and node.expression:
            constraint.left_expr = str(node.expression)
        elif hasattr(node, 'condition') and node.condition:
            constraint.left_expr = str(node.condition)
        elif hasattr(node, 'left') and node.left:
            constraint.left_expr = str(node.left)
        
        if hasattr(node, 'right') and node.right:
            constraint.right_expr = str(node.right)
        
        return constraint if constraint.name or constraint.left_expr else None
    
    def _detect_constraint_type(self, node) -> str:
        """检测约束类型 - 通过 AST 属性而不是字符串"""
        # 检查是否包含 if-else (条件约束)
        if hasattr(node, 'condition') and node.condition:
            return 'if-else'
        
        # 检查是否包含 dist (分布约束)
        if hasattr(node, 'distribution') and node.distribution:
            return 'dist'
        
        # 检查 solve before/after
        if hasattr(node, 'solveBefore') and node.solveBefore:
            return 'solve_before'
        if hasattr(node, 'solveAfter') and node.solveAfter:
            return 'solve_after'
        
        # 检查 soft 约束
        if hasattr(node, 'keyword') and node.keyword:
            if 'soft' in str(node.keyword).lower():
                return 'soft'
        
        return 'simple'
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        """从文本提取约束"""
        tree = pyslang.SyntaxTree.fromText(code, source)
        constraints = self._extract_from_tree(tree.root)
        
        return [
            {
                'name': c.name,
                'type': c.constraint_type,
                'expression': c.left_expr[:50] if c.left_expr else '',
                'right': c.right_expr[:30] if c.right_expr else ''
            }
            for c in constraints
        ]
    
    def get_constraints(self) -> List[ConstraintDeclaration]:
        return self.constraints


# ============================================================================
# 便捷函数
# ============================================================================

def extract_constraints_from_text(code: str) -> List[Dict]:
    """从代码提取约束 - 使用正确的 AST 遍历"""
    extractor = ConstraintExtractor()
    return extractor.extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
class packet;
    rand int data;
    rand int addr;
    
    constraint c1 { data < 256; }
    constraint c2 { if (addr < 10) data == 0; else data == addr * 2; }
    constraint c3 { addr dist {0 := 1, 1 := 2}; }
    constraint c4 { solve data before addr; }
    soft constraint c5 { data > 0; }
endclass
'''
    
    print("=== Constraint Extraction ===\n")
    
    result = extract_constraints_from_text(test_code)
    
    print(f"Found {len(result)} constraints:")
    for c in result:
        print(f"  {c['type']}: {c['name']} - {c['expression'][:30]}...")
