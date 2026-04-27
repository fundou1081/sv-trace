# SV-Trace 开源项目拆分建议

## ⚠️ 名称冲突说明

GitHub搜索发现以下项目名已被占用：
- `sv-parser` → dalance/sv-parser (Rust语言)
- `svlint` → dalance/svlint (Rust语言)

因此采用以下命名策略，避免冲突：

---

## 最终命名方案

| 原名 | 最终命名 | 说明 |
|------|----------|------|
| sv-parser | **sv-ast** | AST操作工具，与Rust版本区分 |
| svlint | **sv-codecheck** | 代码检查工具 |
| sv-trace | **sv-trace** | 信号追踪（原名可用） |
| sv-verify | **sv-verify** | 验证工具（原名可用） |

---

## 1. 🧬 sv-ast (原sv-parser)

**定位**: Python pyslang封装，提供SystemVerilog AST操作能力

### 包含模块
```
src/parse/
├── parser.py        # SVParser核心
├── assertion.py    # 断言解析
├── constraint.py   # 约束解析
├── covergroup.py  # Coverage解析
├── params.py      # 参数解析
└── extractors.py  # 提取器基类
```

### 用户群体
- EDA工具开发者
- 脚本自动化开发者
- 验证环境构建者

### 安装
```bash
pip install sv-ast
```

---

## 2. 🔍 sv-trace (信号追踪)

**定位**: RTL信号追踪、数据流分析、依赖图构建

### 包含模块
```
src/trace/
├── driver.py           # 驱动追踪
├── load.py            # 负载追踪
├── connection.py      # 连接追踪
├── dataflow.py       # 数据流分析
├── controlflow.py    # 控制流分析
├── dependency.py      # 依赖分析
├── timing_path.py    # 时序路径
├── timing_depth.py   # 时序深度
├── pipeline_analyzer.py  # Pipeline分析
├── cdc_analyzer.py   # CDC分析
├── vcd_analyzer.py   # VCD波形分析
└── performance/     # 性能估算
    ├── performance.py
    ├── power_estimation.py
    ├── resource_estimation.py
    └── throughput_estimation.py
```

### CLI工具
- `sv-trace driver`
- `sv-trace load`
- `sv-trace flow`

### 用户群体
- RTL设计工程师
- 验证工程师
- 架构工程师

### 安装
```bash
pip install sv-ast sv-trace
```

---

## 3. ✅ sv-verify (验证工具集)

**定位**: 验证IP开发支持、约束分析、TB质量评估

### 包含模块
```
src/verify/
├── tb_analyzer/
│   └── complexity.py  # TB复杂度分析(40+指标)
├── constraint/
│   ├── parser_v2.py   # 约束解析+z3冲突检测
│   └── probabilistic.py # 概率分析
├── class_analyzer/
│   ├── extractor.py    # Class提取
│   ├── relation.py     # 类关系
│   ├── hierarchy.py   # 继承链
│   └── usage.py       # 使用分析
├── coverage/
│   ├── model.py        # 覆盖率模型
│   ├── advisor.py      # 覆盖率建议
│   └── generator.py    # 约束生成
└── risk/
    ├── evaluator.py    # 风险评估
    └── test_manager.py # 测试管理
```

### CLI工具
- `sv-verify constraint`  # 约束分析
- `sv-verify tb-quality`   # TB质量
- `sv-verify coverage`    # 覆盖率

### 用户群体
- 验证工程师
- IP开发者
- 项目经理

### 安装
```bash
pip install sv-ast sv-trace sv-verify
```

---

## 4. 📊 sv-codecheck (原svlint)

**定位**: 代码质量检查、Linting、Style检查

### 包含模块
```
src/lint/
├── complexity.py       # 复杂度分析
├── signal_classifier.py # 信号分类
├── naming_checker.py   # 命名规范
├── style_checker.py   # 代码风格
└── suggestions.py     # 优化建议
```

### CLI工具
- `sv-codecheck quality`     # 质量报告
- `sv-codecheck naming`      # 命名检查
- `sv-codecheck style`      # 风格检查

### 用户群体
- 所有工程师
- Code Review自动化

### 安装
```bash
pip install sv-ast sv-codecheck
```

---

## 共享依赖

```toml
# 所有项目的pyproject.toml基础配置
[project]
requires-python = ">=3.11"
dependencies = [
    "pyslang>=10.0",
]

# sv-verify额外依赖
z3-solver>=4.16

# 可视化支持(可选)
graphviz>=0.20
```

---

## Monorepo结构

建议采用Monorepo结构，各自独立发布：

```
sv-trace-org/              # 组织目录
├── sv-ast/              # 项目1: AST操作
├── sv-trace/            # 项目2: RTL追踪  
├── sv-verify/           # 项目3: 验证工具
├── sv-codecheck/         # 项目4: 代码检查
└── README.md            # 主索引
```

每个项目可独立安装：
```bash
pip install sv-ast           # 只用解析器
pip install sv-ast sv-verify  # 解析器+验证
pip install sv-ast sv-trace sv-verify  # 完整安装
```

---

## 与dalance项目的区别

| 特性 | dalance (Rust) | 我们 (Python) |
|------|-----------------|---------------|
| 语言 | Rust | Python |
| 定位 | 底层解析 | 上层应用 |
| API | C FFI | 原生Python |
| 用户 | 嵌入式/C++集成 | 脚本/验证自动化 |

---

## 下一步

1. 确定最终项目数量（可以只发布最成熟的几个）
2. 清理代码和测试
3. 编写每个项目的独立README
4. 配置CI/CD
5. 发布到PyPI

建议优先级：
1. **sv-ast** - 核心基础
2. **sv-verify** - TB分析是强项
3. **sv-trace** - RTL追踪
4. **sv-codecheck** - 可后续发布
