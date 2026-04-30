"""
Class 解析器 - 使用 pyslang AST

class 成员、方法、约束提取
"""
from dataclasses import dataclass
from typing import List, Dict
import pyslang
from pyslang import SyntaxKind


@dataclass
class ClassMethod:
    name: str = ""
    kind: str = "function"
    return_type: str = ""
    
    def to_dict(self):
        return {"name": self.name, "kind": self.kind, "return_type": self.return_type}


@dataclass  
class ClassMember:
    name: str = ""
    data_type: str = "logic"
    width: int = 1
    rand_mode: str = ""
    
    def to_dict(self):
        return {"name": self.name, "type": self.data_type, "width": self.width, "rand": self.rand_mode}


@dataclass
class ClassConstraint:
    name: str = ""
    expr: str = ""
    
    def to_dict(self):
        return {"name": self.name, "expr": self.expr}


class ClassExtractor:
    def __init__(self, parser=None):
        self.parser = parser
        self.classes: List[Dict] = []
        if parser:
            self._extract_all()
    
    def _extract_all(self):
        for key, tree in getattr(self.parser, 'trees', {}).items():
            if tree and hasattr(tree, 'root') and tree.root:
                self._extract_from_tree(tree.root)
    
    def extract_from_tree(self, root) -> List[Dict]:
        """从 tree root 提取"""
        results = []
        
        def collect(node):
            if node.kind == SyntaxKind.ClassDeclaration:
                class_info = self._extract_class(node)
                if class_info:
                    results.append(class_info)
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
        self.classes = results
        return results
    
    def _extract_class(self, node):
        # name
        name = str(node.name) if hasattr(node, 'name') and node.name else ""
        if not name:
            return None
        
        # extends
        extends = ""
        if hasattr(node, 'extendsClause') and node.extendsClause:
            extends = str(node.extendsClause).strip()
        
        info = {
            'name': name,
            'extends': extends,
            'members': [],
            'methods': [],
            'constraints': []
        }
        
        # items - 类成员
        if hasattr(node, 'items') and node.items:
            for item in node.items:
                if not item:
                    continue
                
                kind = item.kind.name if hasattr(item.kind, 'name') else str(item.kind)
                
                # ClassPropertyDeclaration
                if kind == 'ClassPropertyDeclaration':
                    member = self._extract_member(item)
                    if member:
                        info['members'].append(member)
                
                # ClassMethodDeclaration
                elif kind == 'ClassMethodDeclaration':
                    method = self._extract_method(item)
                    if method:
                        info['methods'].append(method)
                
                # ConstraintDeclaration
                elif kind == 'ConstraintDeclaration':
                    constr = self._extract_constraint(item)
                    if constr:
                        info['constraints'].append(constr)
        
        return info
    
    def _extract_member(self, node):
        """提取类成员"""
        member = ClassMember()
        
        # 获取声明字符串
        decl = str(node).strip()
        
        # rand 模式
        if hasattr(node, 'qualifiers') and node.qualifiers:
            member.rand_mode = str(node.qualifiers).strip()
        
        # 类型和名称
        import re
        # rand bit [7:0] name;
        match = re.search(r'(rand|randc)?\s*(bit|logic|byte|int)\s*(?:\[(\d+):(\d+)\])?\s*(\w+)', decl)
        if match:
            if match.group(1):
                member.rand_mode = match.group(1)
            if match.group(2):
                member.data_type = match.group(2)
            if match.group(3) and match.group(4):
                member.width = (int(match.group(3)) + 1)
            if match.group(5):
                member.name = match.group(5)
        
        return member
    
    def _extract_method(self, node):
        """提取类方法"""
        method = ClassMethod()
        
        decl = str(node).strip()
        
        # function/task
        if 'task' in decl.split()[0]:
            method.kind = 'task'
        
        # 返回类型和名称
        import re
        match = re.search(r'(function|task)\s+(\w+(?:\s+\w+)*?)\s+(\w+)', decl)
        if match:
            method.kind = match.group(1)
            method.return_type = match.group(2)
            method.name = match.group(3)
        
        return method
    
    def _extract_constraint(self, node):
        """提取类约束"""
        constr = ClassConstraint()
        
        if hasattr(node, 'name') and node.name:
            constr.name = str(node.name).strip()
        
        # expr from block
        if hasattr(node, 'block') and node.block:
            constr.expr = str(node.block).strip()
        
        return constr
    
    def extract_from_text(self, code: str) -> List[Dict]:
        """从文本提取"""
        tree = pyslang.SyntaxTree.fromText(code)
        return self.extract_from_tree(tree.root)


# 别名
def get_classes(code):
    """便捷函数"""
    ce = ClassExtractor()
    return ce.extract_from_text(code)
