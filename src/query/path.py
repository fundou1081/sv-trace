"""Path & Hierarchy Query - 路径与层级查询。

提供层次化路径解析和模块实例查询功能。

Example:
    >>> from query.path import PathQuery, HierarchyQuery
    >>> from parse import SVParser
    >>> parser = SVParser()
    >>> parser.parse_file("design.sv")
    >>> pq = PathQuery(parser)
    >>> path = pq.get_hierarchical_path(symbol)
"""
from typing import List, Dict, Optional, Any
import pyslang


class PathQuery:
    """路径查询。
    
    提供符号的层次化路径查询功能。

    Attributes:
        parser: SVParser 实例
    """
    
    def __init__(self, parser):
        """初始化路径查询器。
        
        Args:
            parser: SVParser 实例
        """
        self.parser = parser
    
    def get_hierarchical_path(self, symbol, instance_path: str = "") -> str:
        """获取层次化路径。
        
        Args:
            symbol: 符号对象
            instance_path: 实例路径前缀
        
        Returns:
            str: 层次化路径字符串，格式为 "instance.submodule.signal"
        """
        parts = []
        
        if instance_path:
            parts.append(instance_path)
        
        if hasattr(symbol, 'name') and symbol.name:
            parts.append(symbol.name.value)
        
        return ".".join(parts)
    
    def resolve_path(self, path: str) -> Optional[Any]:
        """解析层次路径。
        
        Args:
            path: 层次路径字符串
        
        Returns:
            解析后的对象，如果未找到则返回 None
        """
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
    """层级查询。
    
    提供模块实例的查找和层级关系查询功能。

    Attributes:
        parser: SVParser 实例
    """
    
    def __init__(self, parser):
        """初始化层级查询器。
        
        Args:
            parser: SVParser 实例
        """
        self.parser = parser
    
    def get_instances(self, module_name: str = None) -> List[Dict[str, Any]]:
        """获取模块实例。
        
        Args:
            module_name: 可选的模块名过滤条件
        
        Returns:
            List[Dict]: 实例信息列表，每项包含 name/module/parameters
        """
        instances = []
        
        # 搜索所有模块
        for tree in self.parser.trees.values():
            for member in tree.root.members:
                if hasattr(member, 'kind') and member.kind == pyslang.SyntaxKind.ModuleDeclaration:
                    # 查找实例化
                    instances.extend(self._find_instantiations(member, module_name))
        
        return instances
    
    def _find_instantiations(self, module, target_name: str = None) -> List[Dict[str, Any]]:
        """查找模块实例化。
        
        Args:
            module: 模块语法节点
            target_name: 目标模块名
        
        Returns:
            List[Dict]: 实例信息列表
        """
        instances = []
        
        if not hasattr(module, 'body'):
            return instances
        
        for member in module.body:
            if hasattr(member, 'kind') and member.kind == pyslang.SyntaxKind.HierarchyInstantiation:
                if hasattr(member, 'instances') and member.instances:
                    for inst in member.instances:
                        inst_name = inst.name.value if hasattr(inst, 'name') and inst.name else ""
                        
                        if target_name and hasattr(inst, 'moduleName') and inst.moduleName:
                            if inst.moduleName.value != target_name:
                                continue
                        
                        instances.append({
                            "name": inst_name,
                            "module": inst.moduleName.value if hasattr(inst, 'moduleName') and inst.moduleName else "",
                            "parameters": self._extract_parameters(inst),
                        })
        
        return instances
    
    def _extract_parameters(self, inst) -> List[str]:
        """提取参数。
        
        Args:
            inst: 实例化语法节点
        
        Returns:
            List[str]: 参数名列表
        """
        params = []
        if hasattr(inst, 'connections'):
            for conn in inst.connections:
                # Skip ordered connections
                if hasattr(conn, 'ordered') and conn.ordered:
                    continue
                # Handle named connections
                if hasattr(conn, 'port') and conn.port:
                    params.append(str(conn.port))
        return params
