# SV-TRACE 开发计划

## 已完成 ✅

### 质量检查工具
- [x] MultiDriverDetector - 多驱动检测
- [x] CodeQualityScorer v2 - 代码质量评分(客观指标)
- [x] CDCAnalyzer v5 - 跨时钟域分析

### 性能评估工具
- [x] PerformanceEstimator - 频率/流水线估算
- [x] AreaEstimator v3 - 资源估算(LUT/FF/DSP)
- [x] PowerEstimator - 功耗估算

---

## 面积评估 (Area Estimation)

### 估算模型

基于7-series FPGA架构:

| 资源 | 估算公式 | 系数 |
|------|----------|------|
| **FF** | always_ff驱动 × 位宽 | 1 FF/bit |
| **LUT** | 操作符类型加权 | 见下方 |
| **DSP** | `*` 乘法器计数 | 1 DSP/乘法器 |
| **BRAM** | 大数组检测 | >512深度 × >8位宽 |
| **CLB** | 合���计算 | LUT/8 + FF/16 + DSP×30 + BRAM×30 |

### LUT估算规则

```
加法(+)   : +1 LUT/bit
减法(-)   : +1 LUT/bit
乘法(*)   : +8 LUT/bit (32位约需8 LUT6)
除法(/)   : +16 LUT/bit
比较(==,!=,<,>) : +1 LUT
逻辑(&,|) : +0.1 LUT/bit
移位(<<,>>): +1 LUT
```

### 资源模型系数

```python
FF_PER_BIT = 1.0          # 每位寄存器
LUT_PER_ADD = 1.0         # 加法
LUT_PER_MUL = 8.0         # 乘法(32位)
LUT_PER_DIV = 16.0        # 除法
DSP_PER_MUL = 1.0         # DSP48E1
BRAM_PER_ARRAY = 1.0      # 大数组
SLICE_PER_LUT = 0.125     # 8 LUT = 1 CLB
SLICE_PER_FF = 0.0625     # 16 FF = 1 CLB
SLICE_PER_DSP = 30.0      # 1 DSP = 30 CLB
SLICE_PER_BRAM = 30.0     # 1 18K BRAM = 30 CLB
```

### 状态: ✅ 已实现

---

## 功耗评估 (Power Estimation)

### 估算模型

总功耗 = 静态功耗 + 动态功耗 + 峰值功耗

#### 静态功耗 (mW)

| 组件 | 公式 | 系数 |
|------|------|------|
| LUT | LUT × 0.0001 | 0.1 μW/LUT |
| FF | FF × 0.00005 | 0.05 μW/FF |

```
P_static = LUT × 0.0001 + FF × 0.00005 mW
```

#### 动态功耗 (mW)

基于翻转率模型:

```
P_dynamic = Σ(翻转率 × 频率 × 资源量 × 系数)
```

| 组件 | 公式 | 系数 |
|------|------|------|
| FF翻转 | FF × 20% × freq × 0.0005 | 0.5 μW/FF @ 100MHz |
| LUT切换 | LUT × 20% × freq × 0.001 | 1 μW/LUT @ 100MHz |
| DSP工作 | DSP × freq × 0.1 | 100 mW/DSP @ 100MHz |
| BRAM | BRAM × freq × 0.05 | 50 mW/18K @ 100MHz |

#### 峰值功耗 (mW)

```
P_peak = P_dynamic × 4.0
```

#### 频率因子

```
freq_factor = frequency_mhz / 100.0
```

### 功耗估算公式汇总

```python
# 静态功耗
P_static = lut_count * 0.0001 + ff_count * 0.00005  # mW

# 动态功耗
P_dynamic = (
    ff_count * 0.2 * freq_factor * 0.0005 * 1000 +  # FF
    lut_count * 0.2 * freq_factor * 0.001 * 1000 +   # LUT
    dsp_count * freq_factor * 0.1 * 100 +             # DSP
    bram_count * freq_factor * 0.05 * 100             # BRAM
)  # mW

# 峰值功耗
P_peak = P_dynamic * 4.0  # mW

# 总功耗
P_total = P_static + P_dynamic  # mW
```

### 电池寿命估算

