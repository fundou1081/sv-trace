"""
MultiFileAnalyzer - 多文件联合分析器
分析多个SystemVerilog文件之间的信号传递和依赖关系
"""
import os
import sys
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


@dataclass
class ModuleInterface:
    """模块接口"""
    module_name: str
    file_path: str
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    inouts: List[str] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)
    localparams: List[str] = field(default_factory=list)


@dataclass
class SignalConnection:
    """信号连接"""
    source_module: str
    source_signal: str
    dest_module: str
    dest_signal: str
    file_path: str = ""


@dataclass
class FileDependency:
    """文件依赖"""
    file: str
    depends_on: List[str] = field(default_factory=list)
    depended_by: List[str] = field(default_factory=list)
    instantiates: List[str] = field(default_factory=list)
    instantiated_by: List[str] = field(default_factory=list)


@dataclass
class CrossFileSignal:
    """跨文件信号"""
    signal: str
    source_module: str
    source_file: str
    dest_modules: List[str] = field(default_factory=list)
    fanout: int = 0


@dataclass
class MultiFileReport:
    """多文件分析报告"""
    modules: Dict[str, ModuleInterface] = field(default_factory=dict)
    connections: List[SignalConnection] = field(default_factory=list)
    dependencies: Dict[str, FileDependency] = field(default_factory=dict)
    cross_file_signals: List[CrossFileSignal] = field(default_factory=list)
    orphan_signals: List[str] = field(default_factory=list)  # 未连接的信号


