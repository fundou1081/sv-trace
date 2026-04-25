# ADR-019: 解析器源代码保存机制

## 状态
**提议中** (Proposed)

## 决策者
方浩博

## 日期
2026-04-25

## 背景

### 问题描述
边界测试发现 Query Modules (特别是 OverflowRiskDetector) 失败，原因是：
- 解析器使用 `pyslang.SyntaxTree.fromFile()` 解析临时文件
- 解析后仅保存 `SyntaxTree` 对象，不保存原始源代码
- 后续需要源代码的模块 (如文本分析、正则匹配) 无法获取完整代码

### 影响范围
- `OverflowRiskDetector`: 依赖 `_get_code()` 读取源代码进行模式匹配
- 其他可能需要文本分析的模块

### 当前代码
```python
def parse_file(self, filepath: str) -> pyslang.SyntaxTree:
    tree = pyslang.SyntaxTree.fromFile(filepath)
    self.trees[filepath] = tree  # 只保存 SyntaxTree
    return tree
```

## 决策

### 方案选择

#### 方案 A: 在 SyntaxTree 字典中同时保存源代码
```python
class SVParser:
    def __init__(self):
        self.trees: Dict[str, pyslang.SyntaxTree] = {}
        self.sources: Dict[str, str] = {}  # 新增：保存源代码
    
    def parse_file(self, filepath: str) -> pyslang.SyntaxTree:
        with open(filepath) as f:
            source = f.read()
        tree = pyslang.SyntaxTree.fromFile(filepath)
        self.trees[filepath] = tree
        self.sources[filepath] = source  # 保存源代码
        return tree
```
- **优点**: 简单直接，与现有接口兼容
- **缺点**: 内存占用略增 (源代码字符串)

#### 方案 B: 创建 ParserTree 包装类
```python
@dataclass
class ParserTree:
    tree: pyslang.SyntaxTree
    source: str
    filepath: str

class SVParser:
    def __init__(self):
        self.trees: Dict[str, ParserTree] = {}
    
    def parse_file(self, filepath: str) -> ParserTree:
        with open(filepath) as f:
            source = f.read()
        tree = pyslang.SyntaxTree.fromFile(filepath)
        parser_tree = ParserTree(tree=tree, source=source, filepath=filepath)
        self.trees[filepath] = parser_tree
        return parser_tree
```
- **优点**: 封装性好，接口统一
- **缺点**: 需要修改所有调用方

#### 方案 C: 混合方案 - 延迟加载 + 缓存
```python
class SVParser:
    def __init__(self):
        self.trees: Dict[str, pyslang.SyntaxTree] = {}
        self._source_cache: Dict[str, str] = {}
    
    def get_source(self, filepath: str) -> str:
        if filepath in self._source_cache:
            return self._source_cache[filepath]
        try:
            with open(filepath) as f:
                source = f.read()
            self._source_cache[filepath] = source
            return source
        except:
            # 对于临时文件，fallback 到从 tree 重建
            return str(self.trees.get(filepath, ''))
```
- **优点**: 处理临时文件和永久文件
- **缺点**: 复杂度略高

## 选择

**采用方案 A**: 在 SyntaxTree 字典中同时保存源代码

理由：
1. 简单直接，实现成本最低
2. 与现有接口完全兼容
3. 内存占用可接受 (典型的 SystemVerilog 文件几KB-几百KB)
4. 性能开销小 (一次性读取)

## 实现

### 修改 SVParser
```python
class SVParser:
    def __init__(self):
        self.compilation = pyslang.Compilation()
        self.trees: Dict[str, pyslang.SyntaxTree] = {}
        self.sources: Dict[str, str] = {}  # 保存源代码
    
    def parse_file(self, filepath: str) -> pyslang.SyntaxTree:
        if filepath in self.trees:
            return self.trees[filepath]
        
        # 读取源代码
        with open(filepath) as f:
            source = f.read()
        
        # 解析并保存
        tree = pyslang.SyntaxTree.fromFile(filepath)
        self.compilation.addSyntaxTree(tree)
        self.trees[filepath] = tree
        self.sources[filepath] = source
        
        return tree
    
    def get_source(self, filepath: str) -> str:
        """获取源代码"""
        if filepath in self.sources:
            return self.sources[filepath]
        # Fallback: 尝试从 trees 重建
        if filepath in self.trees:
            return str(self.trees[filepath])
        return ""
```

### 修改需要的模块
- `OverflowRiskDetector._get_code()`: 使用 `self.parser.sources.get(fname, '')`
- 其他需要源代码的模块

## 影响

### 正面
- 解决临时文件读取问题
- 提高代码可维护性
- 源代码可用于调试

### 负面
- 内存占用增加 (每个文件额外保存一份源代码)
- 需要同步维护 `sources` 字典

## 引用
- `tests/edge_cases/test_query_edge.py` - 边界测试
- `src/query/overflow_risk_detector.py` - 受影响的模块
