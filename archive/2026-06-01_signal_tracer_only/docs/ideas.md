# SV Trace Ideas - 功能想法池

> 记录待实现的功能想法，按优先级排序

---

## 🔧 中优先级 (已完成 CLI)

### 1. CLI 工具 (已完成 ✅)
- **目标**: 命令行工具 `sv-trace`
- **用法**: 
  - `python cli/main.py analyze <file.sv> -s <signal>`
  - `python cli/main.py signals <file.sv>`
  - `python cli/main.py drivers <file.sv> -s <signal>`
- **状态**: ✅ 完成 (v0.4)

### 2. 参数化模块实例 (已完成 ✅ v0.3.4)
- **目标**: 支持 `#(.ADDR_WIDTH(8))` 参数化实例
- **状态**: ✅ 已完成

---

## ✅ 已完成

- [x] SVParser + pyslang 集成
- [x] DriverTracer (assign + always)
- [x] LoadTracer
- [x] ControlFlowTracer
- [x] DependencyAnalyzer
- [x] BitSelectTracer
- [x] HierarchicalResolver
- [x] SignalFlowAnalyzer (数据流可视化)
- [x] **代码召回 (ScopeExtractor)** - 带行号和截断
- [x] **DataPathAnalyzer** - 数据流深度追踪 (assign + always + if/case + for/while + 流水线)
- [x] **CLI 工具** - 命令行接口

---

## 功能清单

| 功能 | 文件 | 状态 |
|------|------|------|
| 代码解析 | SVParser | ✅ |
| 驱动追踪 | DriverTracer | ✅ |
| 负载追踪 | LoadTracer | ✅ |
| 控制流分析 | ControlFlowTracer | ✅ |
| 依赖分析 | DependencyAnalyzer | ✅ |
| 位选分析 | BitSelectTracer | ✅ |
| 层级解析 | HierarchicalResolver | ✅ |
| 数据流可视化 | SignalFlowAnalyzer | ✅ |
| 代码召回 | ScopeExtractor | ✅ |
| 数据流深度分析 | DataPathAnalyzer | ✅ |
| CLI 工具 | cli/main.py | ✅ |

---

*最后更新: 2026-04-18*

---

## 🚀 v0.4 更新 (2026-04-21)

### UVM Testbench 分析
- **目标**: 提取 UVM testbench 静态结构
- **功能**:
  - UVM 组件识别 (agent/monitor/driver/sequencer/env/scoreboard)
  - TLM 连接提取 (analysis/put/get/transport 端口)
  - Phase 方法提取 (build_phase/connect_phase/run_phase 等)
  - 类继承关系分析
- **测试**: ethernet_10ge_mac (GitHub ⭐ 162)

### ClassExtractor 修复
- 添加 `extract()` 方法
- 属性限定符提取
- 数组维度提取
- Soft/Dist constraint 支持

### 测试结果
- test_class.py: 18/18 通过
- 真实 UVM 项目: 40 classes, 35 components, 6 TLM connections
