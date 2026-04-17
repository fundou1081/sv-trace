"""
Path & Hierarchy Query - 路径与层级查询
"""
from typing import List, Dict, Optional, Any
import pyslang


class PathQuery:
    """路径查询"""
    
    def __init__(self, parser):
        self.parser = parser
    
    def get_hierarchical_path(self, symbol, instance_path: str = "") -> str:
        """获取层次化路径"""
        parts = []
        
        if instance_path:
            parts.append(instance_path)
        
        if hasattr(symbol, 'name') and symbol.name:
            parts.append(symbol.name.value)
        
        return ".".join(parts)
    
    def resolve_path(self, path: str) -> Optional[Any]:
        """解析层次路径"""
        parts = path.split(".")
        
        # 从根开始查找
        root = self.parser.compilation.getRoot()
        
        # 逐层查找
        current = root
        for part in parts:
            if hasattr(current, part):
                current = getattr(current, part)
            else:
                return None
        
        return current


class HierarchyQuery:
    """层级查询"""
    
    def __init__(self, parser):
        self.parser = parser
    
    def get_instances(self, module_name: str = None) -> List[Dict[str, Any]]:
        """获取模块实例"""
        instances = []
        
        # 搜索所有模块
        for tree in self.parser.trees.values():
            for member in tree.root.members:
                if hasattr(member, 'kind') and member.kind == pyslang.SyntaxKind.ModuleDeclaration:
                    # 查找实例化
                    instances.extend(self._find_instantiations(member, module_name))
        
        return instances
    
    def _find_instantiations(self, module, target_name: str = None) -> List[Dict[str, Any]]:
        """查找模块实例化"""
        instances = []
        
        if not hasattr(module, 'body'):
            return instances
        
        for member in module.body:
            if hasattr(member, 'kind') and member.kind == pyslang.SyntaxKind.HierarchicalInstantiation:
                for inst in member.instances:
                    inst_name = inst.name.value if hasattr(inst, 'name') and inst.name else ""
                    
                    if target_name and inst.moduleName.value != target_name:
                        continue
                    
                    instances.append({
                        "name": inst_name,
                        "module": inst.moduleName.value,
                        "parameters": self._extract_parameters(inst),
                    })
        
        return instances
    
    def _extract_parameters(self, inst) -> List[str]:
        """提取参数"""
        params = []
        if hasattr(inst, 'connections'):
            for conn in inst.connections:
                if hasattr(conn, 'ordered':
                    continue
        return params
