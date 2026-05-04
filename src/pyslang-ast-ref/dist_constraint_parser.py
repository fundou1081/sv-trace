"""
Dist Constraint Parser - 使用正确的 AST 遍历

注意：此文件不包含任何正则表达式，所有解析使用直接的 AST 属性访问
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import pyslang
from pyslang import SyntaxKind


@dataclass
class DistVariable:
    """dist 变量信息"""
    name: str = ""
    weight: str = ""  # := 或 :/ 加值


@dataclass
class DistConstraint:
    """dist 约束信息"""
    name: str = ""
    expression: str = ""
    variables: List[DistVariable] = field(default_factory=list)
    is_soft: bool = False


class DistConstraintExtractor:
    """从 SystemVerilog 代码中提取 dist 约束 - 使用 AST 遍历"""
    
    def __init__(self):
        self.constraints: List[DistConstraint] = []
    
    def _extract_from_tree(self, root):
        """使用 AST 遍历提取约束"""
        self.constraints = []
        
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            # 查找 Distribution constraint（DistConstraintList 或带有 dist 的约束）
            if kind_name == 'DistConstraintList' or self._is_dist_constraint(node):
                constraint = self._extract_dist(node)
                if constraint:
                    self.constraints.append(constraint)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
        return self.constraints
    
    def _is_dist_constraint(self, node) -> bool:
        """检查是否是 dist 约束"""
        # 检查节点字符串表示中是否包含 dist
        # 但这是最后的备选方案，最好用属性检查
        try:
            if hasattr(node, 'keyword') and node.keyword:
                if 'dist' in str(node.keyword).lower():
                    return True
        except:
            pass
        return False
    
    def _extract_dist(self, node) -> Optional[DistConstraint]:
        """提取 dist 约束 - 使用 AST 属性"""
        constraint = DistConstraint()
        
        # 约束名
        if hasattr(node, 'name') and node.name:
            constraint.name = str(node.name)
        
        # 是否为 soft 约束
        if hasattr(node, 'keyword') and node.keyword:
            if 'soft' in str(node.keyword).lower():
                constraint.is_soft = True
        
        # 提取 dist 变量 - 通过 AST 遍历而不是字符串
        for child in node:
            if not child:
                continue
            
            try:
                child_kind = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            except:
                continue
            
            # DistItem - 每个 dist 项
            if child_kind in ['DistItem', 'DistItemBase']:
                var = self._extract_dist_item(child)
                if var:
                    constraint.variables.append(var)
        
        # 如果没有提取到变量，尝试从 expression 提取
        if not constraint.variables and hasattr(node, 'distribution') and node.distribution:
            constraint.expression = str(node.distribution)
        
        return constraint if constraint.variables or constraint.expression else None
    
    def _extract_dist_item(self, node) -> Optional[DistVariable]:
        """提取单个 dist 项 - 使用 AST 属性"""
        var = DistVariable()
        
        # 变量名 - 直接从 AST 节点获取
        if hasattr(node, 'name') and node.name:
            var.name = str(node.name)
        elif hasattr(node, 'variable') and node.variable:
            var.name = str(node.variable)
        elif hasattr(node, 'identifier') and node.identifier:
            var.name = str(node.identifier)
        
        # 权重 - 从 AST 属性获取
        if hasattr(node, 'weight'):
            weight = node.weight
            if weight:
                weight_str = str(weight)
                if ':=' in weight_str or ':/' in weight_str:
                    var.weight = weight_str
        
        return var if var.name else None
    
    def extract_from_text(self, code: str, source: str = "<text>"):
        """从文本提取"""
        tree = pyslang.SyntaxTree.fromText(code, source)
        return self._extract_from_tree(tree.root)
    
    def get_constraints(self) -> List[DistConstraint]:
        return self.constraints


# ============================================================================
# 便捷函数
# ============================================================================

def extract_dist_constraints(code: str) -> List[Dict]:
    """从代码提取 dist 约束"""
    extractor = DistConstraintExtractor()
    constraints = extractor.extract_from_text(code)
    
    return [
        {
            'name': c.name,
            'variables': [
                {'name': v.name, 'weight': v.weight}
                for v in c.variables
            ],
            'is_soft': c.is_soft
        }
        for c in constraints
    ]


if __name__ == "__main__":
    test_code = '''
class packet;
    rand int addr;
    
    constraint addr_dist {
        addr dist {0 := 1, 1 := 2, 2:/ 5, [3:7] :/ 2};
    }
    
    soft constraint soft_c {
        data dist {1 := 10};
    }
endclass
'''
    
    print("=== Dist Constraints ===\n")
    
    result = extract_dist_constraints(test_code)
    print(f"Found {len(result)} dist constraints:")
    for c in result:
        print(f"  {c['name']}: {len(c['variables'])} variables, soft={c['is_soft']}")
        for v in c['variables']:
            print(f"    {v['name']}: {v['weight']}")
