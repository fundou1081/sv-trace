"""
SVManager - SystemVerilog 统一管理器
"""
import pyslang
from typing import List, Dict, Optional
from dataclasses import dataclass
import os


@dataclass
class SVResult:
    tree: Optional[pyslang.SyntaxTree]
    filename: str
    source: str
    success: bool
    confidence: str
    diagnostics: List[str]
    error_count: int = 0
    warning_count: int = 0
    caveats: List[str] = None


class SVManager:
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self._trees = {}
        self._results = {}
    
    @property
    def trees(self):
        return {f: r.tree for f, r in self._results.items() if r.success}
    
    def _offset_to_line(self, source, offset):
        line = 1
        for i in range(min(offset, len(source))):
            if source[i] == '\n':
                line += 1
        return line
    
    def _find_all_line_numbers(self, n, source, depth=0):
        lines = []
        if depth > 20:
            return lines
        try:
            if hasattr(n, 'location') and n.location:
                line = self._offset_to_line(source, n.location.offset)
                if line not in lines:
                    lines.append(line)
            for c in n:
                lines.extend(self._find_all_line_numbers(c, source, depth+1))
        except:
            pass
        return lines
    
    def parse_file(self, filepath):
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath) as f:
                source = f.read()
            tree = pyslang.SyntaxTree.fromText(source, filepath)
            diagnostics = [str(d) for d in tree.diagnostics]
            ec = sum(1 for d in diagnostics if 'error' in d.lower())
            wc = sum(1 for d in diagnostics if 'warning' in d.lower())
            conf = "uncertain" if ec else ("medium" if wc else "high")
            result = SVResult(
                tree=tree if ec == 0 else None,
                filename=filepath,
                source=source,
                success=ec == 0,
                confidence=conf,
                diagnostics=diagnostics,
                error_count=ec,
                warning_count=wc,
                caveats=[f"Found {ec} errors" if ec else ""]
            )
            if ec == 0: self._trees[filepath] = tree
            self._results[filepath] = result
            return result
        except Exception as e:
            result = SVResult(tree=None, filename=filepath, source="", success=False,
                confidence="uncertain", diagnostics=[str(e)], error_count=1, caveats=[str(e)])
            self._results[filepath] = result
            return result
    
    def parse_files(self, filepaths):
        return {fp: self.parse_file(fp) for fp in filepaths}
    
    @property
    def results(self):
        return self._results
    
    def get_result(self, filepath):
        return self._results.get(filepath)
    
    def get_line(self, filename, line_number):
        result = self._results.get(filename)
        if not result: return None
        lines = result.source.split('\n')
        return lines[line_number - 1] if 1 <= line_number <= len(lines) else None
    
    def get_lines(self, filename, line, before=0, after=0):
        result = self._results.get(filename)
        if not result: return {}
        lines = result.source.split('\n')
        start, end = max(1, line - before), min(len(lines), line + after)
        return {i: lines[i-1] for i in range(start, end + 1)}
    
    def get_scope_source(self, filename, node, max_lines=50):
        result = self._results.get(filename)
        if not result or not result.source:
            return None
        source = result.source
        
        # 查找节点的所有行号
        line_nums = self._find_all_line_numbers(node, source)
        if not line_nums:
            return None
        
        start_line = min(line_nums)
        end_line = min(max(line_nums), start_line + max_lines)
        
        if start_line < 1 or end_line > len(source.split('\n')):
            return None
        
        scope = {i: source.split('\n')[i-1] for i in range(start_line, end_line + 1)}
        
        return {'start': start_line, 'end': end_line, 'lines': scope}
    
    def get_failed_files(self):
        return [f for f, r in self._results.items() if not r.success]
    
    def get_successful_files(self):
        return [f for f, r in self._results.items() if r.success]
    
    def clear_cache(self):
        self._trees.clear()
        self._results.clear()
    
    def __len__(self):
        return len(self._results)


__all__ = ['SVManager', 'SVResult']
