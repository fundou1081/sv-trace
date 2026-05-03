"""DanglingPortDetector - 悬空端口检测。

检测模块中未连接或未使用的端口。

Example:
    >>> from debug.analyzers.dangling_port import DanglingPortDetector
    >>> from parse import SVParser
    >>> parser = SVParser()
    >>> parser.parse_file("design.sv")
    >>> detector = DanglingPortDetector(parser)
    >>> issues = detector.detect("ModuleName")
    >>> for issue in issues:
    ...     print(f"{issue.port}: {issue.issue_type}")
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class DanglingPortIssue:
    """悬空端口问题数据类。
    
    Attributes:
        module: 模块名
        port: 端口名
        direction: 方向 (input/output/inout)
        issue_type: 问题类型 (unconnected/partially_connected/unused)
        severity: 严重级别
    """
    module: str
    port: str
    direction: str
    issue_type: str
    severity: str = "warning"


class DanglingPortDetector:
    """悬空端口检测器。
    
    检测模块中未连接或未使用的端口。

    Attributes:
        parser: SVParser 实例
    
    Example:
        >>> detector = DanglingPortDetector(parser)
        >>> issues = detector.detect("ModuleName")
    """
    
    def __init__(self, parser):
        """初始化检测器。
        
        Args:
            parser: SVParser 实例
        """
        self.parser = parser
    
    def detect(self, module_name: str = None) -> List[DanglingPortIssue]:
        """检测悬空端口。
        
        Args:
            module_name: 可选的模块名过滤
        
        Returns:
            List[DanglingPortIssue]: 问题列表
        """
        issues = []
        
        for fname, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            root = tree.root
            if not hasattr(root, 'members'):
                continue
            
            for i in range(len(root.members)):
                member = root.members[i]
                if 'ModuleDeclaration' not in str(type(member)):
                    continue
                
                mod_name = self._get_module_name(member)
                if module_name and mod_name != module_name:
                    continue
                
                # Find ports
                ports = self._find_ports(member)
                
                # Find instantiations
                instantiations = self._find_instantiations(member)
                
                # Check each port
                for port in ports:
                    if port not in instantiations:
                        issues.append(DanglingPortIssue(
                            module=mod_name,
                            port=port,
                            direction="unknown",
                            issue_type="unconnected",
                            severity="warning"
                        ))
        
        return issues
    
    def _get_module_name(self, module_node) -> str:
        """获取模块名。"""
        if hasattr(module_node, 'header') and module_node.header:
            if hasattr(module_node.header, 'name') and module_node.header.name:
                name = module_node.header.name
                if hasattr(name, 'value'):
                    return str(name.value).strip()
                return str(name).strip()
        return ""
    
    def _find_ports(self, module) -> List[str]:
        """查找模块端口。"""
        ports = []
        
        if hasattr(module, 'members') and module.members:
            for stmt in module.members:
                if not stmt:
                    continue
                stmt_str = str(stmt)
                
                # Simple pattern matching for port declarations
                import re
                port_pattern = r'\b(input|output|inout)\b.*?(\w+)\s*[,;]'
                matches = re.findall(port_pattern, stmt_str)
                for direction, port_name in matches:
                    if port_name not in ports:
                        ports.append(port_name)
        
        return ports
    
    def _find_instantiations(self, module) -> Set[str]:
        """查找已连接的端口。"""
        connected = set()
        
        if hasattr(module, 'members') and module.members:
            for stmt in module.members:
                if not stmt:
                    continue
                stmt_str = str(stmt)
                
                # Find .portname(...) patterns
                import re
                conn_pattern = r'\.(\w+)\s*\('
                matches = re.findall(conn_pattern, stmt_str)
                connected.update(matches)
        
        return connected
