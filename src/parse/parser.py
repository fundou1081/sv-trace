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
        self._parse_cache: Dict[str, Any] = {}
        self._module_cache: Dict[str, Any] = {}  # 模块缓存
    
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


# =============================================================================
# 统一源码访问工具
# =============================================================================

def get_source_safe(parser, filepath: str) -> str:
    """
    安全获取源码的统一方法
    
    尝试多种方式获取源码:
    1. parser.get_source(filepath)
    2. parser.sources.get(filepath)
    3. 直接读取文件
    """
    # 方式1: 使用get_source方法
    if hasattr(parser, 'get_source'):
        source = parser.get_source(filepath)
        if source:
            return source
    
    # 方式2: 直接访问sources字典
    if hasattr(parser, 'sources') and filepath in parser.sources:
        return parser.sources[filepath]
    
    # 方式3: 尝试读取文件
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return f.read()
    except:
        pass
    
    return ""


# 添加为SVParser的方法
SVParser.get_source_safe = lambda self, fp: get_source_safe(self, fp)

__all__ = ['SVParser', 'get_source_safe']


# =============================================================================
# 全局解析缓存 - 提升性能
# =============================================================================

class GlobalParseCache:
    """全局解析缓存"""
    _instance = None
    _cache: Dict[str, pyslang.SyntaxTree] = {}
    _sources: Dict[str, str] = {}
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = GlobalParseCache()
        return cls._instance
    
    def get_tree(self, filepath: str) -> Optional[pyslang.SyntaxTree]:
        return self._cache.get(filepath)
    
    def get_source(self, filepath: str) -> Optional[str]:
        return self._sources.get(filepath)
    
    def set(self, filepath: str, tree: pyslang.SyntaxTree, source: str):
        self._cache[filepath] = tree
        self._sources[filepath] = source
    
    def clear(self):
        self._cache.clear()
        self._sources.clear()
    
    def size(self) -> int:
        return len(self._cache)


# 添加便捷方法
def parse_file_cached(parser, filepath: str) -> pyslang.SyntaxTree:
    """带缓存的文件解析"""
    cache = GlobalParseCache.get_instance()
    
    # 检查缓存
    cached_tree = cache.get_tree(filepath)
    if cached_tree:
        parser.trees[filepath] = cached_tree
        return cached_tree
    
    # 解析并缓存
    tree = parser.parse_file(filepath)
    if tree:
        try:
            with open(filepath, 'r') as f:
                source = f.read()
            cache.set(filepath, tree, source)
        except:
            pass
    
    return tree


# 更新SVParser方法使用缓存
def _parse_file_with_cache(self, filepath: str) -> pyslang.SyntaxTree:
    """解析文件(带缓存)"""
    cache = GlobalParseCache.get_instance()
    
    # 检查缓存
    cached_tree = cache.get_tree(filepath)
    if cached_tree:
        self.trees[filepath] = cached_tree
        if filepath not in self.sources:
            source = cache.get_source(filepath)
            if source:
                self.sources[filepath] = source
        return cached_tree
    
    # 正常解析
    return self.parse_file(filepath)


# 替换方法
SVParser.parse_file_cached = _parse_file_with_cache

__all__ = [
    'SVParser', 
    'get_source_safe', 
    'GlobalParseCache',
    'parse_file_cached'
]
