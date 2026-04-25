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

## 待开发 📋

### P1 - 核心评价工具

#### 1. CoverageAnalyzer (覆盖率分析)
```
目标: 分析RTL代码覆盖率
指标:
  - 行覆盖率 (line coverage)
  - 分支覆盖率 (branch coverage)  
  - 条件覆盖率 (condition coverage)
  - FSM覆盖率 (state coverage)
状态: TODO
优先级: P1
```

#### 2. TestabilityAnalyzer (可测试性分析)
```
目标: 评估设计的可测试性
指标:
  - controllability (可控性)
  - observability (可观测性)
  - scan chain readiness
  - ATPG coverage estimate
状态: TODO
优先级: P1
```

#### 3. TimingAnalyzer (时序分析)
```
目标: 评估关键路径时序
指标:
  - 组合逻辑延迟
  - 寄存器建立/保持时间
  - slack estimate
  - critical path length
状态: TODO
优先级: P1
```

### P2 - 进阶评价工具

#### 4. EquivalenceChecker (等价性检验)
```
目标: RTL vs 网表等价性
指标:
  - combinational equivalence
  - sequential equivalence
  - 周期精确对比
状态: TODO
优先级: P2
```

#### 5. FuzzTester (模糊测试)
```
目标: 随机激励生成
指标:
  - coverage guided fuzzing
  - constraint solving
  - corner case generation
状态: TODO
优先级: P2
```

#### 6. RegressionSuite (回归测试)
```
目标: 自动回归测试框架
指标:
  - baseline comparison
  - diff detection
  - pass/fail statistics
状态: TODO
优先级: P2
```

### P3 - 高级工具

#### 7. FormalVerifier (形式验证接口)
```
目标: 连接形式验证工具
指标:
  - property checking
  - invariant detection
  - assume/guarantee analysis
状态: TODO
优先级: P3
```

#### 8. PowerOptimizer (功耗优化建议)
```
目标: 基于功耗分析提供优化建议
指标:
  - clock gating opportunities
  - operand isolation
  - dynamic voltage scaling
  - power domain analysis
状态: TODO - 需要结合AreaEstimator
优先级: P3
```

## 评价指标汇总

### 代码质量 (Quality)
| 维度 | 指标 | 权重 | 状态 |
|------|------|------|------|
| 可读性 | 注释比例 | 20% | ✅ |
| 可读性 | 行长度 | 20% | ✅ |
| 可读性 | 命名规范 | 20% | ✅ |
| 可测试性 | IO比例 | 25% | ✅ |
| 可测试性 | 可控性 | 25% | ✅ |
| 可测试性 | 可观测性 | 25% | ✅ |
| 可维护性 | 模块大小 | 40% | ✅ |
| 可维护性 | 嵌套深度 | 30% | ✅ |
| 可维护性 | 层次结构 | 30% | ✅ |
| CDC安全 | FF比例 | 40% | ✅ |
| CDC安全 | Latch数量 | 30% | ✅ |
| CDC安全 | 时钟域数 | 30% | ✅ |

### 性能评估 (Performance)
| 维度 | 指标 | 单位 | 状态 |
|------|------|------|------|
| 频率 | 最高频率 | MHz | ✅ |
| 时序 | 流水线级数 | stages | ✅ |
| 时序 | 关键路径 | ns | TODO |
| 资源 | LUT | count | ✅ |
| 资源 | FF | count | ✅ |
| 资源 | DSP | count | ✅ |
| 资源 | BRAM | 18K units | ✅ |

### 功耗评估 (Power) - 待深入开发
| 维度 | 指标 | 公式 | 状态 |
|------|------|------|------|
| 静态功耗 | LUT功耗 | LUT × 0.0001mW | ✅ |
| 静态功耗 | FF功耗 | FF × 0.00005mW | ✅ |
| 动态功耗 | FF翻转 | 翻转率 × 频率 × FF × 系数 | ✅ |
| 动态功耗 | LUT切换 | 翻转率 × 频率 × LUT × 系数 | ✅ |
| 峰值功耗 | 峰值 | Dynamic × 4 | ✅ |
| **功耗优化** | 时钟门控 | 检测无操作时钟门控 | TODO |
| **功耗优化** | 操作数隔离 | 检测空闲操作 | TODO |
| **功耗优化** | 电压域 | 多电压域分析 | TODO |

## 实现优先级

1. **P1**: CoverageAnalyzer, TestabilityAnalyzer, TimingAnalyzer
2. **P2**: EquivalenceChecker, FuzzTester, RegressionSuite  
3. **P3**: FormalVerifier, PowerOptimizer

---

*最后更新: 2026-04-25*
