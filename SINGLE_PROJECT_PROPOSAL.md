# SV-Trace 单项目发布方案

## 方案：作为单一PyPI项目发布

### 项目信息

| 项目名 | 版本 | 说明 |
|--------|------|------|
| **sv-trace** | 0.1.0 | SystemVerilog静态分析工具库 |

### 安装

```bash
pip install sv-trace
```

### 包含子库

| 子库 | 说明 |
|------|------|
| `sv_trace.ast` | AST解析 (原sv-ast) |
| `sv_trace.trace` | RTL追踪 (原sv-trace) |
| `sv_trace.verify` | 验证工具 (原sv-verify) |
| `sv_trace.lint` | 代码检查 (原sv-codecheck) |

### 使用示例

```python
# 完整导入
import sv_trace

# 单独导入
from sv_trace import ast, trace, verify, lint

# AST解析
from sv_trace.ast import SVParser

# 验证工具
from sv_trace.verify import TBComplexityAnalyzer

# RTL追踪
from sv_trace.trace import DriverTracer
```

---

## 项目结构

```
sv-trace/
├── src/
│   └── sv_trace/
│       ├── __init__.py
│       ├── ast/           # AST解析
│       │   ├── __init__.py
│       │   └── parser.py
│       ├── trace/         # RTL追踪
│       │   ├── __init__.py
│       │   ├── driver.py
│       │   └── ...
│       ├── verify/        # 验证工具
│       │   ├── __init__.py
│       │   ├── tb_analyzer/
│       │   └── constraint/
│       └── lint/         # 代码检查
│           ├── __init__.py
│           └── ...
├── bin/                  # CLI工具
│   ├── sv-constraint
│   ├── sv-tb-complexity
│   └── ...
├── pyproject.toml
└── README.md
```

---

## pyproject.toml 配置

```toml
[project]
name = "sv-trace"
version = "0.1.0"
description = "SystemVerilog static analysis library"
authors = [
    {name = "Your Name", email = "your@email.com"}
]
license = {text = "MIT"}
requires-python = ">=3.11"
dependencies = [
    "pyslang>=10.0",
    "z3-solver>=4.16",
    "graphviz>=0.20",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
]

[project.scripts]
sv-trace = "sv_trace.cli:main"
sv-constraint = "sv_trace.verify.cli.constraint:main"
sv-tb-complexity = "sv_trace.verify.cli.tb_complexity:main"

[build-system]
requires = ["setuptools>=65.0", "wheel"]
build-backend = "setuptools.build_meta"
```

---

## CLI安装后可用

```bash
# 核心工具
sv-constraint        # 约束分析
sv-constraint-prob   # 约束概率分析
sv-tb-complexity    # TB复杂度分析
sv-datapath         # 数据通路分析
sv-quality          # 代码质量
sv-signal          # 信号分类
```

---

## 与拆分方案对比

| 特性 | 单项目 | 拆分4项目 |
|------|--------|----------|
| 仓库数量 | 1 | 4 |
| 安装命令 | `pip install sv-trace` | 需安装多个包 |
| 版本同步 | 简单 | 需协调 |
| 依赖管理 | 统一 | 各自管理 |
| 用户选择 | 完整安装 | 按需安装 |

---

## 结论

**推荐采用单项目方案**，理由：
1. **更简单**: 只需维护一个仓库
2. **版本同步**: 所有子库版本一致
3. **用户友好**: 一行命令安装全部功能
4. **灵活性**: 用户可通过 `from sv_trace import xxx` 选择性使用

后续如需拆分，可将单项目拆分为多个仓库，并保持API兼容性。
