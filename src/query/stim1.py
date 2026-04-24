"""StimulusPathFinder - Simple"""
import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from dataclasses import dataclass, field
from typing import List, Tuple

@dataclass class IO: name: str; w: int=1; r: List[Tuple] = field(default_factory=list)
@dataclass class Seg: sig: str; frm: str=""; op: str=""
@dataclass class MA: 
@dataclass class Res: 

class SPF:
    def __init__(self, p):
        self.parser = p
        self.ios = []
        self.assigns = {}
        self.mems = []
    
    def find(self, target, value=0):
        self.collect_all()
        path = self.trace(target)
        ios = self.calc_ios(path, value)
        return Res(target, value, path, ios, [])
    
    def collect_all(self):
        for f in self.parser.trees:
            c = getattr(self.parser.trees[f], 'source', '')
            if not c:
                try: c = open(f).read()
                except: continue
            
            for l in c.split('\n'):
                l = l.strip()
                if l.startswith('input'):
                    m = re.search(r'(?:\[(\d+):\d+\])?(\w+)', l)
                    if m:
                        w = int(m.group(1)) + 1 if m.group(1) else 1
                        self.ios.append(IO(m.group(2), w))
                
                if 'always' in l or 'assign' in l:
                    m = re.search(r'(\w+)\s*<=(.+)', l)
                    if m:
                        self.assigns[m.group(1).strip()] = m.group(2).strip()
                
                if 'reg' in l and '[' in l:
                    m = re.search(r'reg.*?(\w+)\s*\[', l)
                    if m and 'mem' not in l.lower():
                        self.mems.append(m.group(1))
    
    def trace(self, sig, depth=0):
        if depth > 15 or sig in self.assigns: return []
        segs = []
        if sig in self.assigns:
            e = self.assigns[sig]
            s = Seg(sig)
            s.op = 'add' if '+' in e else 'sub' if '-' in e else 'case'
            for x in re.findall(r'\w+', e):
                if x != sig:
                    s.frm = x
                    segs.extend(self.trace(x, depth+1))
            segs.append(s)
        return segs
    
    def calc_ios(self, path, value):
        return self.ios

def find_stim(p, t, v=None): return SPF(p).find(t,v)
