"""
提取器 - 从 AST 中提取各类元素

增强版: 添加解析警告，显式打印不支持的语法结构
"""
import pyslang
from pyslang import SyntaxKind
from typing import List, Dict, Any
import re
import os
import sys

# 导入解析警告模块
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
        def __init__(self, verbose=True, component="Extractors"):
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


class ModuleExtractor:
    """模块提取器
    
    增强版: 添加解析警告
    """
    
    UNSUPPORTED_TYPES = {
        'CovergroupDeclaration': 'covergroup不支持',
        'InterfaceDeclaration': 'interface不支持',
        'PackageDeclaration': 'package不支持',
        'ProgramDeclaration': 'program不支持',
    }
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.warn_handler = ParseWarningHandler(verbose=verbose, component="ModuleExtractor")
        self._unsupported_encountered = set()
    
    def extract(self, tree: pyslang.SyntaxTree) -> List[Dict[str, Any]]:
        """提取模块信息"""
        modules = []
        
        if not tree or not hasattr(tree, 'root'):
            return modules
        
        root = tree.root
        
        def find_modules(node):
            if not node or not hasattr(node, 'kind'):
                return []
            
            kind_name = str(type(node))
            
            # 检查不支持的类型
            if kind_name in self.UNSUPPORTED_TYPES:
                if kind_name not in self._unsupported_encountered:
                    self.warn_handler.warn_unsupported(
                        kind_name,
                        context="ModuleExtractor",
                        suggestion=self.UNSUPPORTED_TYPES[kind_name],
                        component="ModuleExtractor"
                    )
                    self._unsupported_encountered.add(kind_name)
            
            if 'ModuleDeclaration' in kind_name:
                return [node]
            
            result = []
            for attr in ['members', 'body']:
                if hasattr(node, attr):
                    children = getattr(node, attr)
                    if children:
                        for m in children:
                            result.extend(find_modules(m))
            return result
        
        for member in find_modules(root):
            try:
                modules.append(self._extract_module(member))
            except Exception as e:
                self.warn_handler.warn_error(
                    "ModuleExtraction",
                    e,
                    context="ModuleExtractor.extract",
                    component="ModuleExtractor"
                )
        
        return modules
    
    def _extract_module(self, mod) -> Dict[str, Any]:
        info = {"name": "", "kind": "module", "ports": [], "parameters": []}
        
        try:
            if hasattr(mod, 'header') and mod.header:
                if hasattr(mod.header, 'name') and mod.header.name:
                    info["name"] = str(mod.header.name).strip()
        except Exception as e:
            self.warn_handler.warn_error(
                "ModuleNameExtraction",
                e,
                context="ModuleExtractor._extract_module",
                component="ModuleExtractor"
            )
        
        return info
    
    def get_warning_report(self) -> str:
        return self.warn_handler.get_report()


class SignalExtractor:
    """信号提取器
    
    增强版: 添加解析警告
    """
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.warn_handler = ParseWarningHandler(verbose=verbose, component="SignalExtractor")
    
    def extract(self, tree: pyslang.SyntaxTree) -> List[Dict[str, Any]]:
        signals = []
        
        if not tree or not hasattr(tree, 'root'):
            return signals
        
        root = tree.root
        
        def find_signals(node):
            if not node or not hasattr(node, 'kind'):
                return []
            
            kind_name = str(node.kind) if hasattr(node, 'kind') else str(type(node))
            
            if 'DataDeclaration' in kind_name or 'NetDeclaration' in kind_name or 'VariableDeclaration' in kind_name:
                return [node]
            
            result = []
            for attr in ['members', 'body', 'statements']:
                if hasattr(node, attr):
                    children = getattr(node, attr)
                    if children:
                        for m in children:
                            result.extend(find_signals(m))
            return result
        
        for decl in find_signals(root):
            try:
                sig = {"name": "", "type": "logic", "width": 1}
                
                if hasattr(decl, 'declarators') and decl.declarators:
                    try:
                        decl_item = list(decl.declarators)[0]
                        if hasattr(decl_item, 'name') and decl_item.name:
                            sig["name"] = str(decl_item.name).strip()
                    except Exception:
                        pass
                
                if sig["name"]:
                    signals.append(sig)
            except Exception as e:
                self.warn_handler.warn_error(
                    "SignalExtraction",
                    e,
                    context="SignalExtractor.extract",
                    component="SignalExtractor"
                )
        
        return [s for s in signals if s["name"]]
    
    def get_warning_report(self) -> str:
        return self.warn_handler.get_report()


class PortAnalyzer:
    """端口分析器
    
    增强版: 添加解析警告
    """
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.warn_handler = ParseWarningHandler(verbose=verbose, component="PortAnalyzer")
    
    def analyze(self, module) -> Dict[str, List[Dict[str, Any]]]:
        result = {"inputs": [], "outputs": [], "inouts": []}
        
        try:
            if not hasattr(module, 'header') or not module.header:
                return result
            
            ports = module.header.ports
            if not ports or not hasattr(ports, 'ports'):
                return result
            
            for port in ports.ports:
                if not port:
                    continue
                
                try:
                    port_info = {"name": "", "direction": ""}
                    
                    if hasattr(port, 'name') and port.name:
                        port_info["name"] = str(port.name).strip()
                    
                    if hasattr(port, 'direction'):
                        port_info["direction"] = str(port.direction)
                    
                    direction = port_info["direction"].lower()
                    if "input" in direction:
                        result["inputs"].append(port_info)
                    elif "output" in direction:
                        result["outputs"].append(port_info)
                    elif "inout" in direction:
                        result["inouts"].append(port_info)
                except Exception as e:
                    self.warn_handler.warn_error(
                        "PortAnalysis",
                        e,
                        context="PortAnalyzer.analyze",
                        component="PortAnalyzer"
                    )
                    
        except Exception as e:
            self.warn_handler.warn_error(
                "ModuleAnalysis",
                e,
                context="PortAnalyzer.analyze",
                component="PortAnalyzer"
            )
        
        return result
    
    def get_warning_report(self) -> str:
        return self.warn_handler.get_report()


class InstanceExtractor:
    """实例提取器"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.warn_handler = ParseWarningHandler(verbose=verbose, component="InstanceExtractor")
    
    def extract(self, tree: pyslang.SyntaxTree) -> List[Dict[str, Any]]:
        instances = []
        # 实现待补充
        return instances


class AlwaysBlockExtractor:
    """Always块提取器"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.warn_handler = ParseWarningHandler(verbose=verbose, component="AlwaysBlockExtractor")
    
    def extract(self, tree: pyslang.SyntaxTree) -> List[Dict[str, Any]]:
        blocks = []
        # 实现待补充
        return blocks


# 便捷函数
def extract_signals(parser, verbose: bool = True) -> List[Dict[str, Any]]:
    """提取所有信号"""
    extractor = SignalExtractor(verbose=verbose)
    if hasattr(parser, 'trees'):
        all_signals = []
        for tree in parser.trees.values():
            if tree:
                all_signals.extend(extractor.extract(tree))
        return all_signals
    elif hasattr(parser, 'root'):
        return extractor.extract(parser)
    return []


def extract_instances(parser, verbose: bool = True) -> List[Dict[str, Any]]:
    """提取所有实例"""
    extractor = InstanceExtractor(verbose=verbose)
    return []


def extract_always_blocks(parser, verbose: bool = True) -> List[Dict[str, Any]]:
    """提取所有always块"""
    extractor = AlwaysBlockExtractor(verbose=verbose)
    return []
