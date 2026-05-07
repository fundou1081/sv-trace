# SVParser 功能说明

> 基于 pyslang 的 SystemVerilog 解析器

## 核心功能

### 1. 解析接口

| 方法 | 返回 | 功能 |
|------|------|------|
| `parse_file()` | SyntaxTree | 解析单个 .sv 文件 |
| `parse_text()` | SyntaxTree | 解析字符串代码 |
| `parse_files()` | Dict | 批量解析多个文件 |

### 2. 模块查询

| 方法 | 返回 | 功能 |
|------|------|------|
| `get_modules()` | List | 获取文件中的所有模块 |
| `get_module_by_name()` | Module | 按名称查找模块 |
| `get_root()` | SyntaxNode | 获取 AST 根节点 |

### 3. 诊断和错误处理

| 方法 | 返回 | 功能 |
|------|------|------|
| `get_diagnostics()` | List | 获取解析警告 |
| `has_errors()` | bool | 检查是否有错误 |
| `get_warning_report()` | str | 获取警告报告 |

### 4. 缓存管理

| 方法 | 返回 | 功能 |
|------|------|------|
| `clear_cache()` | None | 清空解析缓存 |

---

## 解析增强功能

### 不支持的语法 (10类)

| 语法类型 | 状态 |
|----------|------|
| CovergroupDeclaration | ⚠️ 警告 |
| PropertyDeclaration | ⚠️ 警告 |
| SequenceDeclaration | ⚠️ 警告 |
| ClassDeclaration | ⚠️ 建议用 pyslang_helper |
| InterfaceDeclaration | ⚠️ 警告 |
| PackageDeclaration | ⚠️ 警告 |
| ProgramDeclaration | ⚠️ 警告 |
| ClockingBlock | ⚠️ 警告 |
| ModportItem | ⚠️ 警告 |
| RandSequenceExpression | ⚠️ 警告 |

### 警告级别

- **ERROR**: 解析失败，无法生成 AST
- **WARN**: 语法不支持，但可以继续解析

---

## 使用示例

```python
from parse import SVParser

# 创建解析器
parser = SVParser(verbose=True)

# 解析文件
tree = parser.parse_file('design.sv')

# 获取模块
modules = parser.get_modules('design.sv')
print(f"Found {len(modules)} modules")

# 检查错误
if parser.has_errors('design.sv'):
    diagnostics = parser.get_diagnostics('design.sv')
    for d in diagnostics:
        print(f"Error: {d}")
```

---

## 返回值

`parse_file()` 返回 `pyslang.SyntaxTree`:

```python
tree.root  # SyntaxNode - AST 根节点
tree.text  # str - 源代码
```

---

## 与其他模块的关系

```
SVParser (底层)
    ↓ 返回 SyntaxTree
extractors.py (提取器)
    ↓ 提取
trace/query/ (分析工具)
    ↓ 分析
最终用户结果
```

### 提取器 (extractors.py)

| 提取器 | 功能 |
|--------|------|
| ModuleExtractor | 模块 |
| SignalExtractor | 信号 |
| PortAnalyzer | 端口 |
| InstanceExtractor | 实例 |
| AlwaysBlockExtractor | always块 |

