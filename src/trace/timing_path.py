"""
TimingPathExtractor - 关键时序路径提取器
"""
import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dataclasses import dataclass, field
from typing import List, Set


@dataclass
class TimingPath:
    start: str = ""
    end: str = ""
    depth: int = 0
    signals: List[str] = field(default_factory=list)


@dataclass
class TimingInfo:
    module: str = ""
    paths: List[TimingPath] = field(default_factory=list)
    max_depth: int = 0
    total: int = 0
    critical: str = ""


    def extract_from_text(source: str):
        """从源码文本提取timing路径"""
        try:
            tree = pyslang.SyntaxTree.fromText(source)
            
            class TextParser:
                def __init__(self, tree):
                    self.trees = {"input.sv": tree}
                    self.compilation = tree
            
            return TimingPathExtractor(TextParser(tree))
        except Exception as e:
            print(f"Timing path error: {e}")
            return None

class TimingPathExtractor:
    """工作版本"""
    
    def __init__(self, parser):
        self.parser = parser
        self.graph = {}
        self._build()
    
    def _build(self):
        for fname, tree in self.parser.trees.items():
            if not tree: continue
            try:
                with open(fname) as f: code = f.read()
            except: continue
            
            for m in re.findall(r'assign\s+(\w+)\s*=\s*([^;]+);', code):
                dest, src = m
                srcs = re.findall(r'\b([a-zA-Z_]\w*)\b', src)
                srcs = [s for s in srcs if s != dest]
                self.graph[dest] = [srcs, src]
    
    def analyze(self, m=None) -> TimingInfo:
        info = TimingInfo(module=m or "top")
        
        for dest in self.graph:
            if self._cr(dest): continue
            path, depth = self._trace(dest, set())
            if path and len(path) > 1:
                info.paths.append(TimingPath(start=path[0], end=dest, depth=depth, signals=path))
        
        if info.paths:
            info.total = len(info.paths)
            info.max_depth = max(p.depth for p in info.paths)
            c = max(info.paths, key=lambda x: x.depth)
            info.critical = f"{c.start}->{c.end}({c.depth})"
        
        return info
    
    def _trace(self, sig, visited):
        if sig not in self.graph or sig in visited:
            return [sig], 0
        
        visited.add(sig)
        srcs, expr = self.graph[sig]
        if not srcs: return [sig], 0
        
        mp, md = [sig], 0
        ed = expr.count('+') + expr.count('-') + expr.count('&') + expr.count('|')
        
        for src in srcs:
            sp, sd = self._trace(src, visited.copy())
            td = ed + sd
            if td > md: md = td; mp = sp + [sig]
        
        return mp, md
    
    def _cr(self, s):
        s = s.lower()
        return 'clk' in s or 'rst' in s


def extract_timing_paths(parser, m=None):
    return TimingPathExtractor(parser).analyze(m)
