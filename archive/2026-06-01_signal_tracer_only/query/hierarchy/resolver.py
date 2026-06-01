"""
层级路径解析器
支持解析跨模块的层次路径，如 top.cpu.u_alu.result
"""
from typing import Optional, List, Dict, Any, Tuple
import pyslang


class HierarchicalPath:
    """层次路径表示"""
    def __init__(self, path_str: str):
        self.original = path_str
        self.parts = path_str.split(".")
    
    def get_signal_name(self) -> str:
        return self.parts[-1] if self.parts else ""
    
    def get_instance_path(self) -> str:
        return ".".join(self.parts[:-1]) if len(self.parts) > 1 else ""
    
    def get_modules(self) -> List[str]:
        return self.parts[:-1]


class HierarchicalResolver:
    """层级路径解析器"""
    
    def __init__(self, parser):
        self.parser = parser
        self._module_def_cache: Dict[str, Any] = {}
        self._port_cache: Dict[str, List[Dict[str, Any]]] = {}
    
    def resolve_signal(self, path: str) -> Optional[Dict[str, Any]]:
        """解析层次路径"""
        hier_path = HierarchicalPath(path)
        signal_name = hier_path.get_signal_name()
        
        if not hier_path.get_instance_path():
            return self._resolve_simple_signal(signal_name)
        
        instance_chain = hier_path.get_modules()
        return self._resolve_hierarchical_signal(signal_name, instance_chain)
    
    def _get_all_modules(self):
        """获取所有模块定义"""
        modules = []
        
        for tree in self.parser.trees.values():
            if not tree or not tree.root:
                continue
            
            root = tree.root
            root_type = type(root).__name__
            
            if root_type == 'CompilationUnitSyntax' and hasattr(root, 'members'):
                for i in range(len(root.members)):
                    member = root.members[i]
                    if hasattr(member, 'header') and member.header:
                        modules.append(member)
            elif root_type == 'ModuleDeclarationSyntax' and hasattr(root, 'header') and root.header:
                modules.append(root)
        
        return modules
    
    def _find_module_by_name(self, name: str):
        """根据名称查找模块"""
        for module in self._get_all_modules():
            if hasattr(module, 'header') and module.header:
                if hasattr(module.header, 'name') and module.header.name:
                    if module.header.name.value == name:
                        return module
        return None
    
    def _resolve_simple_signal(self, signal_name: str) -> Optional[Dict[str, Any]]:
        """解析简单信号"""
        for module in self._get_all_modules():
            result = self._find_signal_in_module(module, signal_name)
            if result:
                result["path"] = signal_name
                return result
        return None
    
    def _resolve_hierarchical_signal(self, signal_name: str, 
                                     instance_chain: List[str]) -> Optional[Dict[str, Any]]:
        """解析层次信号"""
        if not instance_chain:
            return self._resolve_simple_signal(signal_name)
        
        root_module_name = instance_chain[0]
        root_module = self._find_module_by_name(root_module_name)
        if not root_module:
            return None
        
        current_module = root_module
        
        for i in range(1, len(instance_chain)):
            inst_name = instance_chain[i]
            child_module = self._find_child_module(current_module, inst_name)
            if not child_module:
                return None
            current_module = child_module
        
        result = self._find_signal_in_module(current_module, signal_name)
        if result:
            result["path"] = ".".join(instance_chain + [signal_name])
            result["instance_chain"] = instance_chain
            if hasattr(current_module, 'header') and current_module.header:
                result["module"] = current_module.header.name.value
        
        return result
    
    def _get_module_members(self, module):
        """获取模块成员"""
        if hasattr(module, 'members') and module.members:
            return module.members
        if hasattr(module, 'body') and module.body:
            return module.body
        return None
    
    def _find_child_module(self, parent_module, inst_name: str) -> Optional[Any]:
        """在父模块中查找子模块实例"""
        members = self._get_module_members(parent_module)
        if not members:
            return None
        
        for i in range(len(members)):
            member = members[i]
            
            if hasattr(member, 'kind') and member.kind == pyslang.SyntaxKind.HierarchyInstantiation:
                inst_node = member.instances
                if not inst_node:
                    continue
                
                for j in range(len(inst_node)):
                    inst = inst_node[j]
                    
                    inst_name_in_code = ""
                    if hasattr(inst, 'decl') and inst.decl:
                        if hasattr(inst.decl, 'name') and inst.decl.name:
                            inst_name_in_code = inst.decl.name.value
                    
                    if inst_name_in_code == inst_name:
                        module_type = ""
                        if hasattr(member, 'type') and member.type:
                            if hasattr(member.type, 'value'):
                                module_type = member.type.value
                        
                        return self._find_module_by_name(module_type)
        
        return None
    
    def _get_port_direction(self, port_item) -> str:
        """获取端口方向 - 支持两种类型"""
        if not hasattr(port_item, 'header') or not port_item.header:
            return "unknown"
        
        header_val = port_item.header
        header_type = type(header_val).__name__
        
        direction = "unknown"
        
        if header_type == 'VariablePortHeaderSyntax':
            # input logic / output logic
            if hasattr(header_val, 'direction') and header_val.direction:
                dir_kind = header_val.direction.kind
                if dir_kind == pyslang.TokenKind.InputKeyword:
                    direction = "input"
                elif dir_kind == pyslang.TokenKind.OutputKeyword:
                    direction = "output"
                elif dir_kind == pyslang.TokenKind.InoutKeyword:
                    direction = "inout"
        
        elif header_type == 'NetPortHeaderSyntax':
            # input wire / output wire
            if hasattr(header_val, 'direction') and header_val.direction:
                dir_kind = header_val.direction.kind
                if dir_kind == pyslang.TokenKind.InputKeyword:
                    direction = "input"
                elif dir_kind == pyslang.TokenKind.OutputKeyword:
                    direction = "output"
                elif dir_kind == pyslang.TokenKind.InoutKeyword:
                    direction = "inout"
        
        return direction
    
    def _get_module_ports(self, module) -> List[Dict[str, Any]]:
        """获取模块的所有端口及方向"""
        module_name = module.header.name.value if hasattr(module, 'header') and module.header else ""
        
        if module_name in self._port_cache:
            return self._port_cache[module_name]
        
        ports = []
        
        if not hasattr(module, 'header') or not module.header:
            self._port_cache[module_name] = ports
            return ports
        
        header = module.header
        
        if not hasattr(header, 'ports') or not header.ports:
            self._port_cache[module_name] = ports
            return ports
        
        port_list = header.ports
        if len(port_list) < 2:
            self._port_cache[module_name] = ports
            return ports
        
        ports_node = port_list[1]
        
        for i in range(len(ports_node)):
            item = ports_node[i]
            
            if type(item).__name__ not in ['ImplicitAnsiPortSyntax', 'ExplicitAnsiPortSyntax']:
                continue
            
            # 获取端口名
            port_name = ""
            if hasattr(item, 'declarator') and item.declarator:
                if hasattr(item.declarator, 'name') and item.declarator.name:
                    port_name = item.declarator.name.value
            
            # 获取方向
            direction = self._get_port_direction(item)
            
            # 获取 offset
            offset = 0
            if hasattr(item, 'sourceRange') and item.sourceRange:
                if hasattr(item.sourceRange, 'start'):
                    offset = item.sourceRange.start.offset
            
            ports.append({
                "name": port_name,
                "direction": direction,
                "offset": offset,
            })
        
        self._port_cache[module_name] = ports
        return ports
    
    def _find_signal_in_module(self, module, signal_name: str) -> Optional[Dict[str, Any]]:
        """在模块中查找信号定义"""
        members = self._get_module_members(module)
        if not members:
            return None
        
        module_name = module.header.name.value if hasattr(module, 'header') and module.header else ""
        
        # 检查是否是端口
        ports = self._get_module_ports(module)
        for port in ports:
            if port['name'] == signal_name:
                return {
                    "signal": signal_name,
                    "type": "port",
                    "direction": port['direction'],
                    "module": module_name,
                    "file": "",
                    "offset": port.get('offset', 0),
                }
        
        # 检查 DataDeclaration
        for i in range(len(members)):
            member = members[i]
            
            if hasattr(member, 'kind') and member.kind == pyslang.SyntaxKind.DataDeclaration:
                if hasattr(member, 'declarators') and member.declarators:
                    for j in range(len(member.declarators)):
                        decl = member.declarators[j]
                        if hasattr(decl, 'name') and decl.name:
                            if decl.name.value == signal_name:
                                offset = 0
                                if hasattr(decl.name, 'location'):
                                    offset = decl.name.location.offset
                                
                                return {
                                    "signal": signal_name,
                                    "type": "data",
                                    "member": member,
                                    "module": module_name,
                                    "file": "",
                                    "offset": offset,
                                }
        
        return None
    
    def get_all_instances(self) -> List[Dict[str, Any]]:
        """获取所有模块实例"""
        instances = []
        
        for module in self._get_all_modules():
            instances.extend(self._extract_instances_from_module(module))
        
        return instances
    
    def _extract_instances_from_module(self, module) -> List[Dict[str, Any]]:
        """从模块中提取实例"""
        instances = []
        
        members = self._get_module_members(module)
        if not members:
            return instances
        
        module_name = ""
        if hasattr(module, 'header') and module.header:
            if hasattr(module.header, 'name') and module.header.name:
                module_name = module.header.name.value
        
        for i in range(len(members)):
            member = members[i]
            if hasattr(member, 'kind') and member.kind == pyslang.SyntaxKind.HierarchyInstantiation:
                module_type = ""
                if hasattr(member, 'type') and member.type:
                    if hasattr(member.type, 'value'):
                        module_type = member.type.value
                
                inst_node = member.instances
                if not inst_node:
                    continue
                
                for j in range(len(inst_node)):
                    inst = inst_node[j]
                    
                    inst_name = ""
                    if hasattr(inst, 'decl') and inst.decl:
                        if hasattr(inst.decl, 'name') and inst.decl.name:
                            inst_name = inst.decl.name.value
                    
                    ports = self._extract_port_connections(inst, module_type)
                    
                    instances.append({
                        "instance_name": inst_name,
                        "module_type": module_type,
                        "parent_module": module_name,
                        "ports": ports,
                    })
        
        return instances
    
    def _extract_port_connections(self, inst, module_type: str) -> List[Dict[str, Any]]:
        """提取实例的端口连接（带方向）"""
        ports = []
        
        # 获取被实例化模块的端口方向
        target_module = self._find_module_by_name(module_type)
        if target_module:
            target_ports = self._get_module_ports(target_module)
        else:
            target_ports = []
        
        port_dir_map = {p['name']: p['direction'] for p in target_ports}
        
        if not hasattr(inst, 'connections') or not inst.connections:
            return ports
        
        conn_node = inst.connections
        
        for i in range(len(conn_node)):
            conn = conn_node[i]
            
            if type(conn).__name__ == 'Token':
                continue
            
            if hasattr(conn, 'name') and conn.name:
                port_name = conn.name.value if hasattr(conn.name, 'value') else ""
                
                connected_signal = ""
                if hasattr(conn, 'expr') and conn.expr:
                    if hasattr(conn.expr, 'value'):
                        connected_signal = conn.expr.value
                    else:
                        connected_signal = str(conn.expr)
                
                direction = port_dir_map.get(port_name, "unknown")
                
                ports.append({
                    "port": port_name,
                    "direction": direction,
                    "connected_to": connected_signal,
                })
        
        return ports
    
    def get_instance_info(self, instance_path: str) -> Optional[Dict[str, Any]]:
        """获取实例的详细信息"""
        hier_path = HierarchicalPath(instance_path)
        
        if len(hier_path.parts) < 2:
            return None
        
        instance_name = hier_path.parts[-1]
        parent_path = hier_path.parts[:-1]
        
        parent_module = self._find_module_by_name(parent_path[0])
        if not parent_module:
            return None
        
        current = parent_module
        for inst_name in parent_path[1:]:
            current = self._find_child_module(current, inst_name)
            if not current:
                return None
        
        return self._find_instance_in_module(current, instance_name)
    
    def _find_instance_in_module(self, module, instance_name: str) -> Optional[Dict[str, Any]]:
        """在模块中查找实例"""
        members = self._get_module_members(module)
        if not members:
            return None
        
        module_name = module.header.name.value if hasattr(module, 'header') and module.header else ""
        
        for i in range(len(members)):
            member = members[i]
            if hasattr(member, 'kind') and member.kind == pyslang.SyntaxKind.HierarchyInstantiation:
                inst_node = member.instances
                if not inst_node:
                    continue
                
                for j in range(len(inst_node)):
                    inst = inst_node[j]
                    
                    inst_name_found = ""
                    if hasattr(inst, 'decl') and inst.decl:
                        if hasattr(inst.decl, 'name') and inst.decl.name:
                            inst_name_found = inst.decl.name.value
                    
                    if inst_name_found == instance_name:
                        module_type = ""
                        if hasattr(member, 'type') and member.type:
                            if hasattr(member.type, 'value'):
                                module_type = member.type.value
                        
                        ports = self._extract_port_connections(inst, module_type)
                        
                        return {
                            "instance_name": instance_name,
                            "module_type": module_type,
                            "parent_module": module_name,
                            "ports": ports,
                        }
        
        return None
