"""FuzzyPathMatcher - Hier Path 模糊匹配搜索。

用户输入可能不完整的 path，搜索最接近的准确 path。
用于信号路径的智能提示和自动补全。

Example:
    >>> from query.fuzzy_path_matcher import FuzzyPathMatcher
    >>> from parse import SVParser
    >>> parser = SVParser()
    >>> parser.parse_file("design.sv")
    >>> matcher = FuzzyPathMatcher(parser)
    >>> result = matcher.match("top.sub.data")
    >>> print(result.visualize())
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class PathCandidate:
    """路径候选数据类。
    
    Attributes:
        path: 完整路径
        score: 匹配分数 (0-1)
        matched_parts: 匹配的部分
        missing_parts: 缺失的部分
    """
    path: str
    score: float = 0.0
    matched_parts: List[str] = field(default_factory=list)
    missing_parts: List[str] = field(default_factory=list)


@dataclass
class FuzzyMatchResult:
    """模糊匹配结果数据类。
    
    Attributes:
        input_path: 输入路径
        candidates: 候选路径列表
        exact_match: 是否精确匹配
    """
    input_path: str
    candidates: List[PathCandidate] = field(default_factory=list)
    exact_match: bool = False
    
    def visualize(self) -> str:
        """可视化匹配结果。
        
        Returns:
            str: 格式化的报告字符串
        """
        lines = []
        lines.append("=" * 60)
        lines.append(f"Fuzzy Match: {self.input_path}")
        lines.append("=" * 60)
        
        if self.exact_match:
            lines.append("\n✅ Exact match found!")
        
        lines.append(f"\n📋 Top {len(self.candidates)} candidates:")
        
        for i, c in enumerate(self.candidates[:10], 1):
            score_bar = "█" * int(c.score * 10)
            lines.append(f"\n{i}. {c.path}")
            lines.append(f"   {score_bar} {c.score:.2f}")
            if c.matched_parts:
                lines.append(f"   matched: {' -> '.join(c.matched_parts)}")
        
        lines.append("=" * 60)
        return '\n'.join(lines)


class FuzzyPathMatcher:
    """Hier Path 模糊匹配器。
    
    提供层次路径的模糊搜索和自动补全功能。

    Attributes:
        parser: SVParser 实例
        all_paths: 所有已知路径列表
    
    Example:
        >>> matcher = FuzzyPathMatcher(parser)
        >>> result = matcher.match("top.sub.dat")
    """
    
    def __init__(self, parser):
        """初始化匹配器。
        
        Args:
            parser: SVParser 实例
        """
        self.parser = parser
        self.all_paths = []
        self._collect_all_paths()
    
    def _collect_all_paths(self):
        """收集所有可能的 hier path。"""
        def get_paths(node, prefix=""):
            paths = []
            
            # 收集当前层的 ports/signals
            if hasattr(node, 'members') and node.members:
                for m in node.members:
                    if hasattr(m, 'name') and m.name:
                        name = str(m.name)
                        full_path = f"{prefix}.{name}" if prefix else name
                        paths.append(full_path)
                        
                        # 递归向下
                        sub = get_paths(m, full_path)
                        paths.extend(sub)
            
            return paths
        
        # 从所有 module 收集
        for fname, tree in self.parser.trees.items():
            if tree and hasattr(tree, 'root'):
                paths = get_paths(tree.root)
                self.all_paths.extend(paths)
    
    def match(self, input_path: str, top_n: int = 10) -> FuzzyMatchResult:
        """模糊匹配路径。
        
        Args:
            input_path: 输入的部分路径
            top_n: 返回的最多候选数
        
        Returns:
            FuzzyMatchResult: 匹配结果
        """
        result = FuzzyMatchResult(input_path=input_path)
        
        # 1. 检查完全匹配
        if input_path in self.all_paths:
            result.exact_match = True
            result.candidates.append(PathCandidate(
                path=input_path,
                score=1.0,
                matched_parts=[input_path]
            ))
            return result
        
        # 2. 计算每个路径的相似度
        input_parts = input_path.lower().split('.')
        
        for path in self.all_paths:
            path_parts = path.lower().split('.')
            
            # 计算匹配分数
            score, matched, missing = self._calculate_score(
                input_parts, path_parts
            )
            
            if score > 0.3:  # 阈值
                result.candidates.append(PathCandidate(
                    path=path,
                    score=score,
                    matched_parts=matched,
                    missing_parts=missing
                ))
        
        # 3. 排序并返回 top N
        result.candidates.sort(key=lambda c: c.score, reverse=True)
        result.candidates = result.candidates[:top_n]
        
        return result
    
    def _calculate_score(self, input_parts: List[str], path_parts: List[str]) -> Tuple[float, List[str], List[str]]:
        """计算相似度。
        
        Args:
            input_parts: 输入路径的各部分
            path_parts: 候选路径的各部分
        
        Returns:
            Tuple[float, List[str], List[str]]: (分数, 匹配部分, 缺失部分)
        """
        matched = []
        missing = []
        
        if len(input_parts) > len(path_parts):
            return 0.0, [], []
        
        # 前缀匹配
        match_count = 0
        for i, part in enumerate(input_parts):
            if i < len(path_parts):
                if part == path_parts[i]:
                    match_count += 1
                elif part in path_parts[i]:
                    match_count += 0.8
                elif path_parts[i] in part:
                    match_count += 0.5
        
        # 部分匹配检查
        for part in input_parts:
            found = False
            for pp in path_parts:
                if part == pp:
                    matched.append(part)
                    found = True
                    break
                elif part in pp:
                    matched.append(pp)
                    found = True
                    break
            if not found:
                missing.append(part)
        
        # 计算分数
        if match_count == 0:
            return 0.0, [], []
        
        score = match_count / len(input_parts)
        
        return score, matched, missing
    
    def suggest_correction(self, input_path: str) -> List[str]:
        """建议纠错。
        
        Args:
            input_path: 输入路径
        
        Returns:
            List[str]: 可能的正确路径建议
        """
        result = self.match(input_path, top_n=5)
        
        suggestions = []
        for c in result.candidates:
            if c.score >= 0.9:
                suggestions.append(c.path)
        
        return suggestions[:3]


def fuzzy_match_path(parser, input_path: str, top_n: int = 10) -> FuzzyMatchResult:
    """便捷函数：模糊匹配路径。
    
    Args:
        parser: SVParser 实例
        input_path: 输入路径
        top_n: 返回候选数
    
    Returns:
        FuzzyMatchResult: 匹配结果
    """
    matcher = FuzzyPathMatcher(parser)
    return matcher.match(input_path, top_n)
