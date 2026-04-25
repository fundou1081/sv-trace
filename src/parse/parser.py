"""
SystemVerilog 解析器
"""
import pyslang
from typing import Optional, List, Dict, Any


class SVParser:
    """SystemVerilog 解析器"""
    
    def __init__(self):
        self.compilation = pyslang.Compilation()
        self.trees: Dict[str, pyslang.SyntaxTree] = {}
        self.sources: Dict[str, str] = {}  # 保存源代码
        self.sources: Dict[str, str] = {}  # 保存源代码
        self._parse_cache: Dict[str, Any] = {}
    
    def parse_file(self, filepath: str) -> pyslang.SyntaxTree:
        """解析单个文件"""
        if filepath in self.trees:
            return self.trees[filepath]
        
        # Read and save source
        with open(filepath) as f:
            source = f.read()
        
        tree = pyslang.SyntaxTree.fromFile(filepath)
        self.compilation.addSyntaxTree(tree)
        self.trees[filepath] = tree
        self.sources[filepath] = source
        return tree
    
    def get_source(self, filepath: str) -> str:
        """Get saved source code"""
        if filepath in self.sources:
            return self.sources[filepath]
        if filepath in self.trees:
            return str(self.trees[filepath])
        return ""
    
    def parse_text(self, code: str, filename: str = "<text>") -> pyslang.SyntaxTree:
        """解析代码文本"""
        key = hash(code)
        if key in self._parse_cache:
            return self._parse_cache[key]
        
        tree = pyslang.SyntaxTree.fromText(code, filename)
        self.compilation.addSyntaxTree(tree)
        
        # 保存以便后续查询
        self.trees[key] = tree
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
        
        if filepath:
            trees = [self.trees.get(filepath)]
        else:
            trees = list(self.trees.values())
        
        for tree in trees:
            if not tree:
                continue
            
            # 检查 root 是否是模块
            if hasattr(tree, 'root') and tree.root:
                type_name = str(type(tree.root))
                if 'Module' in type_name:
                    modules.append(tree.root)
        
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
