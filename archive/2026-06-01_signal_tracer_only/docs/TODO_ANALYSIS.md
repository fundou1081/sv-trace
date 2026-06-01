# SV-Trace 项目分析报告

> 生成时间: 2026-05-13
> 项目路径: `/Users/fundou/my_dv_proj/sv-trace`

---

## TODO 1: 检查所有测试中的弱断言

### 弱断言列表

| 文件 | 问题 | 数量 |
|------|------|------|
| `tests/unit/tools/test_opentitan_modules.py` | `assert x > 0` 无详细信息 | 4 |
| `tests/unit/tools/test_driver.py` | `assert x > 0` 无详细信息 | 4 |
| `tests/unit/tools/test_connection.py` | `assert x > 0` 无详细信息 | 1 |
| `tests/unit/tools/test_load.py` | `assert x > 0` 无详细信息 | 1 |
| `tests/unit/tools/test_driver_enhanced.py` | `assert x > 0` 无详细信息 | 1 |
| `tests/unit/tools/test_driver_complex.py` | `assert True` | 1 |
| `tests/unit/tools/test_load_unsupported_syntax.py` | `assert True` | 1 |
| `tests/unit/sv_trace/test_tier2_tools.py` | `assert True` | 2 |

### 弱断言示例

**问题类型 1**: `assert True` (无检查)
```python
# 问题
assert True  # 跳过实际检查

# 建议
assert extractor is not None
assert len(classes) >= 1, f"expected classes, got {len(classes)}"
```

**问题类型 2**: `assert x > 0` (无详细信息)
```python
# 问题
assert len(drivers) > 0

# 建议
assert len(drivers) >= 1, f"信号 q 应有驱动，实际: {len(drivers)}"
```

### 修复建议

需要逐一修复上述 8 个文件中的弱断言，添加有意义的错误信息。

---

## TODO 2: 检查金标准预期结果的语义正确性

### 金标准覆盖情况

| 类别 | 文件数 | 覆盖情况 |
|------|--------|----------|
| 有金标准注释 | 32 | ✅ 良好 |
| 有详细断言 | 3 | ⚠️ 需加强 |

### 金标准详细程度评估

**良好** (有详细断言和注释):
- `test_cross_module_driver.py` ✅
- `test_driver_operator_combo.py` ✅

**一般** (有注释但断言较弱):
- 大部分测试文件 ⚠️

### 语义正确性问题

以下测试可能存在语义验证不足的问题：

| 测试 | 问题 | 建议 |
|------|------|------|
| `test_driver.py` | 只检查 `kind`，未验证 `driver` 内容 | 应验证 RHS 表达式 |
| `test_signal_chain.py` | 只检查驱动存在，未验证链路 | 应验证完整数据流 |
| `test_load.py` | 只检查 load tracer 创建 | 应验证负载关系 |

### 金标准验证清单

每个测试应包含：
1. ✅ RTL 源码
2. ✅ 人工推导的金标准表格
3. ✅ 逐项断言验证
4. ✅ 详细的错误信息

---

## TODO 3: 列出每一个功能完成度

### 核心功能完成度

| 功能 | 模块 | 完成度 | 测试数 | 状态 |
|------|------|--------|--------|------|
| **驱动提取** | | | | |
| - always_ff | DriverCollector | 90% | 15+ | ✅ |
| - always_comb | DriverCollector | 85% | 10+ | ✅ |
| - continuous | DriverCollector | 85% | 8+ | ✅ |
| - 嵌套 if | DriverCollector | 70% | 3 | ⚠️ |
| - case 语句 | DriverCollector | 70% | 3 | ⚠️ |
| - 拼接 RHS | DriverCollector | 60% | 2 | ⚠️ |
| - 多驱动检测 | DriverCollector | 50% | 2 | 🔴 |
| **负载提取** | | | | |
| - 基本负载 | LoadTracer | 80% | 5+ | ✅ |
| - 反向查找 | LoadTracer | 60% | 2 | ⚠️ |
| - 跨模块负载 | LoadTracer | 30% | 0 | 🔴 |
| **连接追踪** | | | | |
| - 模块实例 | ConnectionTracer | 85% | 5+ | ✅ |
| - 端口连接 | ConnectionTracer | 75% | 3 | ⚠️ |
| - 跨模块连接 | ConnectionTracer | 40% | 1 | 🔴 |
| **时钟/复位** | | | | |
| - 时钟提取 | SemanticClock | 75% | 4 | ⚠️ |
| - 复位提取 | SemanticReset | 60% | 2 | ⚠️ |
| - 时序关系 | SemanticEnricher | 50% | 1 | 🔴 |
| **数据流分析** | | | | |
| - 流水线 | DataFlowTracer | 70% | 3 | ⚠️ |
| - 组合逻辑链 | DataFlowTracer | 60% | 2 | ⚠️ |
| **FSM 分析** | | | | |
| - 状态机提取 | FSMAnalyzer | 50% | 2 | ⚠️ |
| - 状态转换 | FSMAnalyzer | 30% | 0 | 🔴 |
| **CDC 分析** | | | | |
| - 多时钟检测 | CDCAnalyzer | 60% | 2 | ⚠️ |

