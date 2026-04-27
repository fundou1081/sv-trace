# SV-Trace 开源项目拆分建议

## 背景

当前项目包含40+模块、9个CLI工具、20+Skills，功能涵盖：
- SystemVerilog解析
- RTL信号追踪
- 验证约束分析
- TB质量评估
- 时序/CDC分析

## 建议：拆分为4个独立开源项目

---

## 1. 🧬 sv-parser (核心解析库)

**定位**: Python pyslang封装，提供SystemVerilog解析能力

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
pip install sv-parser
```

---

## 2. 🔍 sv-trace (RTL追踪分析)

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
pip install sv-parser sv-trace
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
- `sv-verify tb-quality`  # TB质量
- `sv-verify coverage`   # 覆盖率

### 用户群体
- 验证工程师
- IP开发者
- 项目经理

### 安装
```bash
pip install sv-parser sv-verify
```

---

## 4. 📊 sv-lint (代码质量工具)

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
- `sv-lint quality`     # 质量报告
- `sv-lint naming`      # 命名检查
- `sv-lint style`      # 风格检查

### 用户群体
- 所有工程师
- Code Review自动化

### 安装
```bash
pip install sv-lint
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

## 拆分后的目录结构

```
sv-trace/                    # 当前项目 -> Archive/过渡
├── sv-parser/              # 新项目1
├── sv-trace-rtl/           # 新项目2  
├── sv-verify/              # 新项目3
├── sv-lint/                # 新项目4
└── README_SPLIT.md         # 本文档
```

---

## 迁移策略

### Phase 1: 拆分sv-parser
```bash
mkdir sv-parser && mv src/parse sv-parser/
```

### Phase 2: 拆分sv-trace
```bash
mkdir sv-trace-rtl && mv src/trace sv-trace-rtl/
```

### Phase 3: 拆分sv-verify
```bash
mkdir sv-verify && mv src/verify sv-verify/
mv src/debug/constraint* sv-verify/
mv src/debug/class* sv-verify/
```

### Phase 4: 拆分sv-lint
```bash
mkdir sv-lint && mv src/debug/complexity.py sv-lint/
mv src/debug/signal* sv-lint/
```

---

## 推荐: 保持单仓库，分成多个子包

考虑到：
1. 模块间有依赖关系
2. 用户可能需要完整工具链
3. 版本同步简单

**建议**: 采用Monorepo结构，发布多个子包

```toml
# sv-parser/pyproject.toml
[project]
name = "sv-parser"

# sv-trace/pyproject.toml
[project]
name = "sv-trace"
dependencies = ["sv-parser"]

# sv-verify/pyproject.toml
[project]
name = "sv-verify"
dependencies = ["sv-parser", "sv-trace", "z3-solver"]
```

---

## 总结

| 方案 | 优点 | 缺点 |
|------|------|------|
| **拆成4个项目** | 职责清晰、独立使用 | 依赖管理复杂 |
| **Monorepo多包** | 版本同步、灵活组合 | 仓库较大 |
| **保持现状** | 最简单 | 功能混杂 |

**推荐**: 采用Monorepo方案，分成4个独立发布的Python子包
