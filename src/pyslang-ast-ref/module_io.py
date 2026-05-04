"""
ModuleIOExtractor - 提取模块IO及参数
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


class Parameter:
    def __init__(self, name, value=""):
        self.name = name.strip()
        self.value = value
    
    def __str__(self):
        return f"parameter {self.name} = {self.value}"


class ModuleIO:
    def __init__(self, name):
        self.name = name
        self.ports = []
        self.params = []
    
    def add_port(self, port):
        self.ports.append(port)
    
    def add_param(self, param):
        self.params.append(param)
    
    def to_list(self) -> List[Dict]:
        return {
            "ports": [{"name": p.name, "direction": p.direction, "width": p.width} for p in self.ports],
            "params": [{"name": p.name, "value": p.value} for p in self.params]
        }
    
    def to_dict(self) -> Dict:
        return {
            "module": self.name,
            "ports": [{"name": p.name, "direction": p.direction, "width": p.width} for p in self.ports],
            "params": [{"name": p.name, "value": p.value} for p in self.params]
        }


class ModuleIOExtractor:
    """模块IO和参数提取器"""
    
    def __init__(self, parser=None):
        self.parser = parser
        self.modules = {}
    
    def extract_from_text(self, code: str) -> List[ModuleIO]:
        """从源码文本提取"""
        modules = []
        
        # 分割每个module
        module_pattern = r'module\s+(\w+)\s*#\s*\(([^)]*)\)\s*\(([^)]*)\)\s*;|module\s+(\w+)\s*\(([^)]*)\)\s*;'
        # 更简单的匹配
        module_blocks = re.split(r'(?=module\s+\w+)', code)
        
        for block in module_blocks:
            block = block.strip()
            if not block.startswith('module'):
                continue
            
            # 提取module名和参数
            header_match = re.search(r'module\s+(\w+)\s*(?:#\s*\(([^)]*)\))?\s*\(([^)]*)\)\s*;', block, re.DOTALL)
            if not header_match:
                continue
            
            name = header_match.group(1)
            params_str = header_match.group(2) or ""
            ports_str = header_match.group(3) or ""
            
            io = ModuleIO(name)
            
            # 解析参数
            if params_str:
                for param in params_str.split(','):
                    param = param.strip()
                    if not param:
                        continue
                    # parameter NAME = value 或 localparam NAME = value
                    pm = re.match(r'(?:parameter|localparam)\s+(\w+)\s*=\s*(\S+)', param, re.IGNORECASE)
                    if pm:
                        io.add_param(Parameter(pm.group(1), pm.group(2)))
                    else:
                        # 简单参数名
                        parts = param.split()
                        if len(parts) >= 2 and parts[0].lower() in ['parameter', 'localparam']:
                            io.add_param(Parameter(parts[1], ""))
            
            # 解析端口
            for port in ports_str.split(','):
                port = port.strip()
                if not port:
                    continue
                
                parts = port.split()
                if len(parts) < 2:
                    continue
                
                direction = parts[0]
                if direction not in ['input', 'output', 'inout']:
                    continue
                
                # 检查位宽
                width = 1
                port_str = ' '.join(parts[1:])
                
                # 跳过 reg, wire, logic 等类型关键词
                for keyword in ['reg', 'wire', 'logic', 'bit']:
                    port_str = port_str.replace(keyword, '').strip()
                
                # 匹配 [xxx:0] 格式
                width_match = re.search(r'\[.*?:\s*0\]', port_str)
                if width_match:
                    # 提取冒号前的数字或标识符
                    bracket_content = width_match.group(0)[1:-3]  # 去掉 [ 和 :0]
                    if bracket_content.isdigit():
                        width = int(bracket_content) + 1
                    else:
                        width = bracket_content  # 保留表达式如 WIDTH-1
                    # 提取端口名
                    name = port_str.split(']')[-1].strip() if ']' in port_str else parts[-1]
                else:
                    name = port_str.strip()
                
                io.add_port(Port(name, direction, width))
            
            modules.append(io)
            self.modules[name] = io
        
        return modules

    def extract_from_text(self, code: str) -> List[ModuleIO]:
        """从源码文本提取 (使用 pyslang AST)"""
        import pyslang
        from pyslang import SyntaxKind
        import re
        
        modules = []
        
        try:
            tree = pyslang.SyntaxTree.fromText(code)
            root = tree.root
            
            # 找到所有 ModuleDeclaration - 使用 visit 遍历
            modules_data = []
            
            def collect_module(node):
                if node.kind.name == 'ModuleDeclaration':
                    modules_data.append(node)
                return pyslang.VisitAction.Advance
            
            root.visit(collect_module)
            
            for mod in modules_data:
                if not hasattr(mod, 'header'):
                    continue
                    
                h = mod.header
                name = str(h.name) if hasattr(h, 'name') else 'unknown'
                io = ModuleIO(name)
                
                # 提取 parameters
                if hasattr(h, 'parameters') and h.parameters:
                    params = h.parameters
                    if hasattr(params, 'parameters'):
                        params = params.parameters
                    for p in params:
                        if hasattr(p, 'name'):
                            param_name = str(p.name)
                            param_value = str(p.value) if hasattr(p, 'value') else '1'
                            io.add_param(Parameter(param_name, param_value))
                
                # 提取 ports
                if hasattr(h, 'ports') and h.ports:
                    ports = h.ports
                    if hasattr(ports, 'ports'):
                        ports = ports.ports
                    
                    for p in ports:
                        if not isinstance(p, pyslang.ImplicitAnsiPortSyntax):
                            continue
                        
                        decl = p.declarator
                        if not decl or not hasattr(decl, 'name'):
                            continue
                            
                        port_name = str(decl.name)
                        
                        # 方向
                        direction = 'input'
                        if hasattr(p.header, 'direction') and hasattr(p.header.direction, 'kind'):
                            dk = p.header.direction.kind
                            if 'Output' in str(dk):
                                direction = 'output'
                            elif 'InOut' in str(dk):
                                direction = 'inout'
                        else:
                            header_str = str(p.header).strip() if hasattr(p, 'header') else ''
                            if header_str.startswith('output'):
                                direction = 'output'
                            elif header_str.startswith('inout'):
                                direction = 'inout'
                        
                        # 宽度
                        width = 1
                        if hasattr(decl, 'dimensions') and decl.dimensions:
                            dims_str = str(decl.dimensions)
                            m = re.search(r'\[(\d+):(\d+)\]', dims_str)
                            if m:
                                width = int(m.group(1)) - int(m.group(2)) + 1
                        
                        # 是否是 reg
                        header_str = str(p.header).strip() if hasattr(p, 'header') else ''
                        is_reg = 'reg' in header_str.lower()
                        
                        io.add_port(Port(port_name, direction, width))
                
                modules.append(io)
                
        except Exception as e:
            print(f"Module parse error: {e}")
            import traceback
            traceback.print_exc()
        
        return modules

    
    def get_io(self, name) -> ModuleIO:
        return self.modules.get(name)
    
    def list_modules(self) -> List[str]:
        return list(self.modules.keys())


__all__ = ['ModuleIOExtractor', 'ModuleIO', 'Port', 'Parameter']
