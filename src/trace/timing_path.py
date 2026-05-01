"""
TimingPathExtractor - 关键时序路径提取器

增强版: 添加解析警告，显式打印不支持的语法结构
"""
import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dataclasses import dataclass, field
from typing import List, Set

# 导入解析警告模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from trace.parse_warn import (
    ParseWarningHandler,
    warn_unsupported,
    warn_error,
    WarningLevel
)


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

    def extract_from_text(source: str, verbose: bool = True):
        """从源码文本提取timing路径"""
        try:
            tree = pyslang.SyntaxTree.fromText(source)
            
            class TextParser:
                def __init__(self, tree):
                    self.trees = {"input.sv": tree}
                    self.compilation = tree
            
            return TimingPathExtractor(TextParser(tree), verbose=verbose)
        except Exception as e:
            print(f"Timing path error: {e}")
            return None


class TimingPathExtractor:
    """时序路径提取器
    
    增强: 添加解析警告
    """
    
    # 不支持的语法类型
    UNSUPPORTED_TYPES = {
        'CovergroupDeclaration': 'covergroup不影响时序路径分析',
        'PropertyDeclaration': 'property声明无时序路径',
        'SequenceDeclaration': 'sequence声明无时序路径',
        'ClassDeclaration': 'class内部时序路径分析可能不完整',
        'InterfaceDeclaration': 'interface内部时序路径分析可能不完整',
        'PackageDeclaration': 'package无时序路径',
        'ProgramDeclaration': 'program块时序路径分析可能不完整',
        'ClockingBlock': 'clocking block时序路径分析有限',
    }
    
    def __init__(self, parser, verbose: bool = True):
        self.parser = parser
        self.verbose = verbose
        # 创建警告处理器
        self.warn_handler = ParseWarningHandler(
            verbose=verbose,
            component="TimingPathExtractor"
        )
        self.graph = {}
        self._unsupported_encountered: Set[str] = set()
        self._build()
    
    def _check_unsupported_syntax(self, tree, source: str = ""):
        """检查不支持的语法"""
        if not tree or not hasattr(tree, 'root'):
            return
        
        root = tree.root
        if hasattr(root, 'members') and root.members:
            try:
                members = list(root.members) if hasattr(root.members, '__iter__') else [root.members]
                for member in members:
                    if member is None:
                        continue
                    kind_name = str(member.kind) if hasattr(member, 'kind') else type(member).__name__
                    
                    if kind_name in self.UNSUPPORTED_TYPES:
                        if kind_name not in self._unsupported_encountered:
                            self.warn_handler.warn_unsupported(
                                kind_name,
                                context=source,
                                suggestion=self.UNSUPPORTED_TYPES[kind_name],
                                component="TimingPathExtractor"
                            )
                            self._unsupported_encountered.add(kind_name)
            except Exception as e:
                self.warn_handler.warn_error(
                    "UnsupportedSyntaxCheck",
                    e,
                    context=f"file={source}",
                    component="TimingPathExtractor"
                )
    
    def _build(self):
        for fname, tree in self.parser.trees.items():
            if not tree:
                self.warn_handler.warn_info(
                    f"文件 {fname} 解析树为空",
                    context="TimingPathBuild"
                )
                continue
            
            # 检查不支持的语法
            self._check_unsupported_syntax(tree, fname)
            
            try:
                with open(fname) as f: code = f.read()
            except Exception as e:
                self.warn_handler.warn_error(
                    "FileRead",
                    e,
                    context=f"file={fname}",
                    component="TimingPathExtractor"
                )
                continue
            
            try:
                for m in re.findall(r'assign\s+(\w+)\s*=\s*([^;]+);', code):
                    dest, src = m
                    srcs = re.findall(r'\b([a-zA-Z_]\w*)\b', src)
                    srcs = [s for s in srcs if s != dest]
                    self.graph[dest] = [srcs, src]
            except Exception as e:
                self.warn_handler.warn_error(
                    "GraphBuild",
                    e,
                    context=f"file={fname}",
                    component="TimingPathExtractor"
                )
    
    def analyze(self, m=None) -> TimingInfo:
        info = TimingInfo(module=m or "top")
        
        try:
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
        except Exception as e:
            self.warn_handler.warn_error(
                "TimingAnalysis",
                e,
                context="analyze",
                component="TimingPathExtractor"
            )
        
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
    
    def get_warning_report(self) -> str:
        """获取警告报告"""
        return self.warn_handler.get_report()
    
    def print_warning_report(self):
        """打印警告报告"""
        self.warn_handler.print_report()


def extract_timing_paths(parser, m=None, verbose: bool = True):
    return TimingPathExtractor(parser, verbose=verbose).analyze(m)