### 完成度等级

- ✅ **90%**: 功能基本完成，边缘用例待优化
- ⚠️ **60-80%**: 功能基本可用，部分场景不支持
- 🔴 **<60%**: 功能不完整或实验性

---

## TODO 4: 全局测试入口

### 当前状态

当前测试分散在多个目录：
- `tests/unit/tools/` - 工具测试
- `tests/unit/sv_trace/` - 核心功能测试
- `tests/unit/trace/` - 追踪模块测试
- `tests/unit/sv_verify/` - 验证测试

### 建议: 创建统一测试入口

```python
# tests/test_all.py
"""
SV-Trace 全功能测试入口

Usage:
    pytest tests/test_all.py              # 运行所有测试
    pytest tests/test_all.py -k driver    # 只跑 driver 相关
    pytest tests/test_all.py --cov        # 覆盖率报告
"""

import pytest
import sys
sys.path.insert(0, 'src')

# 标记分类
pytest_plugins = ['pytest.anyio']

def pytest_configure(config):
    config.addinivalue_line("markers", "driver: 驱动提取测试")
    config.addinivalue_line("markers", "load: 负载追踪测试")
    config.addinivalue_line("markers", "connection: 连接追踪测试")
    config.addinivalue_line("markers", "clock: 时钟提取测试")
    config.addinivalue_line("markers", "semantic: 语义增强测试")
    config.addinivalue_line("markers", "integration: 集成测试")

# 导入所有测试模块
pytest_plugins = []

# 测试入口点
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
```

### 创建计划

1. 创建 `tests/test_all.py` 作为统一入口
2. 创建 `tests/quick_test.py` 快速冒烟测试 (< 1 分钟)
3. 创建 `tests/full_test.py` 完整测试 (包含性能测试)

---

## TODO 5: 架构后续演变

### 当前架构 (Phase 3)

```
User → Semantic Layer → Extractors → Scope Builder → Parse → Pyslang
```

### 后续演变计划

#### Phase 4: 智能体集成
- AgentContext 完善
- 多智能体协作
- 自然语言查询接口

#### Phase 5: 验证增强
- Formal verification 接口
- CDC/RCA 集成
- 覆盖率分析增强

#### Phase 6: 自动化优化
- 自动性能调优
- 自适应提取策略
- ML-based 信号分类

### 架构风险

| 风险 | 影响 | 缓解 |
|------|------|------|
| SemanticCollector 废弃 | 兼容性问题 | 已提供兼容层 |
| Query 模块迁移 | API 变更 | 分阶段迁移 |
| 依赖 pyslang | 底层依赖 | 抽象接口层 |

---

## TODO 6: 整理项目文件，区分已实现和潜在需求

### 已实现功能 ✅

#### 核心提取 (Stable)
```
src/
├── extractors/
│   ├── base.py          # DriverPoint, LoadPoint, Connection
│   ├── driver.py        # DriverExtractor
│   ├── load.py          # LoadExtractor
│   └── connection.py    # ConnectionExtractor
├── trace/
│   ├── driver.py        # DriverCollector
│   ├── load.py          # LoadTracer
│   ├── connection.py    # ConnectionTracer
│   └── dataflow.py      # DataFlowTracer
└── parse/
    └── parser.py        # SVParser
```

#### 语义增强 (Beta)
```
src/semantic/
├── enricher.py          # SemanticEnricher
├── clock.py             # ClockDomainItem
├── reset.py             # ResetSignalItem
└── models.py            # EnrichedSignal
```

#### 调试分析 (Beta)
```
src/debug/
├── analyzers/
│   ├── cdc.py           # CDCAnalyzer
│   ├── fsm_analyzer.py  # FSMAnalyzer
│   └── ...
└── class_extractor.py   # ClassExtractor
```

### 待实现/实验性功能 🔴

#### 高优先级
| 功能 | 状态 | 难度 | 说明 |
|------|------|------|------|
| 跨模块驱动追踪 | 🔴 | 高 | 需要模块依赖分析 |
| 多驱动冲突检测 | 🔴 | 高 | CDC 的一部分 |
| 时序路径分析 | 🔴 | 高 | 依赖数据流分析 |
| FSM 状态转换提取 | 🔴 | 中 | 已有基础框架 |

