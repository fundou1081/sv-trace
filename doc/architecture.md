# SV-TRACE 架构文档

## 1. 模块结构

```
sv-trace/
├── parse/          # SystemVerilog解析器 (pyslang)
├── trace/         # 静态分析核心模块
│   ├── driver.py      # 驱动分析
│   ├── load.py       # 负载分析
│   ├── dependency.py # 依赖分析
│   ├── dataflow.py   # 数据流分析
│   ├── controlflow.py# 控制流分析
│   ├── bitselect.py  # 位选择分析
│   ├── timing_*.py  # 时序分析
│   ├── performance_*.py # 性能分析
│   ├── area_estimator.py # 面积估算
│   ├── power_estimator.py # 功耗估算
│   └── reports/     # 报告生成
└── debug/
    └── analyzers/   # 诊断分析工具
        ├── cdc_analyzer.py
        ├── coverage_analyzer.py
        ├── testability_analyzer.py
        ├── timing_analyzer.py
        ├── fsm_analyzer.py
        ├── code_metrics_analyzer.py
        └── project_analyzer.py
```

## 2. 核心依赖关系

### 2.1 依赖层次

```
parse (pyslang)
    ↓
trace (核心分析) ← dependency: driver, load, dataflow, controlflow
    ↓
analyzers (诊断工具) ← dependency: trace, parse
```

### 2.2 关键模块调用链

| 分析器 | 调用的trace模块 |
|--------|-------------|
| CDCAnalyzer | DriverCollector, ControlFlowTracer |
| CoverageAnalyzer | DriverCollector |
| TestabilityAnalyzer | DriverCollector, LoadTracer |
| TimingAnalyzer | DriverCollector |
| ProjectAnalyzer | CodeMetricsAnalyzer |

### 2.3 Trace核心模块

| 模块 | 功能 | 依赖 |
|------|------|------|
| DriverCollector | 收集信号驱动 | parse |
| LoadTracer | 收集信号负载 | parse |
| DependencyGraph | 依赖关系 | - |
| DataFlowTracer | 数据流分析 | - |
| ControlFlowTracer | 控制流分析 | - |
| BitselectTracer | 位选择分析 | - |

## 3. 分析工具矩阵

### 3.1 质量分析

| 工具 | 功能 | 依赖模块 |
|------|------|---------|
| CodeQualityScorer | 代码质量评分 | parse |
| CodeMetricsAnalyzer | 代码度量 | 正则 |
| MultiDriverDetector | 多驱动检测 | DriverCollector |
| CDCAnalyzer | CDC问题 | DriverCollector |

### 3.2 覆盖率分析

| 工具 | 功能 |
|------|------|
| CoverageAnalyzer | 行/分支/条件/FSM覆盖 |

### 3.3 可测试性分析

| 工具 | 功能 |
|------|------|
| TestabilityAnalyzer | 可控性/可观测性/扫描链 |

### 3.4 性能分析

| 工具 | 功能 |
|------|------|
| TimingAnalyzer | 关键路径/Fmax |
| PerformanceEstimator | 性能估算 |
| AreaEstimator | 面积估算 |
| PowerEstimator | 功耗估算 |

### 3.5 项目分析

| 工具 | 功能 |
|------|------|
| ProjectAnalyzer | 批量模块分析 (pyslang) |
| StaticAnalyzer | 纯静态分析 (正则) |

## 4. 实现版本对比

### 4.1 分析器实现

| 工具 | 实现方式 | 准确性 | 速度 |
|------|--------|--------|------|
| StaticAnalyzer | 纯正则 | 基础 | 快 |
| ProjectAnalyzer | pyslang | 精确 | 较慢 |

### 4.2 指标计算

- **静态指标**: 直接计数 (行数、信号数、运算符数)
- **结构指标**: 解析AST (always_ff, if, case)
- **分析指标**: 追踪算法 (依赖关系、数据流)

## 5. 下一步建议

### 5.1 高优先级

- [ ] FSM状态机深度分析
- [ ] CDC多时钟域检测
- [ ] 复位完整性检查
- [ ] 跨时钟域分析 (Timed Path)

### 5.2 中优先级

- [ ] 覆盖率与仿真集成
- [ ] 形式验证接口
- [ ] UVM生成

### 5.3 工具增强

- [ ] 信号统计增强 (更精确的fanin/fanout)
- [ ] 多文件联合分析
- [ ] 报告HTML输出

### 5.4 架构改进

- [ ] 统一报告格式
- [ ] 插件系统
- [ ] 配置管理

