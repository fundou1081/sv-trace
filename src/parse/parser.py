"""
SystemVerilog 解析器

增强版: 添加解析警告，显式打印不支持的语法结构和解析异常
"""
import pyslang
import os
from typing import Optional, List, Dict, Any

# 导入解析警告模块
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
try:
    from trace.parse_warn import (
        ParseWarningHandler,
        warn_unsupported,
        warn_error,
        WarningLevel
    )
except ImportError:
    # 备用方案
    class ParseWarningHandler:
        def __init__(self, verbose=True, component="SVParser"):
            self.verbose = verbose
            self.component = component
        def warn_unsupported(self, node_kind, context="", suggestion="", component=None):
            if self.verbose:
                print(f"⚠️ [WARN][{component or self.component}] <{node_kind}> {suggestion} @ {context}")
        def warn_error(self, operation, exc, context="", component=None):
            if self.verbose:
                print(f"❌ [ERROR][{component or self.component}] {operation}: {exc} @ {context}")
        def get_report(self):
            return ""


class SVParser:
    """SystemVerilog 解析器
    
    增强版: 添加解析警告，显式打印不支持的语法结构和解析异常
    """
    
    # 不支持的语法类型
    UNSUPPORTED_TYPES = {
        'CovergroupDeclaration': '覆盖率group不支持',
        'PropertyDeclaration': 'property声明不支持',
        'SequenceDeclaration': 'sequence声明不支持',
        'ClassDeclaration': 'class声明建议使用pyslang_helper提取',
        'InterfaceDeclaration': 'interface声明不支持',
        'PackageDeclaration': 'package声明不支持',
        'ProgramDeclaration': 'program块不支持',
        'ClockingBlock': 'clocking block不支持',
        'ModportItem': 'modport不支持',
        'RandSequenceExpression': 'rand sequence不支持',
    }
    
    def __init__(self, verbose: bool = True):
        self.compilation = pyslang.Compilation()
        self.trees: Dict[str, pyslang.SyntaxTree] = {}
        self.sources: Dict[str, str] = {}  # 保存源代码
        self._parse_cache: Dict[str, Any] = {}
        self._module_cache: Dict[str, Any] = {}  # 模块缓存
        self.verbose = verbose
        # 创建警告处理器
        self.warn_handler = ParseWarningHandler(
            verbose=verbose,
            component="SVParser"
        )
        self._unsupported_encountered = set()
    
    def parse_file(self, filepath: str) -> pyslang.SyntaxTree:
        """解析单个文件"""
        if filepath in self.trees:
            return self.trees[filepath]
        
        try:
            # Read and save source
            with open(filepath) as f:
                source = f.read()
            
            try:
                tree = pyslang.SyntaxTree.fromFile(filepath)
                self.compilation.addSyntaxTree(tree)
                self.trees[filepath] = tree
                self.sources[filepath] = source
                
                # 检查不支持的语法
                self._check_unsupported_syntax(tree, filepath)
                
                return tree
            except Exception as e:
                self.warn_handler.warn_error(
                    "FileParsing",
                    e,
                    context=filepath,
                    component="SVParser"
                )
                raise
        
        except FileNotFoundError:
            self.warn_handler.warn_error(
                "FileNotFound",
                FileNotFoundError(f"File not found: {filepath}"),
                context=filepath,
                component="SVParser"
            )
            raise
        except Exception as e:
            self.warn_handler.warn_error(
                "FileRead",
                e,
                context=filepath,
                component="SVParser"
            )
            raise
    
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
                                component="SVParser"
                            )
                            self._unsupported_encountered.add(kind_name)
                    elif 'Declaration' in kind_name or 'Block' in kind_name:
                        # 记录其他声明类型
                        if kind_name not in self._unsupported_encountered and kind_name not in ['ModuleDeclaration', 'CompilationUnit']:
                            self.warn_handler.warn_unsupported(
                                kind_name,
                                context=source,
                                suggestion="可能影响解析完整性",
                                component="SVParser"
                            )
                            self._unsupported_encountered.add(kind_name)
            except Exception as e:
                self.warn_handler.warn_error(
                    "UnsupportedSyntaxCheck",
                    e,
                    context=f"file={source}",
                    component="SVParser"
                )
    
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
        
        try:
            tree = pyslang.SyntaxTree.fromText(code, filename)
            self.compilation.addSyntaxTree(tree)
            
            # 保存以便后续查询
            self.trees[key] = tree
            self._parse_cache[key] = tree
            
            # 检查不支持的语法
            self._check_unsupported_syntax(tree, filename)
            
            return tree
        except Exception as e:
            self.warn_handler.warn_error(
                "TextParsing",
                e,
                context=filename,
                component="SVParser"
            )
            raise
    
    def parse_files(self, filepaths: List[str]) -> Dict[str, pyslang.SyntaxTree]:
        """批量解析文件"""
        result = {}
        for fp in filepaths:
            try:
                result[fp] = self.parse_file(fp)
            except Exception as e:
                self.warn_handler.warn_error(
                    "BatchFileParsing",
                    e,
                    context=fp,
                    component="SVParser"
                )
        return result
    
    def get_diagnostics(self, filepath: str = None) -> List[str]:
        """获取诊断信息"""
        diags = []
        try:
            all_diags = self.compilation.getAllDiagnostics()
            for d in all_diags:
                diag_str = str(d)
                if filepath:
                    # 尝试过滤特定文件的诊断
                    if filepath in diag_str or '<text>' in diag_str:
                        diags.append(diag_str)
                else:
                    diags.append(diag_str)
        except Exception as e:
            self.warn_handler.warn_error(
                "DiagnosticsRetrieval",
                e,
                context=filepath or "all",
                component="SVParser"
            )
        
        return diags
    
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
            
            try:
                # 检查 root 是否是模块
                if hasattr(tree, 'root') and tree.root:
                    type_name = str(type(tree.root))
                    if 'Module' in type_name:
                        modules.append(tree.root)
            except Exception as e:
                self.warn_handler.warn_error(
                    "ModuleRetrieval",
                    e,
                    context=f"file={filepath}",
                    component="SVParser"
                )
        
        return modules
    
    def get_module_by_name(self, name: str, filepath: str = None) -> Optional[Any]:
        """根据名称查找模块"""
        modules = self.get_modules(filepath)
        for mod in modules:
            try:
                if hasattr(mod, 'header') and mod.header:
                    if hasattr(mod.header, 'name') and mod.header.name:
                        if mod.header.name.value == name:
                            return mod
            except Exception as e:
                self.warn_handler.warn_error(
                    "ModuleNameSearch",
                    e,
                    context=f"name={name}",
                    component="SVParser"
                )
        return None
    
    def get_root(self) -> Any:
        """获取编译根"""
        return self.compilation.getRoot()
    
    def clear_cache(self):
        """清除缓存"""
        self.trees.clear()
        self._parse_cache.clear()
        self._module_cache.clear()
        self.compilation = pyslang.Compilation()
    
    def get_warning_report(self) -> str:
        """获取警告报告"""
        return self.warn_handler.get_report()
    
    def print_warning_report(self):
        """打印警告报告"""
        self.warn_handler.print_report()


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


