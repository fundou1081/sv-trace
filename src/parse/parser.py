"""
SystemVerilog 解析器 - 简化版
"""
import pyslang
from typing import Optional, List, Dict, Any
from pathlib import Path


class SVParser:
    """SystemVerilog 解析器"""
    
    def __init__(self):
        self.compilation = pyslang.Compilation()
        self.trees: Dict[str, pyslang.SyntaxTree] = {}
        self._parse_cache: Dict[str, Any] = {}
    
    def parse_file(self, filepath: str) -> pyslang.SyntaxTree:
        """解析单个文件"""
        if filepath in self.trees:
            return self.trees[filepath]
        
        tree = pyslang.SyntaxTree.fromFile(filepath)
        self.compilation.addSyntaxTree(tree)
        self.trees[filepath] = tree
        return tree
    
    def parse_text(self, code: str, filename: str = "<text>") -> pyslang.SyntaxTree:
        """解析代码文本"""
        key = hash(code)
        if key in self._parse_cache:
            return self._parse_cache[key]
        
        tree = pyslang.SyntaxTree.fromText(code, filename)
        self.compilation.addSyntaxTree(tree)
        self._parse_cache[key] = tree
        return tree
    
    def parse_files(self, filepaths: List[str]) -> Dict[str, pyslang.SyntaxTree]:
        """批量解析文件"""
        result = {}
        for fp in filepaths:
            result[fp] = self.parse_file(fp)
        return result
    
    def get_diagnostics(self, filepath: str = None) -> List[str]:
        """获取诊断信息"""
        self.compilation.getAllDiagnostics()
        
        if filepath:
            tree = self.trees.get(filepath)
            if tree:
                return [str(d) for d in tree.diagnostics]
        
        return []
    
    def has_errors(self, filepath: str = None) -> bool:
        """检查是否有解析错误"""
        diags = self.get_diagnostics(filepath)
        return any("error" in d.lower() for d in diags)
    
    def get_modules(self, filepath: str = None) -> List[Any]:
        """获取模块列表"""
        modules = []
        trees = [self.trees[filepath]] if filepath else self.trees.values()
        
        for tree in trees:
            # 遍历 member 查找 module
            def find_modules(node):
                if hasattr(node, 'kind'):
                    # 检查是否是模块（通过字符串匹配）
                    if 'ModuleDeclaration' in str(type(node)):
                        return [node]
                    # 递归查找
                    if hasattr(node, 'members'):
                        result = []
                        for m in node.members:
                            result.extend(find_modules(m))
                        return result
                    if hasattr(node, 'body'):
                        result = []
                        for m in node.body:
                            result.extend(find_modules(m))
                        return result
                return []
            
            modules.extend(find_modules(tree.root))
        
        return modules
    
    def get_module_by_name(self, name: str, filepath: str = None) -> Optional[Any]:
        """根据名称查找模块"""
        modules = self.get_modules(filepath)
        for mod in modules:
            if hasattr(mod, 'header') and mod.header:
                if hasattr(mod.header, 'name') and mod.header.name:
                    if mod.header.name.value == name:
                        return mod
        return None
    
    def get_root(self) -> Any:
        """获取编译根"""
        return self.compilation.getRoot()
    
    def clear_cache(self):
        """清除缓存"""
        self.trees.clear()
        self._parse_cache.clear()
        self.compilation = pyslang.Compilation()
