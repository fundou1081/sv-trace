"""Data Path Probabilistic Analyzer

把图论+概率分析应用到RTL数据通路
寻找: 低概率×高影响 的corner case

增强版: 添加解析警告，显式打印不支持的语法结构
"""

import collections
from typing import Dict, List, Set, Tuple, Any

from trace.parse_warn import (
    ParseWarningHandler,
    warn_unsupported,
    warn_error,
    WarningLevel
)


class ProbabilisticDataPathAnalyzer:
    """数据通路概率分析器
    
    增强: 解析过程中显式打印不支持的语法结构
    """
    
    # 节点类型到概率的映射
    TYPE_PROBS = {
        'REGISTER': 0.5,
        'MUX': 0.5,
        'ADD': 0.6,
        'SUB': 0.4,
        'MUL': 0.3,
        'DIV': 0.1,
        'SHIFT': 0.4,
        'CMP': 0.5,
        'SIGNAL': 0.5,
        'FIFO': 0.3,
        'AND': 0.6,
        'OR': 0.6,
        'XOR': 0.5,
        'NOT': 0.5,
    }
    
    def __init__(self, graph, constraints=None, verbose: bool = True):
        self.graph = graph
        self.constraints = constraints or {}
        self.verbose = verbose
        # 创建警告处理器
        self.warn_handler = ParseWarningHandler(
            verbose=verbose,
            component="ProbabilisticDataPathAnalyzer"
        )
        # 估计节点激活概率
        self.node_probs = {}
        self._estimate_probabilities()
    
    def _estimate_probabilities(self):
        """基于节点类型估计激活概率"""
        for name in self.graph.nodes:
            node = self.graph.nodes[name]
            if hasattr(node, 'node_type'):
                node_type = node.node_type
            else:
                node_type = str(node)
            
            self.node_probs[name] = self.TYPE_PROBS.get(node_type, 0.5)
    
    def analyze(self) -> Dict:
        """完整分析"""
        return {
            'rare_scc': self._find_rare_scc(),
            'danger_zones': self._find_danger_zones(),
            'rare_paths': self._find_rare_paths(),
            'critical_rare': self._find_critical_rare(),
            'corner_cases': self._identify_corner_cases(),
        }
    
    def _find_rare_scc(self) -> List[Dict]:
        """找低概率SCC"""
        sccs = self.graph.find_scc()
        rare = []
        
        for scc in sccs:
            prob = 1.0
            for node in scc:
                prob *= self.node_probs.get(node, 0.5)
            
            if prob < 0.1:
                rare.append({
                    'cycle': scc,
                    'joint_prob': round(prob, 4),
                })
        
        return rare[:10]
    
    def _find_danger_zones(self) -> List[Dict]:
        """危险区域"""
        danger = []
        
        for node in self.graph.nodes:
            indeg = self.graph.get_in_degree(node)
            outdeg = self.graph.get_out_degree(node)
            
            # 高扇入+高扇出 = 潜在危险
            if indeg > 5 and outdeg > 5:
                prob = self.node_probs.get(node, 0.5)
                danger.append({
                    'node': node,
                    'in_degree': indeg,
                    'out_degree': outdeg,
                    'probability': prob,
                    'risk_score': round(indeg * outdeg * (1 - prob), 3),
                })
        
        return sorted(danger, key=lambda x: -x['risk_score'])[:10]
    
    def _find_rare_paths(self) -> List[Dict]:
        """找低概率路径"""
        paths = []
        
        # 简单的BFS找所有路径
        for src in self.graph.nodes:
            for dst in self.graph.nodes:
                if src == dst:
                    continue
                
                path_prob = self._calc_path_probability(src, dst)
                if path_prob and path_prob < 0.05:
                    paths.append({
                        'src': src,
                        'dst': dst,
                        'probability': round(path_prob, 4),
                    })
        
        return sorted(paths, key=lambda x: x['probability'])[:10]
    
    def _calc_path_probability(self, src: str, dst: str) -> float:
        """计算路径概率"""
        prob = self.node_probs.get(src, 0.5)
        prob *= self.node_probs.get(dst, 0.5)
        return prob
    
    def _find_critical_rare(self) -> List[Dict]:
        """找关键低概率节点"""
        critical = []
        
        for node in self.graph.nodes:
            prob = self.node_probs.get(node, 0.5)
            
            # 低概率 + 高连接度 = 关键低概率
            if prob < 0.2:
                degree = self.graph.get_in_degree(node) + self.graph.get_out_degree(node)
                if degree > 3:
                    critical.append({
                        'node': node,
                        'probability': prob,
                        'total_degree': degree,
                    })
        
        return sorted(critical, key=lambda x: (x['probability'], -x['total_degree']))[:10]
    
    def _identify_corner_cases(self) -> List[Dict]:
        """识别corner case"""
        cases = []
        
        # 1. 独立节点（无入无出）
        for node in self.graph.nodes:
            indeg = self.graph.get_in_degree(node)
            outdeg = self.graph.get_out_degree(node)
            
            if indeg == 0 and outdeg == 0:
                cases.append({
                    'type': 'isolated',
                    'node': node,
                    'description': '孤立节点，可能未连接',
                })
        
        # 2. 高扇入节点
        for node in self.graph.nodes:
            indeg = self.graph.get_in_degree(node)
            if indeg > 10:
                cases.append({
                    'type': 'high_fanin',
                    'node': node,
                    'description': f'高扇入节点({indeg}个输入)',
                })
        
        # 3. 多路选择器后直接跟寄存器（可能有问题）
        for node in self.graph.nodes:
            if hasattr(self.graph.nodes[node], 'node_type'):
                if self.graph.nodes[node].node_type == 'REGISTER':
                    # 检查前驱
                    predecessors = self.graph.get_predecessors(node)
                    for pred in predecessors:
                        if hasattr(self.graph.nodes.get(pred), 'node_type'):
                            if self.graph.nodes[pred].node_type == 'MUX':
                                cases.append({
                                    'type': 'mux_to_reg',
                                    'nodes': [pred, node],
                                    'description': 'MUX后直接接寄存器，可能有毛刺',
                                })
        
        return cases[:20]
    
    def get_warning_report(self) -> str:
        """获取警告报告"""
        return self.warn_handler.get_report()
    
    def print_warning_report(self):
        """打印警告报告"""
        self.warn_handler.print_report()


