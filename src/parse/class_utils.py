"""
Class 解析器 - 使用 pyslang AST

class 成员、方法、约束提取

增强版: 添加解析警告，显式打印不支持的语法结构
"""
from dataclasses import dataclass
from typing import List, Dict
import pyslang
from pyslang import SyntaxKind
import re

# 导入解析警告模块
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
try:
    from trace.parse_warn import (
        ParseWarningHandler,
        warn_unsupported,
        warn_error,
        WarningLevel
    )
except ImportError:
    class ParseWarningHandler:
        def __init__(self, verbose=True, component="ClassExtractor"):
            self.verbose = verbose
            self.component = component
        def warn_unsupported(self, node_kind, context="", suggestion="", component=None):
            if self.verbose:
                print(f"⚠️ [WARN][{component or self.component}] <{node_kind}> {suggestion} @ {context}")
        def warn_error(self, operation, exc, context="", component=None):
            if self.verbose:
                print(f"❌ [ERROR][{component or self.component}] {operation}: {exc} @ {context}")
        def get_report(self):
            return ""


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
    """
    Class 提取器
    
    增强版: 添加解析警告
    """
    
    # 不支持的语法类型
    UNSUPPORTED_TYPES = {
        'CovergroupDeclaration': 'covergroup不影响class提取',
        'PropertyDeclaration': 'property声明暂不支持',
        'SequenceDeclaration': 'sequence声明暂不支持',
        'InterfaceDeclaration': 'interface声明暂不支持',
        'PackageDeclaration': 'package声明暂不支持',
        'ProgramDeclaration': 'program块暂不支持',
        'ClockingBlock': 'clocking block暂不支持',
    }
    
    def __init__(self, parser=None, verbose: bool = True):
        self.parser = parser
        self.verbose = verbose
        # 创建警告处理器
        self.warn_handler = ParseWarningHandler(
            verbose=verbose,
            component="ClassExtractor"
        )
        self.classes: List[Dict] = []
        self._unsupported_encountered = set()
        if parser:
            self._extract_all()
    
    def _check_unsupported_node(self, node, source: str = ""):
        """检查不支持的节点类型"""
        kind_name = str(node.kind) if hasattr(node, 'kind') else type(node).__name__
        
        if kind_name in self.UNSUPPORTED_TYPES:
            if kind_name not in self._unsupported_encountered:
                self.warn_handler.warn_unsupported(
                    kind_name,
                    context=source,
                    suggestion=self.UNSUPPORTED_TYPES[kind_name],
                    component="ClassExtractor"
                )
                self._unsupported_encountered.add(kind_name)
    
    def _extract_all(self):
        """从所有解析树提取"""
        trees = getattr(self.parser, 'trees', {})
        for key, tree in trees.items():
            if tree and hasattr(tree, 'root') and tree.root:
                self._extract_from_tree(tree.root)
    
    def extract_from_tree(self, root, source: str = "") -> List[Dict]:
        """从 tree root 提取"""
        results = []
        
        def collect(node):
            try:
                if node.kind == SyntaxKind.ClassDeclaration:
                    class_info = self._extract_class(node, source)
                    if class_info:
                        results.append(class_info)
                else:
                    self._check_unsupported_node(node, source)
            except Exception as e:
                self.warn_handler.warn_error(
                    "TreeVisit",
                    e,
                    context=f"source={source}",
                    component="ClassExtractor"
                )
            
            return pyslang.VisitAction.Advance
        
        root_node = root if hasattr(root, "root") else root
        if root_node:
            try:
                root_node.visit(collect)
            except Exception as e:
                self.warn_handler.warn_error(
                    "RootVisit",
                    e,
                    context=f"source={source}",
                    component="ClassExtractor"
                )
        
        self.classes = results
        return results
    
    def _extract_class(self, node, source: str = ""):
        """提取单个类"""
        # name
        name = ""
        try:
            if hasattr(node, 'name') and node.name:
                name = str(node.name).strip()
        except Exception as e:
            self.warn_handler.warn_error(
                "ClassNameExtraction",
                e,
                context=f"source={source}",
                component="ClassExtractor"
            )
        
        if not name:
            self.warn_handler.warn_unsupported(
                "UnnamedClass",
                context=source,
                suggestion="class名为空",
                component="ClassExtractor"
            )
            return None
        
        # extends
        extends = ""
        try:
            if hasattr(node, 'extendsClause') and node.extendsClause:
                extends = str(node.extendsClause).strip()
        except Exception as e:
            self.warn_handler.warn_error(
                "ClassExtendsExtraction",
                e,
                context=f"class={name}",
                component="ClassExtractor"
            )
        
        info = {
            'name': name,
            'extends': extends,
            'members': [],
            'methods': [],
            'constraints': []
        }
        
        # items - 类成员
        if hasattr(node, 'items') and node.items:
            try:
                for item in node.items:
                    if not item:
                        continue
                    
                    kind = str(item.kind) if hasattr(item.kind, 'name') else type(item).__name__
                    
                    try:
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
                        
                        else:
                            self._check_unsupported_node(item, f"class::{name}")
                            
                    except Exception as e:
                        self.warn_handler.warn_error(
                            "ClassItemExtraction",
                            e,
                            context=f"class={name}, kind={kind}",
                            component="ClassExtractor"
                        )
                        
            except Exception as e:
                self.warn_handler.warn_error(
                    "ClassItemsIteration",
                    e,
                    context=f"class={name}",
                    component="ClassExtractor"
                )
        
        return info
    
    def _extract_member(self, node):
        """提取类成员"""
        member = ClassMember()
        
        try:
            # 获取声明字符串
            decl = str(node).strip()
            
            # rand 模式
            if hasattr(node, 'qualifiers') and node.qualifiers:
                member.rand_mode = str(node.qualifiers).strip()
            
            # 类型和名称
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
            else:
                # 尝试更简单的格式
                simple_match = re.search(r'(\w+)\s+(\w+)', decl)
                if simple_match:
                    member.data_type = simple_match.group(1)
                    member.name = simple_match.group(2)
                else:
                    self.warn_handler.warn_unsupported(
                        "UnknownMemberFormat",
                        context=decl[:50],
                        suggestion="无法解析class成员格式",
                        component="ClassExtractor"
                    )
                    
        except Exception as e:
            self.warn_handler.warn_error(
                "MemberExtraction",
                e,
                context="_extract_member",
                component="ClassExtractor"
            )
        
        return member
    
    def _extract_method(self, node):
        """提取类方法"""
        method = ClassMethod()
        
        try:
            decl = str(node).strip()
            
            # function/task
            if 'task' in decl.split()[0]:
                method.kind = 'task'
            
            # 返回类型和名称
            match = re.search(r'(function|task)\s+(\w+(?:\s+\w+)*?)\s+(\w+)', decl)
            if match:
                method.kind = match.group(1)
                method.return_type = match.group(2)
                method.name = match.group(3)
            else:
                # 尝试更简单的格式
                simple_match = re.search(r'(function|task)\s+(\w+)', decl)
                if simple_match:
                    method.kind = simple_match.group(1)
                    method.name = simple_match.group(2)
                else:
                    self.warn_handler.warn_unsupported(
                        "UnknownMethodFormat",
                        context=decl[:50],
                        suggestion="无法解析class方法格式",
                        component="ClassExtractor"
                    )
                        
        except Exception as e:
            self.warn_handler.warn_error(
                "MethodExtraction",
                e,
                context="_extract_method",
                component="ClassExtractor"
            )
        
        return method
    
    def _extract_constraint(self, node):
        """提取类约束"""
        constr = ClassConstraint()
        
        try:
            if hasattr(node, 'name') and node.name:
                constr.name = str(node.name).strip()
            
            # expr from block
            if hasattr(node, 'block') and node.block:
                constr.expr = str(node.block).strip()
            else:
                constr.expr = str(node)[:80].strip()
                
        except Exception as e:
            self.warn_handler.warn_error(
                "ConstraintExtraction",
                e,
                context="_extract_constraint",
                component="ClassExtractor"
            )
        
        return constr
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        """从文本提取"""
        try:
            tree = pyslang.SyntaxTree.fromText(code, source)
            return self.extract_from_tree(tree.root, source)
        except Exception as e:
            self.warn_handler.warn_error(
                "TextParsing",
                e,
                context=source,
                component="ClassExtractor"
            )
            return []
    
    def get_warning_report(self) -> str:
        """获取警告报告"""
        return self.warn_handler.get_report()
    
    def print_warning_report(self):
        """打印警告报告"""
        self.warn_handler.print_report()


# 别名
def get_classes(code, verbose: bool = True):
    """便捷函数"""
    ce = ClassExtractor(verbose=verbose)
    return ce.extract_from_text(code)