class MultiFileAnalyzer:
    """多文件联合分析器"""
    
    def __init__(self, file_paths: List[str]):
        self.file_paths = file_paths
        self.modules: Dict[str, ModuleInterface] = {}
        self.connections: List[SignalConnection] = []
        self.dependencies: Dict[str, FileDependency] = {}
        self.cross_file_signals: List[CrossFileSignal] = []
        self._parsed_content: Dict[str, str] = {}
    
    def analyze(self) -> MultiFileReport:
        """执行多文件分析"""
        
        # 1. 解析每个文件，提取模块接口
        self._extract_module_interfaces()
        
        # 2. 分析模块实例化关系
        self._analyze_instantiations()
        
        # 3. 追踪信号连接
        self._trace_connections()
        
        # 4. 查找跨文件信号
        self._find_cross_file_signals()
        
        # 5. 查找孤立信号
        self.orphan_signals: List[str] = []
        self._find_orphan_signals()
        
        return MultiFileReport(
            modules=self.modules,
            connections=self.connections,
            dependencies=self.dependencies,
            cross_file_signals=self.cross_file_signals,
            orphan_signals=self.orphan_signals
        )
    
    def _extract_module_interfaces(self):
        """提取每个文件的模块接口"""
        import re
        
        for fpath in self.file_paths:
            if not os.path.exists(fpath):
                continue
            
            with open(fpath, 'r') as f:
                content = f.read()
            
            self._parsed_content[fpath] = content
            
            # 查找module声明
            module_matches = re.finditer(
                r'module\s+(\w+)\s*#\s*\(([^)]*)\)\s*\(([^)]*)\)',
                content, re.DOTALL
            )
            
            for match in module_matches:
                module_name = match.group(1)
                params_str = match.group(2)
                ports_str = match.group(3)
                
                # 解析端口
                ports = self._parse_ports(ports_str)
                
                self.modules[module_name] = ModuleInterface(
                    module_name=module_name,
                    file_path=fpath,
                    inputs=ports['input'],
                    outputs=ports['output'],
                    inouts=ports['inout'],
                    parameters=self._parse_parameters(params_str)
                )
            
            # 处理没有参数的模块
            module_matches = re.finditer(
                r'module\s+(\w+)\s*\(([^)]*)\)',
                content
            )
            
            for match in module_matches:
                module_name = match.group(1)
                if module_name in self.modules:
                    continue
                
                ports_str = match.group(2)
                ports = self._parse_ports(ports_str)
                
                self.modules[module_name] = ModuleInterface(
                    module_name=module_name,
                    file_path=fpath,
                    inputs=ports['input'],
                    outputs=ports['output'],
                    inouts=ports['inout']
                )
    
    def _parse_ports(self, ports_str: str) -> Dict[str, List[str]]:
        """解析端口列表"""
        import re
        
        result = {'input': [], 'output': [], 'inout': []}
        
        # 分割端口声明
        port_decls = re.findall(r'(input|output|inout)\s+(?:logic\s+)?(?:wire\s+)?(?:reg\s+)?(?: signed)?(?:\[[^\]]+\])?\s*(\w+)', ports_str)
        
        for direction, name in port_decls:
            if direction == 'input':
                result['input'].append(name)
            elif direction == 'output':
                result['output'].append(name)
            elif direction == 'inout':
                result['inout'].append(name)
        
        return result
    
    def _parse_parameters(self, params_str: str) -> List[str]:
        """解析参数列表"""
        import re
        params = re.findall(r'parameter\s+\w+\s+(\w+)', params_str)
        return params
    
    def _analyze_instantiations(self):
        """分析模块实例化关系"""
        import re
        
        for fpath, content in self._parsed_content.items():
            # 查找module实例化
            # 格式: module_name instance_name (...);
            pattern = r'(\w+)\s+(\w+)\s*(?:#\([^)]*\))?\s*\('
            matches = re.finditer(pattern, content)
            
            for match in matches:
                inst_module = match.group(1)
                inst_name = match.group(2)
                
                if inst_module in self.modules:
                    # 记录被谁实例化
                    if fpath not in self.dependencies:
                        self.dependencies[fpath] = FileDependency(file=fpath)
                    
                    self.dependencies[fpath].instantiates.append(inst_module)
                    
                    # 记录实例化它的文件
                    inst_module_file = self.modules[inst_module].file_path
                    if inst_module_file not in self.dependencies:
                        self.dependencies[inst_module_file] = FileDependency(file=inst_module_file)
                    
                    self.dependencies[inst_module_file].instantiated_by.append(fpath)
    
    def _trace_connections(self):
        """追踪模块间的信号连接"""
        import re
        
        for fpath, content in self._parsed_content.items():
            # 查找模块实例化中的信号连接
            # 格式: .port_name(signal_name)
            pattern = r'\.(\w+)\s*\(\s*(\w+)\s*\)'
            matches = re.finditer(pattern, content)
            
            for match in matches:
                port_name = match.group(1)
                signal_name = match.group(2)
                
                # 查找这个信号定义在哪个模块
                src_module = self._find_signal_source(signal_name, fpath)
                if src_module:
                    # 查找这个信号被连接到哪些模块的输入
                    for mod_name, mod_info in self.modules.items():
                        if port_name in mod_info.inputs:
                            self.connections.append(SignalConnection(
                                source_module=src_module,
                                source_signal=signal_name,
                                dest_module=mod_name,
                                dest_signal=port_name,
                                file_path=fpath
                            ))
    
    def _find_signal_source(self, signal: str, current_file: str) -> Optional[str]:
        """查找信号源模块"""
        for mod_name, mod_info in self.modules.items():
            if signal in mod_info.outputs:
                return mod_name
        return None
    
    def _find_cross_file_signals(self):
        """查找跨文件传播的信号"""
        signal_paths: Dict[str, CrossFileSignal] = {}
        
        for conn in self.connections:
            sig_name = conn.source_signal
            
            if sig_name not in signal_paths:
                signal_paths[sig_name] = CrossFileSignal(
                    signal=sig_name,
                    source_module=conn.source_module,
                    source_file=self.modules[conn.source_module].file_path
                )
            
            if conn.dest_module not in signal_paths[sig_name].dest_modules:
                signal_paths[sig_name].dest_modules.append(conn.dest_module)
                signal_paths[sig_name].fanout += 1
        
        # 过滤跨文件的信号
        for sig, info in signal_paths.items():
            if info.source_file != self.modules[info.dest_modules[0]].file_path:
                self.cross_file_signals.append(info)
            elif len(info.dest_modules) > 1:
                self.cross_file_signals.append(info)
    
    def _find_orphan_signals(self):
        """查找孤立信号（定义但未使用）"""
        for mod_name, mod_info in self.modules.items():
            for output_sig in mod_info.outputs:
                used = False
                for conn in self.connections:
                    if conn.source_signal == output_sig and conn.source_module == mod_name:
                        used = True
                        break
                
                if not used:
                    self.orphan_signals.append(f"{mod_name}.{output_sig}")
    
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """获取依赖图"""
        graph = {}
        for fpath, dep in self.dependencies.items():
            graph[os.path.basename(fpath)] = dep.depends_on
        return graph
    
    def find_cycles(self) -> List[List[str]]:
        """检测循环依赖"""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            if node in self.dependencies:
                for dep in self.dependencies[node].depends_on:
                    if dep not in visited:
                        dfs(dep, path[:])
                    elif dep in rec_stack:
                        # 找到环
                        cycle_start = path.index(dep)
                        cycles.append(path[cycle_start:])
            
            rec_stack.remove(node)
        
        for fpath in self.dependencies:
            if fpath not in visited:
                dfs(fpath, [])
        
        return cycles


def analyze_multiple_files(file_paths: List[str]) -> MultiFileReport:
    """分析多个文件的便捷函数"""
    analyzer = MultiFileAnalyzer(file_paths)
    return analyzer.analyze()


__all__ = [
    'MultiFileAnalyzer',
    'MultiFileReport',
    'ModuleInterface',
    'SignalConnection',
    'FileDependency',
    'CrossFileSignal',
    'analyze_multiple_files',
]