# =============================================================================
# 扩展语法支持 - 2026-05-01 添加
# =============================================================================

# 添加对更多语法类型的支持
PARSER_EXTENSIONS = {
    # Interface 语法
    'InterfaceDeclaration': {
        'extractor': 'interface',
        'module': 'parse.interface',
        'class': 'InterfaceExtractor',
        'desc': 'Interface/Modport/Clocking 块解析',
    },
    'ModportDeclaration': {
        'extractor': 'interface', 
        'module': 'parse.interface',
        'class': 'InterfaceExtractor',
        'desc': 'Modport 声明解析',
    },
    'ClockingBlock': {
        'extractor': 'clocking',
        'module': 'parse.clocking',
        'class': 'ClockingExtractor',
        'desc': 'Clocking 块解析',
    },
    
    # Package 语法  
    'PackageDeclaration': {
        'extractor': 'package',
        'module': 'parse.package',
        'class': 'PackageExtractor',
        'desc': 'Package 声明解析',
    },
    'PackageImportDeclaration': {
        'extractor': 'package',
        'module': 'parse.package', 
        'class': 'PackageExtractor',
        'desc': 'Import 语句解析',
    },
    
    # Covergroup 语法
    'CovergroupDeclaration': {
        'extractor': 'covergroup',
        'module': 'parse.covergroup',
        'class': 'CovergroupExtractor', 
        'desc': 'Covergroup 解析',
    },
    
    # Program 语法
    'ProgramDeclaration': {
        'extractor': 'program',
        'module': 'parse.program',
        'class': 'ProgramExtractor',
        'desc': 'Program 块解析',
    },
    
    # Property/Sequence 语法
    'PropertyDeclaration': {
        'extractor': 'property',
        'module': 'parse.assertion',
        'class': 'PropertyExtractor',
        'desc': 'Property 声明解析',
    },
    'SequenceDeclaration': {
        'extractor': 'sequence',
        'module': 'parse.assertion',
        'class': 'SequenceExtractor',
        'desc': 'Sequence 声明解析',
    },
}

# 更新 UNSUPPORTED_TYPES 字典，移除已支持的语法
UPDATED_UNSUPPORTED_TYPES = {
    # 这些现在通过 parse 模块支持
    'InterfaceDeclaration': 'Interface/Modport 需要通过 parse.interface 解析',
    'ModportDeclaration': 'Modport 需要通过 parse.interface 解析', 
    'ClockingBlock': 'Clocking 需要通过 parse.clocking 解析',
    'PackageDeclaration': 'Package 需要通过 parse.package 解析',
    'PackageImportDeclaration': 'Import 需要通过 parse.package 解析',
    'CovergroupDeclaration': 'Covergroup 需要通过 parse.covergroup 解析',
    'PropertyDeclaration': 'Property 需要通过 parse.assertion 解析',
    'SequenceDeclaration': 'Sequence 需要通过 parse.assertion 解析',
    # 仍然不支持的
    'ProgramDeclaration': 'Program 块 - 较少使用',
}


# 修改解析器以支持这些语法
def enable_parser_extensions(parser):
    """启用解析器扩展"""
    for kind_name, config in PARSER_EXTENSIONS.items():
        try:
            # 动态导入模块
            mod = __import__(config['module'], fromlist=[config['class']])
            extractor_class = getattr(mod, config['class'])
            # 可以在这里存储提取器实例
            setattr(parser, f"_{config['extractor']}_extractor", extractor_class(parser))
            print(f"  ✅ Enabled: {kind_name}")
        except ImportError as e:
            print(f"  ⚠️  {kind_name}: {e}")
        except Exception as e:
            print(f"  ❌ {kind_name}: {e}")


def get_extended_parser_capabilities(parser):
    """获取扩展解析器能力"""
    return list(PARSER_EXTENSIONS.keys())


# 打印当前支持的状态
print("="*60)
print("解析器扩展能力")
print("="*60)

kind_names = list(PARSER_EXTENSIONS.keys())
for i, name in enumerate(kind_names, 1):
    print(f"  [{i}] {name}")

print(f"\n共 {len(kind_names)} 个语法类型支持")
