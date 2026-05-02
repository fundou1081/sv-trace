"""
Constraint Block Parser - 使用正确的 AST 遍历

提取 constraint block 及其内容：
- constraint 块声明
- 表达式约束 (in, inside, ==, !=, >, <, >=, <=)
- if-else 约束
- foreach 约束
- 约束优先级 (soft, unique, solve...before)

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
class ConstraintExpr:
    """约束表达式"""
    expr_type: str = ""  # binary, unary, range, dist, if_else, foreach
    operator: str = ""
    left: str = ""
    right: str = ""
    body: str = ""


@dataclass
class ConstraintBlock:
    """约束块"""
    name: str = ""
    class_name: str = ""
    is_soft: bool = False
    expressions: List[ConstraintExpr] = field(default_factory=list)


class ConstraintBlockExtractor:
    """提取 constraint block 声明和内容"""
    
    def __init__(self):
        self.constraints: List[ConstraintBlock] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            # ConstraintBlockDeclaration
            if kind_name == 'ConstraintBlockDeclaration':
                cb = self._extract_constraint_block(node)
                if cb:
                    self.constraints.append(cb)
            
            # ConstraintExpression 直接子节点
            elif kind_name == 'ConstraintExpression':
                ce = self._extract_constraint_expr(node)
                if ce:
                    pass  # 可以收集但通常属于某个 block
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _extract_constraint_block(self, node) -> Optional[ConstraintBlock]:
        cb = ConstraintBlock()
        
        # 获取名称
        if hasattr(node, 'name') and node.name:
            cb.name = str(node.name)
        
        # 检查 soft 属性
        if hasattr(node, 'keyword') and node.keyword:
            kw = str(node.keyword).lower()
            cb.is_soft = 'soft' in kw
        
        # 遍历子节点提取约束表达式
        for child in node:
            if not child:
                continue
            try:
                child_kind = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            except:
                continue
            
            # 约束表达式
            if child_kind in ['BinaryConstraint', 'UnaryConstraint', 'ImplicationConstraint',
                             'ConditionalConstraint', 'ForeachConstraint']:
                expr = self._extract_constraint_expr(child)
                if expr:
                    cb.expressions.append(expr)
            
            # 分布约束
            elif child_kind == 'DistConstraint':
                dist_expr = self._extract_dist_expr(child)
                if dist_expr:
                    ce = ConstraintExpr()
                    ce.expr_type = 'dist'
                    ce.body = dist_expr
                    cb.expressions.append(ce)
        
        return cb if cb.name else None
    
    def _extract_constraint_expr(self, node) -> Optional[ConstraintExpr]:
        ce = ConstraintExpr()
        
        try:
            kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
        except:
            return None
        
        ce.expr_type = kind_name
        
        # 二元约束 (a == b, a < b, etc.)
        if kind_name in ['BinaryConstraint', 'BinaryExpression']:
            if hasattr(node, 'left') and node.left:
                ce.left = str(node.left)
            if hasattr(node, 'operator') and node.operator:
                ce.operator = str(node.operator)
            if hasattr(node, 'right') and node.right:
                ce.right = str(node.right)
        
        # 隐含约束 (a -> b)
        elif kind_name == 'ImplicationConstraint':
            if hasattr(node, 'condition') and node.condition:
                ce.left = str(node.condition)
            if hasattr(node, 'expression') and node.expression:
                ce.right = str(node.expression)
            ce.operator = '->'
        
        # 条件约束 (if-else)
        elif kind_name in ['ConditionalConstraint', 'ConditionalExpression']:
            if hasattr(node, 'condition') and node.condition:
                ce.left = str(node.condition)
            if hasattr(node, 'trueExpression') and node.trueExpression:
                ce.body = str(node.trueExpression)
            ce.expr_type = 'if_else'
        
        # foreach 约束
        elif kind_name in ['ForeachConstraint', 'ForeachExpression']:
            if hasattr(node, 'loopVariables') and node.loopVariables:
                ce.body = str(node.loopVariables)
            ce.expr_type = 'foreach'
        
        # 范围约束 (inside {[1:10]})
        elif kind_name == 'RangeConstraint':
            if hasattr(node, 'expression') and node.expression:
                ce.body = str(node.expression)
            ce.expr_type = 'range'
        
        return ce if (ce.left or ce.right or ce.body) else None
    
    def _extract_dist_expr(self, node) -> str:
        """提取 dist 表达式"""
        if hasattr(node, 'expression') and node.expression:
            return str(node.expression)
        return ""
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        
        return [
            {
                'name': cb.name,
                'soft': cb.is_soft,
                'expressions': [
                    {
                        'type': e.expr_type,
                        'operator': e.operator,
                        'left': e.left[:30] if e.left else '',
                        'right': e.right[:30] if e.right else '',
                        'body': e.body[:30] if e.body else ''
                    }
                    for e in cb.expressions
                ]
            }
            for cb in self.constraints
        ]
    
    def extract_from_file(self, filepath: str) -> List[Dict]:
        with open(filepath, 'r') as f:
            code = f.read()
        return self.extract_from_text(code, filepath)


def extract_constraint_blocks(code: str) -> List[Dict]:
    """便捷函数"""
    return ConstraintBlockExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
class Packet;
    rand bit [7:0] addr;
    rand bit [7:0] data;
    
    constraint c1 {
        addr inside {[0:100]};
    }
    
    constraint c2 {
        soft data == 8'hFF;
        if (addr > 50) {
            data inside {[1:10]};
        }
    }
    
    constraint c3 {
        addr dist {0:/10, [1:100]:/90};
    }
endclass
'''
    
    print("=== Constraint Block Extraction ===\n")
    result = extract_constraint_blocks(test_code)
    for item in result:
        print(f"Constraint: {item['name']}")
        print(f"  Soft: {item['soft']}")
        print(f"  Expressions: {len(item['expressions'])}")
    print(f"\nTotal: {len(result)} constraints")
