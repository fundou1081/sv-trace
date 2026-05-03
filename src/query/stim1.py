"""StimulusPathFinder - Simple - 激励路径追踪器简化版。

简化的激励路径追踪器，用于查找信号的激励来源。

Example:
    >>> from query.stim1 import SPF, find_stim
    >>> from parse import SVParser
    >>> parser = SVParser()
    >>> parser.parse_file("design.sv")
    >>> result = find_stim(parser, "data_out", 0)
"""
import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class IO:
    """IO 信号数据类。
    
    Attributes:
        name: 信号名
        w: 位宽
        r: 关联列表
    """
    name: str
    w: int = 1
    r: List[Tuple] = field(default_factory=list)


@dataclass
class Seg:
    """路径段数据类。
    
    Attributes:
        sig: 信号名
        frm: 来源信号
        op: 操作类型
    """
    sig: str
    frm: str = ""
    op: str = ""


@dataclass
class MA:
    """匹配属性数据类。"""
    pass


@dataclass
class Res:
    """结果数据类。
    
    Attributes:
        target: 目标信号
        value: 目标值
        path: 激励路径
        ios: 相关 IO
        extra: 额外信息
    """
    target: str = ""
    value: int = 0
    path: List = field(default_factory=list)
    ios: List = field(default_factory=list)
    extra: List = field(default_factory=list)


class SPF:
    """Stimulus Path Finder - 激励路径查找器。
    
    追踪信号到其激励源的路径。

    Attributes:
        parser: SVParser 实例
        ios: IO 信号列表
        assigns: 赋值映射
        mems: 存储器列表
    
    Example:
        >>> spf = SPF(parser)
        >>> result = spf.find("data_out", 0)
    """
    
    def __init__(self, p):
        """初始化查找器。
        
        Args:
            p: SVParser 实例
        """
        self.parser = p
        self.ios = []
        self.assigns = {}
        self.mems = []
    
    def find(self, target, value=0):
        """查找激励路径。
        
        Args:
            target: 目标信号名
            value: 目标值
        
        Returns:
            Res: 结果对象
        """
        self.collect_all()
        path = self.trace(target)
        ios = self.calc_ios(path, value)
        return Res(target, value, path, ios, [])
    
    def collect_all(self):
        """收集所有 IO 和赋值关系。"""
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
        """追踪信号源。
        
        Args:
            sig: 信号名
            depth: 递归深度
        
        Returns:
            List[Seg]: 路径段列表
        """
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
        """计算相关 IO。
        
        Args:
            path: 路径段列表
            value: 目标值
        
        Returns:
            List[IO]: 相关 IO 列表
        """
        return self.ios


def find_stim(p, t, v=None):
    """便捷函数：查找激励路径。
    
    Args:
        p: SVParser 实例
        t: 目标信号名
        v: 目标值
    
    Returns:
        Res: 结果对象
    """
    return SPF(p).find(t, v)
