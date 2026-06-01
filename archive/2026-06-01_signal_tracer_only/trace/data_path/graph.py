"""Data Path Graph"""

import collections
from typing import Dict, List, Set, Tuple


class DataPathGraph:
    def __init__(self, nodes: Dict, edges: List):
        self.nodes = nodes
        try:
            it = iter(edges)
            first = next(it)
            if hasattr(first, 'src'):  # DataPathEdge objects
                self.edges = [(e.src, e.dst, e.edge_type if hasattr(e, 'edge_type') else 'data') for e in edges]
            else:
                self.edges = edges
        except:
            self.edges = edges
        
        self.adj = collections.defaultdict(list)
        self.radj = collections.defaultdict(list)
        self._build_adj()
    
    def _build_adj(self):
        for e in self.edges:
            if len(e) >= 2:
                src, dst = e[0], e[1]
                etype = e[2] if len(e) > 2 else 'data'
                self.adj[src].append((dst, etype))
                self.radj[dst].append((src, etype))
    
    def get_in_degree(self, node):
        return len(self.radj.get(node, []))
    
    def get_out_degree(self, node):
        return len(self.adj.get(node, []))
    
    def find_scc(self):
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
    
    def summary(self):
        return f"Graph: {len(self.nodes)} nodes, {len(self.edges)} edges"
