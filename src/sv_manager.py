"""
SVManager - SystemVerilog 统一管理器
"""
import pyslang
from typing import List, Dict, Optional
from dataclasses import dataclass
import os


@dataclass
class SVFileResult:
    filename: str
    tree: pyslang.SyntaxTree
    source: str
    success: bool
    diagnostics: List[str]
    confidence: str = "high"
    caveats: List[str] = None
    
    def __post_init__(self):
        if self.caveats is None:
            self.caveats = []


class SVManager:
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self._trees: Dict[str, pyslang.SyntaxTree] = {}
        self._sources: Dict[str, str] = {}
        self._errors: Dict[str, List[str]] = {}
    
    @property
    def trees(self) -> Dict[str, pyslang.SyntaxTree]:
        return self._trees
    
    def parse_file(self, filepath: str) -> Optional[SVFileResult]:
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath) as f:
                source = f.read()
            tree = pyslang.SyntaxTree.fromText(source, filepath)
            diagnostics = [str(d) for d in tree.diagnostics]
            errors = [d for d in diagnostics if 'error' in d.lower()]
            
            self._trees[filepath] = tree
            self._sources[filepath] = source
            self._errors[filepath] = diagnostics
            
            return SVFileResult(
                filename=filepath,
                tree=tree,
                source=source,
                success=len(errors) == 0,
                diagnostics=diagnostics,
                confidence="high" if len(errors) == 0 else "medium",
                caveats=errors if errors else []
            )
        except Exception as e:
            return None
    
    def get_line(self, filename: str, line_number: int) -> Optional[str]:
        if filename not in self._sources:
            return None
        lines = self._sources[filename].split('\n')
        if line_number < 1 or line_number > len(lines):
            return None
        return lines[line_number - 1]
    
    def get_lines(self, filename: str, line_number: int, before: int = 0, after: int = 0) -> Dict[int, str]:
        if filename not in self._sources:
            return {}
        lines = self._sources[filename].split('\n')
        n = len(lines)
        start = max(1, line_number - before)
        end = min(n, line_number + after)
        return {i: lines[i - 1] for i in range(start, end + 1)}
    
    def find_keyword(self, filename: str, keyword: str) -> List[Dict]:
        if filename not in self._sources:
            return []
        lines = self._sources[filename].split('\n')
        return [{'line': i, 'content': line.strip()} for i, line in enumerate(lines, 1) if keyword in line]
    
    def __len__(self) -> int:
        return len(self._trees)


__all__ = ['SVManager', 'SVFileResult']