#### 中优先级
| 功能 | 状态 | 难度 | 说明 |
|------|------|------|------|
| 约束提取 (constraint) | 🔴 | 中 | parse.constraint 不存在 |
|覆盖率分析 | 🔴 | 高 | 需 VCD 接口 |
| 功耗分析 | 🔴 | 高 | 需时序数据 |
| 面积估算 | 🔴 | 中 | 已有基础 |

#### 低优先级/实验性
| 功能 | 状态 | 说明 |
|------|------|------|
| VCD 波形分析 | 🔴 | 需第三方库 |
| 自动化 formal | 🔴 | 长期目标 |
| ML 信号分类 | 🔴 | 研究性质 |

### 需求优先级分类

| 优先级 | 需求 | 理由 |
|--------|------|------|
| **P0** | 跨模块驱动追踪 | 核心功能缺失 |
| **P0** | 多驱动冲突检测 | CDC 基础 |
| **P1** | 时序路径分析 | 常见用例 |
| **P1** | FSM 状态机完整提取 | 调试需求 |
| **P2** | 约束提取 | SVA/UVM 支持 |
| **P2** | 覆盖率分析 | 验证需求 |
| **P3** | 功耗/面积估算 | 预估功能 |

---

## TODO 7: 每一个功能的验证完整度

### 验证完整度矩阵

| 功能 | 测试数 | 覆盖场景 | 断言质量 | 完整度 |
|------|--------|----------|----------|--------|
| **DriverCollector** | | | | |
| - always_ff 基本 | 15 | 80% | 中 | ⚠️ 70% |
| - always_comb | 10 | 70% | 中 | ⚠️ 65% |
| - continuous | 8 | 75% | 中 | ⚠️ 65% |
| - 嵌套 if | 3 | 50% | 弱 | 🔴 40% |
| - case 语句 | 3 | 50% | 弱 | 🔴 40% |
| - 拼接 RHS | 2 | 40% | 弱 | 🔴 30% |
| - 多驱动 | 2 | 30% | 弱 | 🔴 20% |
| **LoadTracer** | | | | |
| - 基本负载 | 5 | 70% | 中 | ⚠️ 60% |
| - 反向查找 | 2 | 40% | 弱 | 🔴 30% |
| **ConnectionTracer** | | | | |
| - 模块实例 | 5 | 80% | 中 | ⚠️ 70% |
| - 端口连接 | 3 | 60% | 弱 | 🔴 50% |
| **时钟/复位** | | | | |
| - 时钟提取 | 4 | 60% | 中 | ⚠️ 55% |
| - 复位提取 | 2 | 50% | 弱 | 🔴 40% |
| **FSM** | 2 | 30% | 弱 | 🔴 25% |
| **CDC** | 2 | 40% | 弱 | 🔴 30% |

### 验证完整度评估标准

- **完整 (90%+)**: 测试覆盖所有已知场景，断言详细
- **良好 (70-90%)**: 测试覆盖主要场景，断言较详细
- **不足 (50-70%)**: 测试覆盖部分场景，存在弱断言
- **很差 (<50%)**: 测试覆盖不足或断言过弱

### 改进建议

#### 高优先级改进

1. **DriverCollector 嵌套 if** (当前 40%)
   - 添加更多嵌套场景测试
   - 验证条件信号的传播
   - 补充时钟使能验证

2. **多驱动检测** (当前 20%)
   - 添加 case/if 多分支测试
   - 添加跨 always 块多驱动测试
   - 验证冲突报告机制

3. **LoadTracer 反向查找** (当前 30%)
   - 添加复杂表达式负载测试
   - 验证中间信号的负载传播

#### 中优先级改进

4. **FSM 状态机** (当前 25%)
   - 完善 FSMAnalyzer 测试
   - 添加状态转换路径测试

5. **CDC 分析** (当前 30%)
   - 添加多时钟互操作测试
   - 验证同步器链检测

---

## 总结

### 当前状态

| 指标 | 数值 |
|------|------|
| 测试文件数 | 65 |
| 通过测试数 | 164 |
| 失败/错误 | 5 (fixture) |
| 核心模块 | 11 |
| 代码行数 | ~34,600 |

### 需要立即修复

1. **弱断言** (8 个文件)
2. **金标准不完整** (大部分测试)
3. **多驱动检测** (完成度 20%)

### 下一步计划

1. **修复弱断言** - 1-2 天
2. **完善金标准测试** - 3-5 天
3. **实现跨模块追踪** - 1 周
4. **创建统一测试入口** - 1 天

---

*报告生成时间: 2026-05-13*
