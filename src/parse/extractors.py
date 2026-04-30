"""
提取器 - 从 AST 中提取各类元素
"""
import pyslang
from typing import List, Dict, Any


class ModuleExtractor:
    """模块提取器"""
    
    @staticmethod
    def extract(tree: pyslang.SyntaxTree) -> List[Dict[str, Any]]:
        """提取模块信息"""
        modules = []
        
        def find_modules(node):
            if hasattr(node, 'kind'):
                kind_name = str(type(node))
                if 'ModuleDeclaration' in kind_name:
                    return [node]
                for attr in ['members', 'body']:
                    if hasattr(node, attr):
                        result = []
                        for m in getattr(node, attr):
                            result.extend(find_modules(m))
                        return result
            return []
        
        for member in find_modules(root.root):
            modules.append(ModuleExtractor._extract_module(member))
        
        return modules
    
    @staticmethod
    def _extract_module(mod) -> Dict[str, Any]:
        info = {"name": "", "kind": "module", "ports": [], "parameters": []}
        
        if hasattr(mod, 'header') and mod.header:
            if hasattr(mod.header, 'name') and mod.header.name:
                info["name"] = mod.header.name.value
        
        return info


class SignalExtractor:
    """信号提取器"""
    
    @staticmethod
    def extract(tree: pyslang.SyntaxTree) -> List[Dict[str, Any]]:
        signals = []
        
        def find_signals(node):
            if hasattr(node, 'kind') and node.kind == pyslang.SyntaxKind.DataDeclaration:
                return [node]
            result = []
            for attr in ['members', 'body', 'statements']:
                if hasattr(node, attr):
                    for m in getattr(node, attr, []):
                        result.extend(find_signals(m))
            return result
        
        for decl in find_signals(root.root):
            sig = {"name": "", "type": "logic", "width": 1}
            
            if hasattr(decl, 'declarators') and decl.declarators:
                decl_item = decl.declarators[0]
                if hasattr(decl_item, 'name') and decl_item.name:
                    sig["name"] = decl_item.name.value
            
            signals.append(sig)
        
        return [s for s in signals if s["name"]]


class PortAnalyzer:
    """端口分析器"""
    
    @staticmethod
    def analyze(module) -> Dict[str, List[Dict[str, Any]]]:
        result = {"inputs": [], "outputs": [], "inouts": []}
        
        if not hasattr(module, 'header') or not module.header:
            return result
        
        ports = module.header.ports
        if not ports or not hasattr(ports, 'ports'):
            return result
        
        for port in ports.ports:
            port_info = {"name": "", "direction": ""}
            
            if hasattr(port, 'name') and port.name:
                port_info["name"] = port.name.value
            
            if hasattr(port, 'direction'):
                port_info["direction"] = str(port.direction)
            
            direction = port_info["direction"].lower()
            if "input" in direction:
                result["inputs"].append(port_info)
            elif "output" in direction:
                result["outputs"].append(port_info)
            elif "inout" in direction:
                result["inouts"].append(port_info)
        
        return result