```python
# 功率(W) = 电压(V) × 电流(A)
power_w = power_mw / 1000.0
current_a = power_w / voltage

# 使用时间(h) = 容量(Ah) / 电流(A)
hours = capacity_mah / (current_a * 1000)
days = hours / 24
```

### 状态: ✅ 已实现 (基础模型)

---

## 完整指标汇总

### 面积指标

| 指标 | 公式/方法 | 单位 | 状态 |
|------|----------|------|------|
| LUT | 操作符估算 | count | ✅ |
| FF | always_ff × 位宽 | count | ✅ |
| DSP | 乘法器计数 | count | ✅ |
| BRAM | 大数组换算 | 18K units | ✅ |
| CLB | 合并计算 | slices | ✅ |

### 功耗指标

| 指标 | 公式/方法 | 单位 | 状态 |
|------|----------|------|------|
| 静态功耗 | LUT×0.0001 + FF×0.00005 | mW | ✅ |
| FF动态功耗 | FF×翻转率×频率×系数 | mW | ✅ |
| LUT动态功耗 | LUT×翻转率×频率×系数 | mW | ✅ |
| DSP动态功耗 | DSP×频率×系数 | mW | ✅ |
| BRAM动态功耗 | BRAM×频率×系数 | mW | ✅ |
| 峰值功耗 | 动态功耗×4 | mW | ✅ |
| 总功耗 | 静态+动态 | mW | ✅ |
| 电池寿命 | 容量/电流 | hours | ✅ |

### 功耗优化建议 (TODO)

| 优化项 | 检测方法 | 状态 |
|--------|----------|------|
| 时钟门控 | 检测无操作时的时钟使能 | TODO |
| 操作数隔离 | 检测空闲运算单元 | TODO |
| 多电压域 | 分析电压域切换 | TODO |
| 数据通路门控 | 检测不活动数据通路 | TODO |

---

## 待开发工具 📋

### P1 - 核心评价工具

| 工具 | 目标 | 关键指标 | 状态 |
|------|------|----------|------|
| CoverageAnalyzer | 代码覆盖率 | 行/分支/条件/FSM | ✅ DONE |
| TestabilityAnalyzer | 可测试性 | 可控性/可观测性 | ✅ DONE |
| TimingAnalyzer | 时序分析 | slack/关键路径 | ✅ DONE |

### P2 - 进阶评价工具

| 工具 | 目标 | 关键指标 | 状态 |
|------|------|----------|------|
| EquivalenceChecker | 等价性检验 | combinational/sequential | TODO |
| FuzzTester | 模糊测试 | 覆盖率引导 | TODO |
| RegressionSuite | 回归测试 | baseline对比 | TODO |

### P3 - 高级工具

| 工具 | 目标 | 关键指标 | 状态 |
|------|------|----------|------|
| FormalVerifier | 形式验证 | property checking | TODO |
| PowerOptimizer | 功耗优化 | 时钟门控建议 | TODO |

---

## 实现优先级

1. **P1**: CoverageAnalyzer, TestabilityAnalyzer, TimingAnalyzer
2. **P2**: EquivalenceChecker, FuzzTester, RegressionSuite  
3. **P3**: FormalVerifier, PowerOptimizer

---

*最后更新: 2026-04-25*

---

## FSM状态机分析 (TODO)

### 深度分析指标

| 指标 | 检测方法 | 状态 |
|------|--------|------|
| 状态数量 | typedef enum解析 | ✅ 基础 |
| 跳转条件 | case语句分析 | ✅ 基础 |
| 节点度 | in/out degree | ✅ 基础 |
| 环检测 | DFS环路检测 | ⚠️ 需增强 |
| FSM复杂度 | 状态×跳转 | TODO |
| 不可达状态 | 可达性分析 | TODO |
| 死锁检测 | 无出口环 | TODO |

### FSM复杂度模型

```python
# 复杂度 = 状态数 × 平均跳转数
complexity = state_count * avg_transitions_per_state

# 安全阈值
SAFE_COMPLEXITY = 50   # < 50 安全
WARN_COMPLEXITY = 100 # 100-150 警告
HIGH_COMPLEXITY = 150 # > 150 需拆分
```

