"""Data Path Probabilistic Analyzer

把图论+概率分析应用到RTL数据通路
寻找: 低概率×高影响 的corner case
"""

import collections
from typing import Dict, List, Set, Tuple


class ProbabilisticDataPathAnalyzer:
    """数据通路概率分析器"""
    
    def __init__(self, graph, constraints=None):
        self.graph = graph
        self.constraints = constraints or {}
        
        # 估计节点激活概率
        self.node_probs = {}
        self._estimate_probabilities()
    
    def _estimate_probabilities(self):
        """基于节点类型估计激活概率"""
        type_probs = {
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
        }
        
        for name in self.graph.nodes:
            # node could be string or DataPathNode
            node = self.graph.nodes[name]
            if hasattr(node, 'node_type'):
                node_type = node.node_type
            else:
                node_type = str(node)
            
            self.node_probs[name] = type_probs.get(node_type, 0.5)
    
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
            
            if indeg > 1 and outdeg > 1:
                prob = self.node_probs.get(node, 0.5)
                risk = indeg * outdeg * (1 - prob)
                
                if risk > 0.5:
                    danger.append({
                        'node': node,
                        'in': indeg,
                        'out': outdeg,
                        'prob': prob,
                        'risk': round(risk, 3),
                    })
        
        return sorted(danger, key=lambda x: -x['risk'])[:10]
    
    def _find_rare_paths(self) -> List[Dict]:
        return []
    
    def _find_critical_rare(self) -> List[Dict]:
        return []
    
    def _identify_corner_cases(self) -> List[Dict]:
        return []
    
    def get_report(self) -> str:
        results = self.analyze()
        
        lines = ["=" * 50, "RTL DATA PATH ANALYSIS", "=" * 50]
        
        lines.append(f"\nNodes: {len(self.graph.nodes)}")
        lines.append(f"Edges: {len(self.graph.edges)}")
        lines.append(f"SCCs: {len(self.graph.find_scc())}")
        
        return "\n".join(lines)


def analyze_data_path(parser):
    from .extractor import DataPathExtractor
    from .graph import DataPathGraph
    
    extractor = DataPathExtractor(parser)
    edges = extractor.build_edges()
    graph = DataPathGraph(extractor.nodes, edges)
    return ProbabilisticDataPathAnalyzer(graph)
