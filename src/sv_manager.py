"""
SVManager - SystemVerilog 统一管理器

统一处理单文件和多文件解析，返回可遍历的 AST

功能:
- 单文件解析
- 多文件解析 (通过 Compilation)
- 缓存管理
- 便捷遍历接口

Example:
    manager = SVManager()
    
    # 单文件
    tree = manager.parse_file('design.sv')
    
    # 多文件
    manager.parse_files(['a.sv', 'b.sv', 'top.sv'])
    
    # 遍历
    for fname, tree in manager.trees.items():
        tree.root.visit(visitor)
"""

import pyslang
from typing import List, Dict, Optional
from dataclasses import dataclass
import os


@dataclass
class SVFileResult:
    """单文件解析结果"""
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
    """SystemVerilog 统一管理器"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self._trees: Dict[str, pyslang.SyntaxTree] = {}
        self._sources: Dict[str, str] = {}
        self._errors: Dict[str, List[str]] = {}
    
    @property
    def trees(self) -> Dict[str, pyslang.SyntaxTree]:
        """返回解析结果缓存"""
        return self._trees
    
    def parse_file(self, filepath: str) -> Optional[SVFileResult]:
        """解析单个文件
        
        Args:
            filepath: SV 文件路径
            
        Returns:
            SVFileResult: 解析结果
        """
        if not os.path.exists(filepath):
            if self.verbose:
                print(f"[ERROR] File not found: {filepath}")
            return None
        
        try:
            # 读取源码
            with open(filepath) as f:
                source = f.read()
            
            # 解析
            tree = pyslang.SyntaxTree.fromText(source, filepath)
            
            # 检查诊断
            diagnostics = [str(d) for d in tree.diagnostics]
            errors = [d for d in diagnostics if 'error' in d.lower()]
            
            # 缓存结果
            self._trees[filepath] = tree
            self._sources[filepath] = source
            self._errors[filepath] = diagnostics
            
            # 构建结果
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
            if self.verbose:
                print(f"[ERROR] Parse failed: {filepath} - {e}")
            return SVFileResult(
                filename=filepath,
                tree=None,
                source="",
                success=False,
                diagnostics=[str(e)],
                confidence="uncertain",
                caveats=[str(e)]
            )
    
    def parse_files(self, filepaths: List[str]) -> Dict[str, SVFileResult]:
        """批量解析多个文件
        
        Args:
            filepaths: SV 文件路径列表
            
        Returns:
            Dict[filename, SVFileResult]
        """
        results = {}
        
        for fp in filepaths:
            result = self.parse_file(fp)
            if result:
                results[fp] = result
        
        return results
    
    def parse_directory(self, dirpath: str, pattern: str = "*.sv") -> Dict[str, SVFileResult]:
        """解析目录下所有 SV 文件
        
        Args:
            dirpath: 目录路径
            pattern: 文件匹配模式
            
        Returns:
            Dict[filename, SVFileResult]
        """
        # 简单实现，实际可用 glob
        files = []
        for f in os.listdir(dirpath):
            if f.endswith('.sv'):
                files.append(os.path.join(dirpath, f))
        
        return self.parse_files(files)
    
    def get_tree(self, filename: str) -> Optional[pyslang.SyntaxTree]:
        """获取已解析的语法树
        
        Args:
            filename: 文件路径
            
        Returns:
            SyntaxTree 或 None
        """
        return self._trees.get(filename)
    
    def get_diagnostics(self, filename: str = None) -> Dict[str, List[str]]:
        """获取诊断信息
        
        Args:
            filename: 指定文件，或 None 获取所有
            
        Returns:
            Dict[filename, diagnostics]
        """
        if filename:
            return {filename: self._errors.get(filename, [])}
        return self._errors
    
    def has_errors(self, filename: str = None) -> bool:
        """检查是否有错误
        
        Args:
            filename: 指定文件，或 None 检查所有
            
        Returns:
            bool
        """
        if filename:
            errors = self._errors.get(filename, [])
            return any('error' in e.lower() for e in errors)
        
        # 检查所有文件
        for errors in self._errors.values():
            if any('error' in e.lower() for e in errors):
                return True
        return False
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self._trees.clear()
        self._sources.clear()
        self._errors.clear()
        if self.verbose:
            print("[INFO] Cache cleared")
    
    def get_module_names(self, filename: str = None) -> List[str]:
        """获取模块名列表
        
        Args:
            filename: 指定文件，或 None 获取所有
            
        Returns:
            List[str]: 模块名列表
        """
        module_names = []
        
        trees = self._trees.items() if not filename else [(filename, self._trees.get(filename))]
        
        for fname, tree in trees:
            if not tree:
                continue
            
            def visitor(node):
                from pyslang import SyntaxKind
                if node.kind == SyntaxKind.ModuleDeclaration:
                    try:
                        name = str(node.header.name)
                        module_names.append(name)
                    except:
                        pass
                return pyslang.VisitAction.Advance
            
            tree.root.visit(visitor)
        
        return module_names
    
    def __len__(self) -> int:
        """返回已解析文件数"""
        return len(self._trees)
    
    def __repr__(self) -> str:
        return f"SVManager(files={len(self._trees)}, errors={self.has_errors()})"


# 便捷函数
def parse_sv(filepath: str, verbose: bool = True) -> Optional[pyslang.SyntaxTree]:
    """快速解析单个文件
    
    Args:
        filepath: SV 文件路径
        verbose: 是否打印信息
        
    Returns:
        SyntaxTree 或 None
    """
    manager = SVManager(verbose=verbose)
    result = manager.parse_file(filepath)
    return result.tree if result else None


def parse_sv_files(filepaths: List[str], verbose: bool = True) -> Dict[str, pyslang.SyntaxTree]:
    """快速解析多个文件
    
    Args:
        filepaths: 文件路径列表
        verbose: 是否打印信息
        
    Returns:
        Dict[filename, SyntaxTree]
    """
    manager = SVManager(verbose=verbose)
    manager.parse_files(filepaths)
    return manager.trees


__all__ = ['SVManager', 'SVFileResult', 'parse_sv', 'parse_sv_files']