### 下一步实现

- [ ] FSM复杂度评分
- [ ] 不可达状态检测  
- [ ] 死锁环检测
- [ ] FSM优化建议

---

## 新增任务

### 工具增强

| 工具 | 增强项 | 状态 |
|------|-------|------|
| ProjectAnalyzer | FSM复杂度视图 | TODO |
| StaticAnalyzer | FSM检测增强 | TODO |
| CodeMetricsAnalyzer | fanin精确统计 | TODO |

### CDC增强

| 工具 | 功能 | 状态 |
|------|-------|------|
| ClockDomainAnalyzer | 多时钟域检测 | TODO |
| ResetAnalyzer | 复位完整性 | TODO |
| TimingPathAnalyzer | 跨时钟域路径 | TODO |



---

## 2026-04-26 更新

### 新增功能

#### 1. FSM状态编码建议 ✅
- 根据状态数量推荐 binary/gray/one-hot 编码
- 功耗估算
- 编码方案对比

#### 2. HTML报告生成器 ✅
- 通用HTMLReportGenerator类
- 支持章节、表格、徽章、警告
- 多主题支持 (blue/green/purple/dark)
- JSON导出支持

#### 3. 文档更新
- TODO_V2.md - 多视角需求分析
- ADR-020 - FSM深度分析架构

### 下一步任务

| 功能 | 优先级 | 状态 |
|------|--------|------|
| FSM SVA属性生成 | P2 | TODO |
| FSM验证计划生成 | P2 | TODO |
| CDC增强(多时钟域) | P1 | TODO |
| 复位完整性检查增强 | P1 | TODO |
| fanin/fanout精确统计 | P1 | TODO |
| 多文件联合分析 | P2 | TODO |
| 跨时钟域Timed Path | P2 | TODO |

---

## 2026-04-26 上午更新 (第二批)

### 已完成功能

| 功能 | 文件 | 说明 |
|------|------|------|
| **CDC多时钟域检测增强** | `cdc.py` | CDCExtendedAnalyzer, 多时钟域路径分析, MTBF估算 |
| **fanin/fanout精确统计** | `dependency.py` | FanoutAnalyzer, FaninAnalyzer, ConnectivityMatrix |
| **复位完整性检查增强** | `reset_domain_analyzer.py` | ResetIntegrityChecker, 复位树分析, 上电序列生成 |

### 新增类/方法

```python
# CDC增强
CDCExtendedAnalyzer     # 多时钟域检测
ClockDomain             # 时钟域信息
CDCPath                 # CDC路径信息
CDCReportEnh           # 增强报告

# Fanin/Fanout增强
FanoutAnalyzer         # 扇出分析
FaninAnalyzer          # 扇入分析
ConnectivityMatrix     # 模块连接矩阵

# 复位增强
ResetIntegrityChecker  # 复位完整性检查
ResetIntegrityReport   # 完整性报告
ResetTreeNode          # 复位树节点
```

### 待完成

| 功能 | 优先级 | 状态 |
|------|--------|------|
| FSM SVA属性生成 | P2 | TODO |
| FSM验证计划生成 | P2 | TODO |
| 多文件联合分析 | P2 | TODO |
| 跨时钟域Timed Path | P2 | TODO |

---

## 2026-04-26 上午更新 (第三批)

### 已完成功能

| 功能 | 文件 | 说明 |
|------|------|------|
| **FSM SVA属性生成** | `fsm_analyzer.py` | SVAGenerator, 自动生成SVA assertions |
| **FSM验证计划生成** | `fsm_analyzer.py` | VerificationPlanGenerator, 自动生成验证点 |
| **多文件联合分析** | `multi_file_analyzer.py` | MultiFileAnalyzer, 模块接口/连接/依赖 |
| **跨时钟域Timed Path** | `timed_path_analyzer.py` | TimedPathAnalyzer, 时序路径分析 |

### 新增功能一览

#### FSM SVA属性生成
```python
from debug.analyzers.fsm_analyzer import SVAGenerator, generate_fsm_sva

generator = SVAGenerator(parser)
report = generator.generate("fsm_module")
generator.export_svafile("fsm_assertions.sv")
generator.export_as_module("fsm_assertions.sv")
```

