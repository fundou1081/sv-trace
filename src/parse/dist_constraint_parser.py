"""
Dist Constraint Parser - 使用 pyslang AST

支持:
- dist constraint (:= :/权重)
- SolveBeforeConstraint
- SolveAfterConstraint
- Unique constraint
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List
import pyslang
from pyslang import SyntaxKind


@dataclass
class DistItem:
    """dist item"""
    value_range: str = ""
    weight: int = 0
    is_soft: bool = False


@dataclass
class DistConstraint:
    """dist constraint"""
    variable: str = ""
    items: List[DistItem] = field(default_factory=list)


@dataclass
class UniqueConstraint:
    """unique constraint"""
    variables: List[str] = field(default_factory=list)


@dataclass
class SoftConstraint:
    """soft constraint"""
    expression: str = ""
    is_soft: bool = True


class DistConstraintParser:
    def __init__(self, parser=None):
        self.parser = parser
        self.dist_constraints = []
        self.unique_constraints = []
        self.soft_constraints = []
        
        if parser:
            self._extract_all()
    
    def _extract_all(self):
        for key, tree in getattr(self.parser, 'trees', {}).items():
            root = tree.root if hasattr(tree, 'root') else tree
            self._extract_from_tree(root)
    
    def _extract_from_tree(self, root):
        def collect(node):
            kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            
            if kind_name == 'DistConstraint':
                self._extract_dist(node)
            elif kind_name in ['UniqueConstraint', 'UniqueSimpleconstraint']:
                self._extract_unique(node)
            elif kind_name == 'ElseConstraintClause':
                self._extract_soft(node)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _extract_dist(self, node):
        dist = DistConstraint()
        node_str = str(node)
        
        # 提取 dist 内容
        import re
        # 格式: value := weight 或 value :/ weight
        for match in re.finditer(r'(\S+)\s*(:[=:])(\d+)', node_str):
            item = DistItem()
            item.value_range = match.group(1)
            item.weight = int(match.group(3))
            if match.group(2) == '=:':
                item.is_soft = True
            dist.items.append(item)
        
        if dist.items:
            self.dist_constraints.append(dist)
    
    def _extract_unique(self, node):
        unique = UniqueConstraint()
        
        # 提取变量
        if hasattr(node, 'expressions'):
            for expr in node.expressions:
                if expr:
                    unique.variables.append(str(expr))
        elif hasattr(node, 'identifier'):
            unique.variables.append(str(node.identifier))
        
        if unique.variables:
            self.unique_constraints.append(unique)
    
    def _extract_soft(self, node):
        # soft constraint
        soft = SoftConstraint()
        soft.expression = str(node)
        self.soft_constraints.append(soft)
    
    def get_dist_constraints(self):
        return self.dist_constraints
    
    def get_unique_constraints(self):
        return self.unique_constraints
    
    def get_soft_constraints(self):
        return self.soft_constraints


def extract_dist_constraints(code):
    tree = pyslang.SyntaxTree.fromText(code)
    parser = DistConstraintParser(None)
    parser._extract_from_tree(tree)
    return parser


if __name__ == "__main__":
    test_code = '''
class test;
    rand bit [7:0] addr;
    rand bit [2:0] burst;
    
    constraint dist_c {
        addr dist {[0:10] := 1, [11:50] :/ 2, [51:100] := 0};
    }
    
    constraint unique_c {
        unique {addr, burst};
    }
    
    constraint soft_c {
        soft addr > 0;
    }
endclass
'''
    
    result = extract_dist_constraints(test_code)
    print("=== Dist Constraints ===")
    print(f"dist: {len(result.dist_constraints)}")
    print(f"unique: {len(result.unique_constraints)}")
    print(f"soft: {len(result.soft_constraints)}")
