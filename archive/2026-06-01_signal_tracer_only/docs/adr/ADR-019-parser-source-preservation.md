# ADR-019: 解析器源代码保存机制

## 状态
**已接受** (Accepted)

## 决策者
方浩博

## 日期
2026-04-25

## 背景
边界测试发现 Query Modules (特别是 OverflowRiskDetector) 失败，原因是：
- 解析器使用 `pyslang.SyntaxTree.fromFile()` 解析临时文件
- 解析后仅保存 `SyntaxTree` 对象，不保存原始源代码
- 后续需要源代码的模块 (如文本分析，正则匹配) 无法获取完整代码

## 问题影响
- OverflowRiskDetector: 依赖 `_get_code()` 读取源代码进行模式匹配
- 其他可能需要文本分析的模块

## 解决方案
在 SVParser 中同时保存源代码：

```python
class SVParser:
    def __init__(self):
        self.trees: Dict[str, pyslang.SyntaxTree] = {}
        self.sources: Dict[str, str] = {}  # 保存源代码
    
    def parse_file(self, filepath: str) -> pyslang.SyntaxTree:
        with open(filepath) as f:
            source = f.read()
        tree = pyslang.SyntaxTree.fromFile(filepath)
        self.trees[filepath] = tree
        self.sources[filepath] = source  # 保存源代码
        return tree
    
    def get_source(self, filepath: str) -> str:
        if filepath in self.sources:
            return self.sources[filepath]
        return str(self.trees.get(filepath, ''))
```

## 决策理由
1. 简单直接，实现成本最低
2. 与现有接口完全兼容
3. 内存占用可接受 (典型 SV 文件几KB-几百KB)
4. 性能开销小 (一次性读取)

## 影响
### 正面
- 解决临时文件读取问题
- 提高代码可维护性
- 源代码可用于调试

### 负面
- 内存占用增加 (每个文件额外保存一份源代码)

## 实现模块
- `src/parse/parser.py`: 添加 sources 字典和 get_source() 方法
- `src/query/overflow_risk_detector.py`: 使用 parser.get_source() 替代直接文件读取

## 相关测试
- tests/edge_cases/test_query_edge.py: OverflowRiskDetector 边界测试
