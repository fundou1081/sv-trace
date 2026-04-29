"""
Constraint 解析器 - 专注于constraint内容提取
"""
from dataclasses import dataclass
from typing import List
import re


@dataclass
class ConstraintInfo:
    """单个constraint信息"""
    name: str = ""
    class_name: str = ""
    expr: str = ""
    
    def to_dict(self):
        return {
            "name": self.name,
            "class": self.class_name,
            "expr": self.expr
        }


class ConstraintExtractor:
    """Constraint内容提取器"""
    
    def __init__(self, parser=None):
        self.parser = parser
        self.constraints: List[ConstraintInfo] = []
    
    def extract_from_text(self, code: str) -> List[ConstraintInfo]:
        """从源码文本提取constraint"""
        results = []
        
        # 找到所有class和其中的constraint
        class_pattern = r'class\s+(\w+)[^{]*\{([\s\S]*?)\s*endclass'
        
        for class_m in re.finditer(class_pattern, code, re.DOTALL):
            class_name = class_m.group(1).strip()
            class_body = class_m.group(2)
            
            # 提取constraint
            # constraint name { expr };
            constr_pattern = r'constraint\s+(\w+)\s*\{([^}]+)\}'
            for m in re.finditer(constr_pattern, class_body):
                name = m.group(1).strip()
                expr = m.group(2).strip()
                results.append(ConstraintInfo(
                    name=name,
                    class_name=class_name,
                    expr=expr
                ))
            
            # 提取单行constraint: constraint expr;
            simple_pattern = r'constraint\s+(\w+)\s+([^;{]+);'
            for m in re.finditer(simple_pattern, class_body):
                name = m.group(1).strip()
                expr = m.group(2).strip()
                results.append(ConstraintInfo(
                    name=name,
                    class_name=class_name,
                    expr=expr
                ))
        
        self.constraints = results
        return results
    
    def extract_constraints_only(self, code: str) -> List[dict]:
        """只提取constraint表达式，不关心class结构"""
        results = []
        
        # constraint name { expr };
        pattern = r'constraint\s+(\w+)\s*\{([^}]+)\}'
        for m in re.finditer(pattern, code):
            name = m.group(1).strip()
            expr = m.group(2).strip()
            results.append({"name": name, "expr": expr})
        
        return results
    
    def list_constraints(self) -> List[str]:
        """列出所有constraint名"""
        return [c.name for c in self.constraints]
    
    def get_constraint(self, name: str) -> ConstraintInfo:
        """获取指定constraint"""
        for c in self.constraints:
            if c.name == name:
                return c
        return None


__all__ = ['ConstraintExtractor', 'ConstraintInfo']


def extract_constraints_from_text(code: str) -> List[dict]:
    """从源码文本提取constraint (使用 pyslang)"""
    import pyslang
    from pyslang import SyntaxKind
    
    results = []
    
    try:
        tree = pyslang.SyntaxTree.fromText(code)
        
        def collector(node):
            if node.kind == SyntaxKind.ConstraintDeclaration:
                name = str(node.name).strip() if hasattr(node, 'name') else 'unknown'
                expr = str(node)
                # 清理 expr
                expr = expr.replace('\n', ' ').strip()[:80]
                results.append({
                    'name': name,
                    'class': '',
                    'expr': expr
                })
            return pyslang.VisitAction.Advance
        
        tree.root.visit(collector)
    
    except Exception as e:
        print(f"Constraint extract error: {e}")
    
    return results
