"""
FuzzyPathMatcher - Hier Path 模糊匹配搜索
用户输入可能不完整的path，搜索最接近的准确path
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class PathCandidate:
    """路径候选"""
    path: str
    score: float = 0.0
    matched_parts: List[str] = field(default_factory=list)
    missing_parts: List[str] = field(default_factory=list)


@dataclass
class FuzzyMatchResult:
    """匹配结果"""
    input_path: str
    candidates: List[PathCandidate] = field(default_factory=list)
    exact_match: bool = False
    
    def visualize(self) -> str:
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
    """Hier Path 模糊匹配"""
    
    def __init__(self, parser):
        self.parser = parser
        self.all_paths = []
        self._collect_all_paths()
    
    def _collect_all_paths(self):
        """收集所有可能的hier path"""
        
        def get_paths(node, prefix=""):
            paths = []
            
            # 收集当前层的ports/signals
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
        
        # 从所有module收集
        for fname, tree in self.parser.trees.items():
            if tree and hasattr(tree, 'root'):
                paths = get_paths(tree.root)
                self.all_paths.extend(paths)
    
    def match(self, input_path: str, top_n: int = 10) -> FuzzyMatchResult:
        """模糊匹配"""
        
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
        
        # 3. 排序并返回top N
        result.candidates.sort(key=lambda c: c.score, reverse=True)
        result.candidates = result.candidates[:top_n]
        
        return result
    
    def _calculate_score(self, input_parts: List[str], path_parts: List[str]) -> Tuple[float, List[str], List[str]]:
        """计算相似度"""
        
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
        """建议纠错"""
        result = self.match(input_path, top_n=5)
        
        suggestions = []
        for c in result.candidates:
            if c.score >= 0.9:
                suggestions.append(c.path)
        
        return suggestions[:3]


def fuzzy_match_path(parser, input_path: str, top_n: int = 10) -> FuzzyMatchResult:
    """便捷函数"""
    matcher = FuzzyPathMatcher(parser)
    return matcher.match(input_path, top_n)
