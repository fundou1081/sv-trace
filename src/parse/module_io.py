"""
ModuleIOExtractor - 提取模块IO及其定义
使用正则表达式直接从源码提取
"""
import re
from typing import List, Dict


class Port:
    def __init__(self, name, direction, width=1):
        self.name = name.strip()
        self.direction = direction.strip()
        self.width = width
    
    def __str__(self):
        if self.width == 1:
            return f"{self.direction} {self.name}"
        return f"{self.direction} [{self.width-1}:0] {self.name}"


class ModuleIO:
    def __init__(self, name):
        self.name = name
        self.ports = []
        self.params = []
    
    def add_port(self, port):
        self.ports.append(port)
    
    def to_list(self) -> List[Dict]:
        return [
            {"name": p.name, "direction": p.direction, "width": p.width}
            for p in self.ports
        ]
    
    def to_dict(self) -> Dict:
        return {
            "module": self.name,
            "ports": self.to_list()
        }


class ModuleIOExtractor:
    """模块IO提取器"""
    
    def __init__(self, parser=None):
        self.parser = parser
        self.modules = {}
    
    def extract(self, module_name) -> ModuleIO:
        """从解析树提取"""
        if not self.parser:
            return None
        
        for key, tree in self.parser.trees.items():
            if tree and tree.root:
                name = str(tree.root.name)
                if module_name and name != module_name:
                    continue
                
                io = ModuleIO(name)
                
                # 提取端口
                if hasattr(tree.root, 'ports'):
                    for port in tree.root.ports:
                        direction = 'input'
                        if hasattr(port, 'direction') and str(port.direction).lower() == 'out':
                            direction = 'output'
                        elif hasattr(port, 'direction') and str(port.direction).lower() == 'inout':
                            direction = 'inout'
                        
                        port_name = str(port.name) if hasattr(port, 'name') else ''
                        width = 1
                        
                        if hasattr(port, 'width') and port.width:
                            w = port.width
                            if hasattr(w, 'items'):
                                width = 1
                            else:
                                try:
                                    width = int(str(w)) + 1
                                except:
                                    width = 1
                        
                        io.add_port(Port(port_name, direction, width))
                
                self.modules[name] = io
                return io
        
        return None
    
    def extract_from_text(self, code: str) -> List[ModuleIO]:
        """从源码文本提取"""
        modules = []
        
        # 匹配module声明
        pattern = r'module\s+(\w+)\s*\(([^)]*)\)\s*;'
        matches = re.finditer(pattern, code)
        
        for m in matches:
            name = m.group(1)
            ports_str = m.group(2)
            io = ModuleIO(name)
            
            # 解析端口列表
            for port in ports_str.split(','):
                port = port.strip()
                if not port:
                    continue
                
                parts = port.split()
                if len(parts) >= 2:
                    direction = parts[0]
                    
                    # 检查位宽
                    width = 1
                    if '[' in parts[1]:
                        # input [7:0] data
                        width_match = re.search(r'\[(\d+):', parts[1])
                        if width_match:
                            width = int(width_match.group(1)) + 1
                        name = parts[2] if len(parts) > 2 else parts[1].split('[')[0]
                    else:
                        name = parts[1]
                    
                    if direction in ['input', 'output', 'inout']:
                        io.add_port(Port(name, direction, width))
            
            modules.append(io)
            self.modules[name] = io
        
        return modules
    
    def get_io(self, name) -> ModuleIO:
        return self.modules.get(name)
    
    def list_modules(self) -> List[str]:
        return list(self.modules.keys())


__all__ = ['ModuleIOExtractor', 'ModuleIO', 'Port']