class DataPathGraph:
    """数据通路图"""
    
    def __init__(self, verbose: bool = True):
        self.nodes: Dict[str, Any] = {}
        self.edges: List[Tuple[str, str]] = []
        self.adjacency: Dict[str, List[str]] = {}
        self.reverse_adj: Dict[str, List[str]] = {}
        self.verbose = verbose
        self.warn_handler = ParseWarningHandler(
            verbose=verbose,
            component="DataPathGraph"
        )
    
    def add_node(self, name: str, node_type: str = 'SIGNAL', **attrs):
        """添加节点"""
        if name in self.nodes:
            self.warn_handler.warn_info(
                f"节点 {name} 已存在，覆盖",
                context="add_node"
            )
        
        class Node:
            def __init__(self, name, node_type, **kwargs):
                self.name = name
                self.node_type = node_type
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        self.nodes[name] = Node(name, node_type, **attrs)
        if name not in self.adjacency:
            self.adjacency[name] = []
        if name not in self.reverse_adj:
            self.reverse_adj[name] = []
    
    def add_edge(self, src: str, dst: str):
        """添加边"""
        if src not in self.nodes:
            self.warn_handler.warn_unsupported(
                "MissingSource",
                context=f"边 {src} -> {dst}",
                suggestion=f"源节点 {src} 未定义",
                component="DataPathGraph"
            )
            return
        
        if dst not in self.nodes:
            self.warn_handler.warn_unsupported(
                "MissingDestination",
                context=f"边 {src} -> {dst}",
                suggestion=f"目标节点 {dst} 未定义",
                component="DataPathGraph"
            )
            return
        
        self.edges.append((src, dst))
        if src not in self.adjacency:
            self.adjacency[src] = []
        self.adjacency[src].append(dst)
        
        if dst not in self.reverse_adj:
            self.reverse_adj[dst] = []
        self.reverse_adj[dst].append(src)
    
    def get_in_degree(self, node: str) -> int:
        return len(self.reverse_adj.get(node, []))
    
    def get_out_degree(self, node: str) -> int:
        return len(self.adjacency.get(node, []))
    
    def get_predecessors(self, node: str) -> List[str]:
        return self.reverse_adj.get(node, [])
    
    def get_successors(self, node: str) -> List[str]:
        return self.adjacency.get(node, [])
    
    def find_scc(self) -> List[List[str]]:
        """找强连通分量"""
        # Tarjan算法
        index_counter = [0]
        stack = []
        lowlinks = {}
        index = {}
        on_stack = {}
        sccs = []
        
        def strongconnect(node):
            index[node] = index_counter[0]
            lowlinks[node] = index_counter[0]
            index_counter[0] += 1
            stack.append(node)
            on_stack[node] = True
            
            for successor in self.adjacency.get(node, []):
                if successor not in index:
                    strongconnect(successor)
                    lowlinks[node] = min(lowlinks[node], lowlinks[successor])
                elif on_stack.get(successor, False):
                    lowlinks[node] = min(lowlinks[node], index[successor])
            
            if lowlinks[node] == index[node]:
                scc = []
                while True:
                    w = stack.pop()
                    on_stack[w] = False
                    scc.append(w)
                    if w == node:
                        break
                sccs.append(scc)
        
        for node in self.nodes:
            if node not in index:
                strongconnect(node)
        
        return sccs
