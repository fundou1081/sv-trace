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