#### FSM验证计划生成
```python
from debug.analyzers.fsm_analyzer import VerificationPlanGenerator, generate_verification_plan

generator = VerificationPlanGenerator(parser)
plan = generator.generate("main_fsm")
generator.export_to_markdown("verification_plan.md")
generator.export_to_yaml("verification_plan.yaml")
```

#### 多文件联合分析
```python
from debug.analyzers.multi_file_analyzer import MultiFileAnalyzer, analyze_multiple_files

analyzer = MultiFileAnalyzer(["file1.sv", "file2.sv", "file3.sv"])
report = analyzer.analyze()
# report.modules, report.connections, report.cross_file_signals
cycles = analyzer.find_cycles()  # 检测循环依赖
```

#### 跨时钟域Timed Path分析
```python
from debug.analyzers.timed_path_analyzer import TimedPathAnalyzer, analyze_timed_paths

analyzer = TimedPathAnalyzer(parser)
report = analyzer.analyze()
# report.paths, report.clock_relationships
# report.setup_violations, report.hold_violations
```

---

## 2026-04-26 更新 (第四批)

### P3功能 + 新增功能

| 功能 | 文件 | 说明 |
|------|------|------|
| **条件覆盖分析** | `condition_coverage.py` | if嵌套条件coverage, cross覆盖, 中间变量展开 |
| **FSM覆盖率追踪** | `fsm_analyzer.py` | 状态/跳转/序列覆盖, UCIS格式导出 |
| **形式验证接口** | `formal_verification.py` | SVA/PSL属性生成, SymbiYosys脚本 |

### 新增功能详解

#### 条件覆盖分析 (ConditionCoverageAnalyzer)
```python
from debug.analyzers.condition_coverage import ConditionCoverageAnalyzer

analyzer = ConditionCoverageAnalyzer(parser)
report = analyzer.analyze()

# 导出coverage model
analyzer.export_to_coverage_model("coverage_model.sv", report)

# 导出约束
analyzer.export_to_constraint("coverage_constraints.sv", report)
```

**核心功能**:
- 解析if嵌套条件到原始信号
- 展开中间变量到底层信号
- 生成条件cross覆盖对
- 导出SystemVerilog covergroup

#### FSM覆盖率追踪 (FSMCoverageTracker)
```python
from debug.analyzers.fsm_analyzer import FSMCoverageTracker

tracker = FSMCoverageTracker(parser)
reports = tracker.analyze()

# 合并仿真数据
tracker.merge_with_simulation({"states": {"IDLE": 10}, "transitions": {"IDLE->RUN": 5}})

# 导出各种格式
tracker.export_to_json("coverage.json")
tracker.export_to_ucis("coverage.ucis")
tracker.generate_coverage_report_html("coverage.html")
```

#### 形式验证接口 (FormalVerificationGenerator)
```python
from debug.analyzers.formal_verification import FormalVerificationGenerator

gen = FormalVerificationGenerator(parser)
report = gen.analyze()

# 导出各种格式
gen.export_to_sby("design.sby")           # SymbiYosys
gen.export_to_sv_property("props.sv")     # SystemVerilog
gen.export_to_psl("props.psl")             # PSL
gen.export_to_property_list("props.csv")   # CSV清单
gen.generate_formal_testplan("testplan.md") # 测试计划
```

### 完成状态

| 优先级 | 功能 | 状态 |
|--------|------|------|
| P1 | CDC多时钟域检测增强 | ✅ |
| P1 | FSM复杂度评分+死锁检测 | ✅ |
| P1 | 复位完整性检查增强 | ✅ |
| P1 | fanin/fanout精确统计 | ✅ |
| P1 | HTML报告输出 | ✅ |
| P2 | FSM SVA属性生成 | ✅ |
| P2 | FSM验证计划生成 | ✅ |
| P2 | 多文件联合分析 | ✅ |
| P2 | 跨时钟域Timed Path | ✅ |
| **P3** | **FSM覆盖率追踪** | ✅ |
| **P3** | **形式验证接口** | ✅ |
| **新增** | **条件覆盖分析** | ✅ |

**🎉 所有计划功能已完成！**
