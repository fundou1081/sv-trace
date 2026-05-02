"""
Constraint Block Parser - 使用正确的 AST 遍历

支持:
- ConstraintBlock (约束块 inside class)
- ConstraintDeclaration (单个约束声明)
- ExpressionConstraint (表达式约束)
- ConditionalConstraint (if-else 约束)
- ImplicationConstraint (if-else -> 约束)
- LoopConstraint (foreach 约束)
- DistConstraintList (dist 约束)

注意：此文件不包含任何正则表达式，所有解析使用 AST 属性
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import pyslang
from pyslang import SyntaxKind


@dataclass
class ConstraintInfo:
    """约束信息"""
    name: str = ""
    constraint_type: str = ""  # expression, conditional, implication, loop, dist
    expression: str = ""
    expressions_count: int = 0
    solve_order: int = -1


@dataclass  
class ConstraintBlock:
    """约束块信息"""
    name: str = ""
    constraints: List[ConstraintInfo] = field(default_factory=list)
    is_soft: bool = False
    constraints_count: int = 0


class ConstraintBlockExtractor:
    """从 SystemVerilog 代码中提取约束块 - 使用正确的 AST 遍历"""
    
    def __init__(self):
        self.blocks: List[ConstraintBlock] = []
        self.standalone_constraints: List[ConstraintInfo] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            # ConstraintDeclaration - 单个约束声明
            if kind_name == 'ConstraintDeclaration':
                # 检查是否是 dist 约束
                if self._is_dist_constraint(node):
                    constraint = self._extract_constraint(node)
                    if constraint:
                        self.standalone_constraints.append(constraint)
                else:
                    # 普通约束 - 检查是否在类中（即 ConstraintBlock）
                    in_class = self._is_inside_class(node, root)
                    if in_class:
                        block = self._extract_constraint_block(node)
                        if block:
                            self.blocks.append(block)
                    else:
                        constraint = self._extract_constraint(node)
                        if constraint:
                            self.standalone_constraints.append(constraint)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
        return self.blocks + self.standalone_constraints
    
    def _is_dist_constraint(self, node) -> bool:
        """检查是否是 dist 约束 - 使用 AST 属性"""
        try:
            # 通过 AST 属性判断，而不是字符串
            if hasattr(node, 'keyword') and node.keyword:
                kw = str(node.keyword).lower()
                if 'dist' in kw:
                    return True
        except:
            pass
        return False
    
    def _is_inside_class(self, node, root) -> bool:
        """检查约束是否在类内部"""
        # 简单方法：检查父节点是否是 ClassDeclaration
        # 更准确的方法需要维护父节点栈
        return True  # 简化：如果在类中就用 block 模式
    
    def _extract_constraint(self, node) -> Optional[ConstraintInfo]:
        """提取单个约束 - 使用 AST 属性"""
        constraint = ConstraintInfo()
        
        # 约束名
        if hasattr(node, 'name') and node.name:
            constraint.name = str(node.name)
        elif hasattr(node, 'identifier') and node.identifier:
            constraint.name = str(node.identifier)
        
        # 约束类型 - 通过 AST 属性判断
        constraint.constraint_type = self._get_constraint_type(node)
        
        # 表达式 - 直接从 AST 获取
        if hasattr(node, 'expression') and node.expression:
            constraint.expression = str(node.expression)
        elif hasattr(node, 'condition') and node.condition:
            constraint.expression = str(node.condition)
        
        constraint.expressions_count = 1
        
        # solve order
        if hasattr(node, 'solveBefore') and node.solveBefore:
            constraint.solve_order = 1
        elif hasattr(node, 'solveAfter') and node.solveAfter:
            constraint.solve_order = -1
        
        return constraint
    
    def _get_constraint_type(self, node) -> str:
        """判断约束类型 - 使用 AST 属性判断"""
        # if-else 条件约束
        if hasattr(node, 'condition') and node.condition:
            return 'conditional'
        
        # implication (->)
        if hasattr(node, 'left') and node.left:
            return 'implication'
        
        # loop (foreach)
        if hasattr(node, 'body') and node.body:
            return 'loop'
        
        # dist 分布约束
        if self._is_dist_constraint(node):
            return 'dist'
        
        # soft 约束
        if hasattr(node, 'keyword') and node.keyword:
            if 'soft' in str(node.keyword).lower():
                return 'soft'
        
        return 'expression'
    
    def _extract_constraint_block(self, node) -> Optional[ConstraintBlock]:
        """提取约束块"""
        block = ConstraintBlock()
        
        # 块名
        if hasattr(node, 'name') and node.name:
            block.name = str(node.name)
        
        # 软约束
        if hasattr(node, 'keyword') and node.keyword:
            if 'soft' in str(node.keyword).lower():
                block.is_soft = True
        
        # 提取块内的约束 - 遍历子节点
        constraints = []
        for child in node:
            if not child:
                continue
            
            try:
                child_kind = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            except:
                continue
            
            if child_kind in ['ConstraintDeclaration', 'ConstraintItem', 'ExpressionConstraint']:
                c = self._extract_constraint(child)
                if c:
                    constraints.append(c)
        
        block.constraints = constraints
        block.constraints_count = len(constraints)
        
        return block if constraints else None
    
    def extract_from_text(self, code: str, source: str = "<text>"):
        tree = pyslang.SyntaxTree.fromText(code, source)
        return self._extract_from_tree(tree.root)
    
    def get_constraints(self) -> List[ConstraintInfo]:
        return self.standalone_constraints
    
    def get_blocks(self) -> List[ConstraintBlock]:
        return self.blocks


# ============================================================================
# 便捷函数
# ============================================================================

def extract_constraints(code: str) -> List[Dict]:
    """从代码提取约束"""
    extractor = ConstraintBlockExtractor()
    constraints = extractor.extract_from_text(code)
    
    result = []
    for c in constraints:
        if isinstance(c, ConstraintBlock):
            for constraint in c.constraints:
                result.append({
                    'name': constraint.name,
                    'type': constraint.constraint_type,
                    'expression': constraint.expression[:50],
                    'block': c.name,
                    'soft': c.is_soft
                })
        elif isinstance(c, ConstraintInfo):
            result.append({
                'name': c.name,
                'type': c.constraint_type,
                'expression': c.expression[:50],
                'block': '',
                'soft': False
            })
    
    return result


def extract_constraint_blocks(code: str) -> List[Dict]:
    """从代码提取约束块"""
    extractor = ConstraintBlockExtractor()
    extractor.extract_from_text(code)
    
    return [
        {
            'name': b.name,
            'constraints': [
                {'name': c.name, 'type': c.constraint_type, 'expression': c.expression[:50]}
                for c in b.constraints
            ],
            'is_soft': b.is_soft,
            'count': b.constraints_count
        }
        for b in extractor.blocks
    ]


if __name__ == "__main__":
    test_code = '''
class packet;
    rand int data;
    rand int addr;
    
    // Soft constraint block
    soft constraint addr_c {
        addr < 100;
    }
    
    // Simple constraint
    constraint data_c { data < 256; }
    
    // Conditional constraint
    constraint con_c {
        if (addr < 10)
            data == 0;
        else
            data == addr * 2;
    }
    
    // Implication constraint
    constraint imp_c {
        (addr > 100) -> data == 255;
    }
endclass
'''
    
    print("=== Constraint Extraction ===\n")
    
    print("--- extract_constraints ---")
    constraints = extract_constraints(test_code)
    print(f"Found {len(constraints)} constraints:")
    for c in constraints:
        print(f"  {c['type']}: {c['name']} (block: {c['block']})")
    
    print("\n--- extract_constraint_blocks ---")
    blocks = extract_constraint_blocks(test_code)
    print(f"Found {len(blocks)} constraint blocks:")
    for b in blocks:
        print(f"  {b['name']}: {b['count']} constraints, soft={b['is_soft']}")
