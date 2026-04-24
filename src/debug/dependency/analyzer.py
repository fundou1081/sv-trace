"""
ModuleDependencyAnalyzer - 模块依赖分析 (Option A: 实例化追溯)
"""
import sys
import os
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))


@dataclass
class InstanceInfo:
    """实例信息"""
    instance_name: str
    module_type: str
    parameters: Dict[str, str] = field(default_factory=dict)
    port_connections: Dict[str, str] = field(default_factory=dict)


@dataclass
class ModuleDependency:
    """模块依赖信息"""
    module_name: str
    instances: List[InstanceInfo] = field(default_factory=list)
    depended_by: List[str] = field(default_factory=list)  # 依赖此模块的模块
    depends_on: List[str] = field(default_factory=list)  # 此模块依赖的模块


@dataclass
class DependencyGraph:
    """依赖图"""
    modules: Dict[str, ModuleDependency] = field(default_factory=dict)
    cycles: List[List[str]] = field(default_factory=list)
    root_modules: List[str] = field(default_factory=list)
    leaf_modules: List[str] = field(default_factory=list)


class ModuleDependencyAnalyzer:
    """模块依赖分析器"""
    
    def __init__(self, parser):
        self.parser = parser
        self.graph = DependencyGraph()
    
    def analyze(self) -> DependencyGraph:
        """分析模块依赖"""
        self._collect_instances()
        self._build_dependencies()
        self._detect_cycles()
        self._find_roots_and_leaves()
        return self.graph
    
    def _collect_instances(self):
        """收集模块实例化信息"""
        for tree in self.parser.trees.values():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            root = tree.root
            if not hasattr(root, 'members'):
                continue
            
            current_module = None
            
            for i in range(len(root.members)):
                member = root.members[i]
                
                if 'ModuleDeclaration' in str(type(member)):
                    current_module = self._get_module_name(member)
                    if current_module and current_module not in self.graph.modules:
                        self.graph.modules[current_module] = ModuleDependency(module_name=current_module)
                    
                    if hasattr(member, 'members') and member.members:
                        self._find_instantiations(member.members, current_module)
    
    def _get_module_name(self, module) -> str:
        """获取模块名"""
        if hasattr(module, 'header') and module.header:
            if hasattr(module.header, 'name'):
                name = module.header.name
                if hasattr(name, 'value'):
                    return name.value
                return str(name)
        return ""
    
    def _find_instantiations(self, members, module_name: str):
        """在成员列表中查找实例化"""
        if not module_name:
            return
        
        for i in range(len(members)):
            stmt = members[i]
            
            if 'HierarchyInstantiation' in str(type(stmt)):
                module_type = ""
                if hasattr(stmt, 'type') and stmt.type:
                    module_type = str(stmt.type).strip()
                # 移除注释
                import re
                module_type = re.sub(r'//.*', '', module_type).strip()
                
                if hasattr(stmt, 'instances') and stmt.instances:
                    try:
                        for j in range(len(stmt.instances)):
                            inst = stmt.instances[j]
                            
                            instance_name = ""
                            if hasattr(inst, 'decl') and inst.decl:
                                decl = inst.decl
                                if hasattr(decl, 'name'):
                                    instance_name = str(decl.name).strip()
                            
                            params = {}
                            if hasattr(stmt, 'parameters') and stmt.parameters:
                                try:
                                    params = self._extract_inst_parameters(stmt.parameters)
                                except:
                                    pass
                            
                            if instance_name and module_type:
                                info = InstanceInfo(
                                    instance_name=instance_name,
                                    module_type=module_type,
                                    parameters=params
                                )
                                
                                if hasattr(inst, 'connections') and inst.connections:
                                    info.port_connections = self._extract_connections(inst.connections)
                                
                                self.graph.modules[module_name].instances.append(info)
                                
                                if module_type not in self.graph.modules:
                                    self.graph.modules[module_type] = ModuleDependency(module_name=module_type)
                    
                    except Exception as e:
                        pass
    
    def _extract_inst_parameters(self, params) -> Dict[str, str]:
        """提取实例化参数"""
        result = {}
        try:
            actual_params = params.parameters if hasattr(params, 'parameters') else params
            
            for i in range(len(actual_params)):
                p = actual_params[i]
                if hasattr(p, 'name') and hasattr(p, 'expr'):
                    name = str(p.name).strip()
                    value = str(p.expr) if hasattr(p, 'expr') else ''
                    result[name] = value
        except:
            pass
        return result

    def _extract_connections(self, conns) -> Dict[str, str]:
        """提取端口连接"""
        result = {}
        try:
            for i in range(len(conns)):
                c = conns[i]
                port = str(getattr(c, 'port', '')).strip()
                expr = str(getattr(c, 'expression', '')).strip()
                if port:
                    result[port] = expr
        except:
            pass
        return result
    
    def _build_dependencies(self):
        """构建依赖关系"""
        for module_name, mod_dep in self.graph.modules.items():
            for inst in mod_dep.instances:
                if inst.module_type and inst.module_type != module_name:
                    if inst.module_type not in mod_dep.depends_on:
                        mod_dep.depends_on.append(inst.module_type)
                    
                    if module_name not in self.graph.modules[inst.module_type].depended_by:
                        self.graph.modules[inst.module_type].depended_by.append(module_name)
    
    def _detect_cycles(self):
        """检测循环依赖"""
        self.graph.cycles = []
        
        visited = set()
        rec_stack = set()
        
        def dfs(module, path):
            visited.add(module)
            rec_stack.add(module)
            path.append(module)
            
            if module in self.graph.modules:
                for dep in self.graph.modules[module].depends_on:
                    if dep not in visited:
                        dfs(dep, path.copy())
                    elif dep in rec_stack:
                        cycle_start = path.index(dep)
                        cycle = path[cycle_start:] + [dep]
                        if cycle not in self.graph.cycles:
                            self.graph.cycles.append(cycle)
            
            rec_stack.remove(module)
        
        for module in self.graph.modules:
            if module not in visited:
                dfs(module, [])
    
    def _find_roots_and_leaves(self):
        """找出根模块和叶子模块"""
        self.graph.root_modules = []
        self.graph.leaf_modules = []
        
        for module_name, mod_dep in self.graph.modules.items():
            if not mod_dep.depended_by:
                self.graph.root_modules.append(module_name)
            
            if not mod_dep.depends_on:
                self.graph.leaf_modules.append(module_name)
    
    def get_dependency_tree(self, module_name: str, depth: int = 0, max_depth: int = 3) -> List[tuple]:
        """获取依赖树"""
        result = []
        
        if depth > max_depth:
            return result
        
        if module_name in self.graph.modules:
            result.append((module_name, depth))
            for dep in self.graph.modules[module_name].depends_on:
                result.extend(self.get_dependency_tree(dep, depth + 1, max_depth))
        
        return result
    
    def visualize_tree(self, module_name: str = None, max_depth: int = 3) -> str:
        """生成依赖树文本图"""
        if not module_name:
            if self.graph.root_modules:
                module_name = self.graph.root_modules[0]
            else:
                return "No root modules found"
        
        lines = [f"Dependency Tree for: {module_name}", "=" * 50]
        
        tree = self.get_dependency_tree(module_name, 0, max_depth)
        for mod, depth in tree:
            indent = "  " * depth
            lines.append(f"{indent}{mod}")
        
        return "\n".join(lines)
    
    def to_dot(self, name: str = "module_deps") -> str:
        """生成 DOT 格式依赖图"""
        lines = [
            f'digraph {name} {{',
            '  rankdir=LR;',
            '  node [fontname="Arial", shape=box];',
            '  edge [fontname="Arial"];',
            '',
        ]
        
        # 根节点样式
        for mod in self.graph.root_modules:
            lines.append(f'  "{mod}" [style=filled, fillcolor="#90EE90"];')
        
        # 叶子节点样式
        for mod in self.graph.leaf_modules:
            if mod not in self.graph.root_modules:
                lines.append(f'  "{mod}" [style=filled, fillcolor="#FFB6C1"];')
        
        # 循环依赖样式
        cycle_nodes = set()
        for cycle in self.graph.cycles:
            cycle_nodes.update(cycle)
        for mod in cycle_nodes:
            lines.append(f'  "{mod}" [style=filled, fillcolor="#FFD700"];')
        
        lines.append("")
        
        # 边
        for module_name, mod_dep in self.graph.modules.items():
            for dep in mod_dep.depends_on:
                lines.append(f'  "{module_name}" -> "{dep}";')
        
        lines.append("}")
        return "\n".join(lines)
    
    def to_mermaid(self) -> str:
        """生成 Mermaid 格式依赖图"""
        lines = ["flowchart LR", ""]
        
        lines.append("    %% Styles")
        lines.append("    classDef root fill:#90EE90,stroke:#333;")
        lines.append("    classDef leaf fill:#FFB6C1,stroke:#333;")
        lines.append("    classDef cycle fill:#FFD700,stroke:#333;")
        lines.append("")
        
        for mod in self.graph.root_modules:
            lines.append(f'    {mod}:::root')
        for mod in self.graph.leaf_modules:
            if mod not in self.graph.root_modules:
                lines.append(f'    {mod}:::leaf')
        for mod in set().union(*self.graph.cycles) if self.graph.cycles else []:
            lines.append(f'    {mod}:::cycle')
        
        lines.append("")
        
        for module_name, mod_dep in self.graph.modules.items():
            for dep in mod_dep.depends_on:
                lines.append(f'    {module_name} --> {dep}')
        
        return "\n".join(lines)
    
    def visualize(self) -> str:
        """生成可视化报告"""
        lines = ["=" * 60]
        lines.append("MODULE DEPENDENCY ANALYSIS")
        lines.append("=" * 60)
        
        lines.append(f"\n📊 Statistics:")
        lines.append(f"  Total modules: {len(self.graph.modules)}")
        lines.append(f"  Root modules (top-level): {len(self.graph.root_modules)}")
        lines.append(f"  Leaf modules (no children): {len(self.graph.leaf_modules)}")
        lines.append(f"  Cycles detected: {len(self.graph.cycles)}")
        
        if self.graph.root_modules:
            lines.append(f"\n🌳 Root Modules ({len(self.graph.root_modules)}):")
            for mod in sorted(self.graph.root_modules):
                inst_count = len(self.graph.modules.get(mod, ModuleDependency(mod)).instances)
                lines.append(f"  • {mod} ({inst_count} instances)")
        
        if self.graph.leaf_modules:
            lines.append(f"\n🍃 Leaf Modules ({len(self.graph.leaf_modules)}):")
            for mod in sorted(self.graph.leaf_modules)[:10]:
                lines.append(f"  • {mod}")
            if len(self.graph.leaf_modules) > 10:
                lines.append(f"  ... and {len(self.graph.leaf_modules) - 10} more")
        
        if self.graph.cycles:
            lines.append(f"\n⚠️  Cycles Detected ({len(self.graph.cycles)}):")
            for i, cycle in enumerate(self.graph.cycles):
                lines.append(f"  Cycle {i+1}: {' -> '.join(cycle)}")
        
        lines.append(f"\n📦 Module Dependencies:")
        for mod in sorted(self.graph.modules.keys())[:15]:
            mod_dep = self.graph.modules[mod]
            deps = mod_dep.depends_on
            if deps:
                lines.append(f"  {mod} --> {', '.join(deps)}")
        
        return "\n".join(lines)
    
    def save_dot(self, filepath: str):
        """保存为 .dot 文件"""
        with open(filepath, 'w') as f:
            f.write(self.to_dot())
        print(f"DOT saved to: {filepath}")
    
    def render_image(self, output_path: str, format: str = "png"):
        """渲染图片（需要 graphviz）"""
        import subprocess
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
            f.write(self.to_dot())
            dot_file = f.name
        
        try:
            result = subprocess.run(
                ['dot', '-T', format, '-o', output_path, dot_file],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"Image saved to: {output_path}")
            else:
                print(f"Graphviz not available: {result.stderr}")
        finally:
            os.unlink(dot_file)


    def get_complexity_score(self) -> Dict:
        """计算模块依赖复杂度评分"""
        score = 0
        factors = []
        
        # 1. 模块数量因子
        mod_count = len(self.graph.modules)
        mod_score = min(mod_count * 2, 20)
        score += mod_score
        factors.append(f"模块数量: {mod_count} -> +{mod_score}")
        
        # 2. 循环依赖惩罚
        cycle_count = len(self.graph.cycles)
        cycle_penalty = cycle_count * 10
        score += cycle_penalty
        factors.append(f"循环依赖: {cycle_count} -> +{cycle_penalty} (惩罚)")
        
        # 3. 最大依赖深度
        max_depth = self._get_max_depth()
        depth_score = max_depth * 3
        score += depth_score
        factors.append(f"最大深度: {max_depth} -> +{depth_score}")
        
        # 4. 根模块数量
        root_count = len(self.graph.root_modules)
        root_score = root_count * 2
        score += root_score
        factors.append(f"顶层模块: {root_count} -> +{root_score}")
        
        # 5. 依赖边数量
        edge_count = sum(len(m.depends_on) for m in self.graph.modules.values())
        edge_score = edge_count
        score += edge_score
        factors.append(f"依赖边数: {edge_count} -> +{edge_score}")
        
        # 评分等级
        if score < 15:
            grade = "A"
            desc = "简单"
        elif score < 30:
            grade = "B"
            desc = "中等"
        elif score < 50:
            grade = "C"
            desc = "复杂"
        else:
            grade = "D"
            desc = "很复杂"
        
        return {
            "total_score": score,
            "grade": grade,
            "description": desc,
            "factors": factors,
            "metrics": {
                "module_count": mod_count,
                "cycle_count": cycle_count,
                "max_depth": max_depth,
                "root_count": root_count,
                "edge_count": edge_count
            }
        }
    
    def _get_max_depth(self) -> int:
        """计算最大依赖深度"""
        max_depth = 0
        
        def get_depth(module, visited=None):
            nonlocal max_depth
            if visited is None:
                visited = set()
            if module in visited:
                return 0
            visited.add(module)
            
            if module not in self.graph.modules:
                return 0
            
            deps = self.graph.modules[module].depends_on
            if not deps:
                return 1
            
            max_d = 0
            for dep in deps:
                d = get_depth(dep, visited.copy())
                max_d = max(max_d, d)
            
            return 1 + max_d
        
        for mod in self.graph.modules:
            d = get_depth(mod)
            max_depth = max(max_depth, d)
        
        return max_depth
    
    def get_fan_in_out(self) -> Dict[str, Dict]:
        """计算每个模块的 Fan-in 和 Fan-out"""
        result = {}
        
        for mod_name, mod_dep in self.graph.modules.items():
            fan_out = len(mod_dep.depends_on)
            fan_in = len(mod_dep.depended_by)
            
            result[mod_name] = {
                "fan_in": fan_in,
                "fan_out": fan_out,
                "total": fan_in + fan_out,
                "depends_on": mod_dep.depends_on,
                "depended_by": mod_dep.depended_by
            }
        
        return result
    
    def visualize_depth(self, max_depth: int = 5) -> str:
        """生成层次深度可视化"""
        lines = ["=" * 60]
        lines.append("MODULE HIERARCHY DEPTH")
        lines.append("=" * 60)
        
        levels = {i: [] for i in range(max_depth + 1)}
        
        def assign_level(module, level, visited=None):
            if visited is None:
                visited = set()
            if level > max_depth or module in visited:
                return
            visited.add(module)
            
            if module in self.graph.modules:
                levels[level].append(module)
                for dep in self.graph.modules[module].depends_on:
                    assign_level(dep, level + 1, visited.copy())
        
        for root in self.graph.root_modules:
            assign_level(root, 0)
        
        for level, mods in levels.items():
            if mods:
                lines.append(f"\n📍 Level {level}:")
                for mod in sorted(set(mods)):
                    deps = self.graph.modules.get(mod, ModuleDependency(mod))
                    child_count = len(deps.depends_on)
                    lines.append(f"  {'  ' * level}└─ {mod} ({child_count} children)")
        
        return "\n".join(lines)
    
    def get_full_report(self) -> str:
        """生成完整评估报告"""
        lines = []
        
        lines.append(self.visualize())
        lines.append("")
        
        lines.append("=" * 60)
        lines.append("COMPLEXITY SCORE")
        lines.append("=" * 60)
        score = self.get_complexity_score()
        lines.append(f"\n🎯 Score: {score['total_score']} ({score['grade']} - {score['description']})")
        lines.append("\nFactors:")
        for f in score['factors']:
            lines.append(f"  • {f}")
        
        lines.append("\n" + "=" * 60)
        lines.append("FAN-IN / FAN-OUT")
        lines.append("=" * 60)
        fio = self.get_fan_in_out()
        for mod, data in sorted(fio.items(), key=lambda x: x[1]['total'], reverse=True):
            lines.append(f"\n{mod}:")
            lines.append(f"  Fan-in:  {data['fan_in']}")
            lines.append(f"  Fan-out: {data['fan_out']}")
            if data['depends_on']:
                lines.append(f"  → depends: {', '.join(data['depends_on'])}")
            if data['depended_by']:
                lines.append(f"  ← depended by: {', '.join(data['depended_by'])}")
        
        lines.append("\n" + self.visualize_depth())
        
        return "\n".join(lines)


def analyze_dependencies(parser) -> DependencyGraph:
    """便捷函数"""
    return ModuleDependencyAnalyzer(parser).analyze()
