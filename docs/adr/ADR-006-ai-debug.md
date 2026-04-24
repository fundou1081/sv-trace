# ADR-006: AI Debug Workflow Enhancement

> **状态**: In Progress
> **日期**: 2026-04-19
> **版本**: v0.2

---

## 背景

在芯片验证工作中，RTL debug 是一项耗时且重复的工作。AI Agent 的出现可以显著提升效率。

---

## 现有功能 vs 规划场景 对照表

### 已具备 ✅ (可复用)

| 场景 | 需要功能 | 现有工具 | 复用度 |
|------|----------|----------|--------|
| 1. 信号追踪 | 驱动查找 | `DriverTracer.find_driver()` | ✅ 100% |
| 1. 信号追踪 | 代码片段 | `CodeExtractor` | ✅ 100% |
| 1. 信号追踪 | 负载查找 | `LoadTracer.find_load()` | ✅ 100% |
| 2. 数据流 | 数据流追踪 | `DataFlowTracer.find_flow()` | ✅ 100% |
| 2. 数据流 | 深度分析 | `DataPathAnalyzer` | ✅ 100% |
| 2. 数据流 | 可视化 | `visualize_datapath()` | ✅ 100% |
| 4. 批量检查 | 未使用信号 | `SVLinter.check_unused_signals()` | ✅ 100% |
| 4. 批量检查 | 多驱动检测 | `SVLinter.check_multiple_drivers()` | ✅ 100% |
| 4. 批量检查 | 常量信号 | `SVLinter.check_constant_signals()` | ✅ 100% |
| 4. 批量检查 | 未初始化 | `SVLinter.check_uninitialized_registers()` | ✅ 100% |
| 5. 跨模块追踪 | 层级解析 | `HierarchicalResolver` | ✅ 100% |
| 5. 跨模块追踪 | 模块连接 | `ConnectionTracer` | ✅ 100% |
| 6. 控制流分析 | 控制流追踪 | `ControlFlowTracer` | ✅ 100% |
| 6. 控制流分析 | 依赖分析 | `DependencyAnalyzer` | ✅ 100% |
| 6. 控制流分析 | 可视化 | `visualize_controlflow()` | ✅ 100% |

### 需要增强 🔶

| 场景 | 需要功能 | 现有工具 | 增强内容 | 优先级 |
|------|----------|----------|----------|--------|
| 3. 问题诊断 | X值检测 | `SVLinter` | 新增 XValueDetector | P1 |
| 3. 问题诊断 | 未初始化精确检测 | `SVLinter` | 增强条件分析 | P1 |
| 4. 批量检查 | 悬空端口检测 | `ConnectionTracer` | 新增 check_dangling_ports() | P1 |
| 7. 时钟域 | 时钟域分析 | 无 | 新增 ClockDomainAnalyzer | P2 |
| 7. 时钟域 | CDC 检测 | 无 | 新增 CDCAnalyzer | P2 |
| 8. 报告生成 | HTML报告 | LintReport | 新增 ReportGenerator | P2 |

### 缺失需新增 🆕

| 场景 | 需要功能 | 说明 | 优先级 |
|------|----------|------|--------|
| 1-6 | DebugAssistant 入口 | 自然语言 → 工具调用 | P0 |
| 3 | 根因分析器 | 症状 → 原因推理 | P1 |
| 7 | 时序约束分析 | 时序约束追踪 | P3 |

---

## 架构评估与建议

### 当前架构优势

1. **模块化设计好** - Trace/Parse/Query 分离，可独立使用
2. **工具齐全** - DriverTracer, LoadTracer, DataFlowTracer 等已经很完善
3. **Lint 基础好** - SVLinter 已实现 4 种基本检查

### 需要改进的点

| 问题 | 建议 |
|------|------|
| 1. 工具分散 | 创建 DebugAssistant 统一入口，包装现有工具 |
| 2. 返回格式不统一 | 统一各种 tracer 的返回格式，便于组合使用 |
| 3. 缺少时钟域信息 | ConnectionTracer 可增加 clock/reset 信息 |
| 4. 报告能力弱 | LintReport 可扩展为通用 ReportGenerator |

### 扩展建议

```python
# 建议的 DebugAssistant 架构

src/
├── debug/                    # 新增 DebugAssistant 模块
│   ├── __init__.py
│   ├── assistant.py          # 主入口
│   ├── analyzers/
│   │   ├── xvalue.py         # X值检测 (新)
│   │   ├── cdc.py            # CDC分析 (新)
│   │   ├── clock_domain.py   # 时钟域分析 (新)
│   │   └── root_cause.py     # 根因分析 (新)
│   └── reports/
│       ├── generator.py      # 报告生成 (新)
│       └── templates/         # HTML模板
│
├── trace/
│   └── enhanced/
│       └── clock_info.py     # 增强: 时钟域信息
│
└── lint/
    └── enhanced/
        └── port_check.py     # 增强: 悬空端口检测
```

---

## 实现计划 (修订)

### Phase 1: DebugAssistant 统一入口 (v0.4.0)
- [ ] 创建 `src/debug/` 模块
- [ ] DebugAssistant 类，包装现有工具
- [ ] 场景 1: 信号追踪 (自然语言接口)
- [ ] 场景 2: 数据流分析
- [ ] 场景 5: 跨模块追踪

### Phase 2: 问题诊断增强 (v0.4.1)
- [ ] XValueDetector (基于 SVLinter 增强)
- [ ] 增强未初始化检测
- [ ] 根因分析器 (场景 3)
- [ ] 悬空端口检测

### Phase 3: 时钟域分析 (v0.4.2)
- [ ] ClockDomainAnalyzer (场景 7)
- [ ] CDCAnalyzer (场景 7)
- [ ] 控制流增强

### Phase 4: 报告增强 (v0.5.0)
- [ ] ReportGenerator (场景 8)
- [ ] HTML 报告
- [ ] Markdown 报告
- [ ] 可交互式报告

---

## 关键决策

1. **优先实现 DebugAssistant 入口** - 现有工具已经很完善，缺的是统一入口
2. **复用 SVLinter** - 不重造轮子，在现有基础上增强
3. **渐进式增强** - 不追求一步到位，逐步添加功能

---

*最后更新: 2026-04-19*
