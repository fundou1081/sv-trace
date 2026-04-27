"""Data Path Graph

构建数据通路有向图并进行结构分析
"""

import collections
from typing import Dict, List, Set, Tuple, Optional


class DataPathGraph:
    """数据通路图"""
    
    def __init__(self, nodes: Dict, edges: List):
        self.nodes = nodes  # Dict[name] = node_type
        self.edges = edges  # List[(src, dst, edge_type)]
        
        # 构建邻接表
        self.adj = collections.defaultdict(list)
        self.radj = collections.defaultdict(list)
        self._build_adjacency()
    
    def _build_adjacency(self):
        for src, dst, etype in self.edges:
            self.adj[src].append((dst, etype))
            self.radj[dst].append((src, etype))
    
    def get_in_degree(self, node: str) -> int:
        return len(self.radj.get(node, []))
    
    def get_out_degree(self, node: str) -> int:
        return len(self.adj.get(node, []))
    
    def find_scc(self) -> List[List[str]]:
        """找强连通分量 - 循环路径"""
        index = {}
        low = {}
        on_stack = {}
        stack = []
        sccs = []
        counter = [0]
        
        def dfs(v):
            index[v] = low[v] = counter[0]
            counter[0] += 1
            stack.append(v)
            on_stack[v] = True
            
            for w, _ in self.adj.get(v, []):
                if w not in index:
                    dfs(w)
                    low[v] = min(low[v], low[w])
                elif on_stack.get(w, False):
                    low[v] = min(low[v], index[w])
            
            if low[v] == index[v]:
                scc = []
                while True:
                    w = stack.pop()
                    on_stack[w] = False
                    scc.append(w)
                    if w == v:
                        break
                if len(scc) > 1:
                    sccs.append(scc)
        
        for node in self.nodes:
            if node not in index:
                dfs(node)
        
        return sccs
    
    def find_path(self, start: str, end: str, max_len: int = 10) -> List[List[str]]:
        """找路径"""
        if start not in self.nodes or end not in self.nodes:
            return []
        
        paths = []
        visited = set()
        
        def dfs(curr, path):
            if len(path) > max_len:
                return
            if curr == end:
                paths.append(path.copy())
                return
            
            visited.add(curr)
            for next_node, _ in self.adj.get(curr, []):
                if next_node not in visited:
                    path.append(next_node)
                    dfs(next_node, path)
                    path.pop()
            visited.remove(curr)
        
        dfs(start, [start])
        return paths
    
    def get_critical_nodes(self, top_k: int = 10) -> List[Tuple[str, int]]:
        """找关键节点 - 高介数中心性(被依赖最多)"""
        in_degrees = [(n, self.get_in_degree(n)) for n in self.nodes]
        return sorted(in_degrees, key=lambda x: -x[1])[:top_k]
    
    def get_longest_path(self) -> List[str]:
        """找最长路径（无环情况下）"""
        # 简化版 - DFS找最长路径
        longest = []
        
        def dfs(node, path, visited):
            nonlocal longest
            if len(path) > len(longest):
                longest = path.copy()
            
            visited.add(node)
            for next_node, _ in self.adj.get(node, []):
                if next_node not in visited:
                    dfs(next_node, path + [next_node], visited.copy())
        
        for start in self.nodes:
            dfs(start, [start], set())
        
        return longest
    
    def summary(self) -> str:
        """返回图摘要"""
        sccs = self.find_scc()
        critical = self.get_critical_nodes()
        
        lines = ["DataPath Graph Summary", "=" * 40]
        lines.append(f"  Nodes: {len(self.nodes)}")
        lines.append(f"  Edges: {len(self.edges)}")
        lines.append(f"  SCCs: {len(sccs)}")
        lines.append(f"  Critical nodes: {critical[:5]}")
        return "\n".join(lines)
