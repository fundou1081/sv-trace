# SV-Trace 未来实现项目规划
======================================================================

本文件记录 SV-Trace 工具库的未来实现项目，按优先级和工作角色组织。

======================================================================
第一部分: 新增实用工具需求 (用户场景驱动)
======================================================================

## 用户场景 1: Hier Path 模糊匹配搜索
### 需求描述
用户拿到了某个可能是模糊的hier path，但不确定是否准确，需要搜索出和这个path最接近的、准确的hier path。

### 功能
- 模糊路径匹配: 输入可能不完整的hier path
- 相似度计算: 计算与所有实际path的相似度
- 候选列表: 返回最接近的N个候选path
- 自动纠错建议

### 示例输入/输出
```
输入: "top.cpu.alu.result"
输出: 
  1. top.cpu.alu.result_reg (score: 0.85)
  2. top.cpu.alu.result_pipe (score: 0.82)
  3. top.cpu0.alu.result (score: 0.75)
```

### 相关工具
- 当前基于: HierarchyQuery
- 需要实现: FuzzyPathMatcher

---

## 用户场景 2: 采样条件智能识别
### 需求描述
用户在写coverage时需要知道信号什么时候稳定，需要知道根据什么条件进行sample。

### 功能
- 自动识别valid/ready握手
- 识别采样边沿（posedge/negedge）
- 识别条件采样（sample when）
- 生成sample block

### 示例输入/输出
```
输入: signal "data_out", module
输出:
  sample condition: @(posedge valid)
  alternative: @(posedge ready && valid)
  suggestion: "Use @(posedge valid) for data capture"
```

### 相关工具
- 当前基于: CoverageGenerator扩展
- 需要实现: SampleConditionAnalyzer

---

## 用户场景 3: if/case 条件关系自动提取
### 需求描述
用户在写data path coverage时，当某个信号由前置的if或case条件决定时，需要自动拿到这些关系来写cross coverage。

### 功能
- 提取信号的所有if/case条件
- 识别条件信号的层次
- 自动生成cross coverage关系
- 嵌套条件展开

### 示例
```
输入: 
  if (mode == 1) data_out = data_in + 1;
  else if (mode == 2) data_out = data_in - 1;

输出:
  cross: {data_out, mode} 
  bins: {mode==1, mode==2, default}
```

### 相关工具
- 当前基于: CoverageGenerator
- 需要实现: ConditionRelationExtractor

---

## 用户场景 4: if 嵌套条件完全展开
### 需求描述
用户在写控制相关的coverage时，需要直接写出if以及嵌套if条件的所有cross组合，尤其是当if里某个条件已经是组合逻辑时，应该展开到最底层。

### 功能
- 递归展开嵌套if
- 识别组合逻辑条件
- 生成完整bin组合
- 简化组合

### 示例
```
输入:
  if (a && b) ...
  else if (c) ...

输出:
  bins: {a=1,b=1}, {c=1, a=0}, {default}
  # 而不是简单的 {a}, {c}
```

### 相关工具
- 需要实现: NestedConditionExpander

---

## 用户场景 5: Data Path 边界值推导
### 需求描述
用户在写data path coverage时，应该根据其信号的定义的值域，以及涉及到运算，推导出边界以及其他特征点，并写入coverage。

### 功能
- 信号值域分析 (+/- 边界)
- 算术运算边界处理 (+, -, *, /, %)
- 饱和/溢出检测
- 特征点生成

### 示例
```
输入: data_out = data_in + 1
data_in: [7:0]

输出:
  bins: 
    - zero (0)
    - min (1) 
    - max (254)
    - overflow (255)
    - wrap (default)
```

### 当前已有
- CoverageGenerator (基础版)

### 需要扩展: DataPathBoundaryAnalyzer

---

## 用户场景 6: 饱和/溢出风险自动检测
### 需求描述
在data path上自动处理饱和以及溢出的检查，自动给出潜在的风险。

### 功能
- 饱和检测
- 溢出检测
- 风险评估
- 建议修复

### 示例
```
输入: result = data_in + addend

检测:
  - Overflow at: result == 255 (8-bit)
  - Risk level: HIGH
  - Suggestion: Add overflow check or extend width
```

### 需要实现: OverflowRiskDetector

======================================================================
第二部分: 已有工具增强建议
======================================================================

## 1. 验证工程师角色自动化

| 角色 | 当前工具 | 增强建议 |
|------|----------|----------|
| 验证架构师 | SVParser | generate_uvm_env.py |
| 激励工程师 | CoverageGenerator | generate_constraint.py |
| 覆盖率工程师 | RiskCollector | analyze_coverage_gaps.py |
| 调试工程师 | XValueDetector | analyze_simulation_log.py |
| 回归工程师 | - | smart_regression.py |
| 验证经理 | - | generate_progress_report.py |

## 2. 设计评估增强

### 当前覆盖 (83%)

需要补充:
- ProtocolChecker: AXI/APB协议检查
- PowerEstimator: 功耗分析（简单版已完成）

### 评估维度扩展

| 维度 | 当前状态 | 建议 |
|------|----------|------|
| 功能正确性 | ✅ | - |
| 资源利用 | ✅ PowerEstimator | - |
| 时序收敛 | ✅ | - |
| 功耗分析 | ⚠️ 简单版 | 完整版 |
| 可测试性 | ❌ | SCANChainExtractor |
| 接口合规 | ❌ | ProtocolChecker |

## 3. Risk Identification 增强 (Phase 1已完成)

当前可识别:
- CDC
- MultiDriver
- Uninitialized
- ClockDomain
- ResetDomain

Phase 2 (风险评估):
- Probability: 基于历史的概率计算
- Impact: 影响评估
- Severity: 严重度排序
- Risk Matrix: 评分模型

Phase 3 (风险缓解):
- Test Suggestion: 建议测试
- Action Item: 行动项
- Progress Tracking: 进度跟踪

======================================================================
第三部分: 项目路线图
======================================================================

## 短期 (1-2周)

Priority 1:
- [x] RiskCollector Phase1 ✅
- [x] PowerEstimator (简单版) ✅
- [x] CoverageGenerator ✅

Priority 2:
- [ ] SampleConditionAnalyzer
- [ ] ConditionRelationExtractor
- [ ] HierPathFuzzyMatcher

## 中期 (1-2个月)

- [ ] NestedConditionExpander
- [ ] DataPathBoundaryAnalyzer
- [ ] OverflowRiskDetector
- [ ] RiskCollector Phase2 & 3
- [ ] ProtocolChecker

## 长期 (3-6个月)

- [ ] generate_uvm_env.py
- [ ] smart_regression.py
- [ ] generate_progress_report.py
- [ ] ProtocolValidator (AXI/APB/AXI Stream)

======================================================================
第四部分: 工具实现参考
======================================================================

### 命名规范

```
[功能]_[类型].py

例如:
  coverage_generator.py    # 覆盖率生成
  risk_collector.py       # 风险收集
  power_estimation.py      # 功耗估算
  sample_finder.py         # 采样查找
```

### 代码结构

每个工具应包含:
1. 数据类 (dataclass)
2. 主类 (Analyzer/Collector/Estimator)
3. 便捷函数 (方便调用)
4. 测试代码

### 示例结构

```python
@dataclass
class Result:
    data: str

class MyTool:
    def __init__(self, parser):
        self.parser = parser
    
    def analyze(self) -> Result:
        # ...
        return result

def analyze_xxx(parser) -> Result:
    tool = MyTool(parser)
    return tool.analyze()
```

======================================================================
更新日期: 2024
======================================================================

======================================================================
附录 A: 验证工程师角色与自动化
======================================================================

## 6个核心角色与自动化需求

### 【角色1: 验证架构师】
职责: 验证计划、结构、策略
痛点: 如何快速搭建验证环境
自动化: generate_uvm_env.py

### 【角色2: 激励工程师】
职责: 编写测试激励、场景、序列
痛点: 如何覆盖corner case
自动化: generate_random_constraint.py, generate_boundary_test.py

### 【角色3: 覆盖率工程师】
职责: 覆盖率分析、提高
痛点: 如何知道哪些没覆盖
自动化: analyze_coverage_gaps.py

### 【角色4: 调试工程师】
职责: 定位bug、分析错误
痛点: 如何快速定位问题
自动化: analyze_simulation_log.py

### 【角色5: 回归工程师】
职责: 回归测试套件、维护
痛点: 如何管理大量测试
自动化: smart_regression.py

### 【角色6: 验证经理】
职责: 进度跟踪、资源分配
痛点: 验证进度如何
自动化: generate_progress_report.py

======================================================================
附录 B: 设计评估维度扩展
======================================================================

## RTL设计评估维度 (12维度)

| # | 维度 | 当前工具 | 优先级 |
|---|------|----------|--------|
| 1 | 功能正确性 | TimingPathExtractor | 高 |
| 2 | 资源利用 | ResourceEstimation | 高 |
| 3 | 时序收敛 | TimingDepthAnalyzer | 高 |
| 4 | 功耗 | PowerEstimator | 中 |
| 5 | 时钟设计 | ClockTreeAnalyzer | 高 |
| 6 | 复位设计 | ResetDomainAnalyzer | 高 |
| 7 | CDC | CDCAnalyzer | 高 |
| 8 | 可测试性 | - | 低 |
| 9 | 覆盖率 | CoverageGenerator | 高 |
| 10 | 可靠性 | XValueDetector | 高 |
| 11 | 接口合规 | ProtocolChecker | 中 |
| 12 | 模块互联 | ConnectionTracer | 中 |

======================================================================
附录 C: 功耗分析算法 (简单实现)
======================================================================

## 功耗组成

```
P_total = P_dynamic + P_static
```

## 简单估算公式

```python
P_total ≈ (LUTs × 1.0 + FFs × 0.5 + DSPs × 5.0) × f_MHz × α_avg / 1000  # mW
```

## 固定比例分配

- Clock: 35%
- Logic: 45%
- Memory: 15%
- I/O: 5%

======================================================================
附录 D: Risk Identification 子任务 (Phase 1)
======================================================================

## Phase 1: 风险识别 (已完成)

1.1 Coverage Gap Finding - analyze_coverage_gaps
1.2 CDC Risk Detection - CDCAnalyzer
1.3 Multi-Driver Risk - MultiDriverDetector
1.4 Uninitialized Risk - UninitializedDetector
1.5 X-Propagation Risk - XValueDetector
1.6 Clock Domain Risk - ClockTreeAnalyzer
1.7 Reset Domain Risk - ResetDomainAnalyzer
1.8 Interface Risk - ConnectionTracer
1.9 Resource Exhaustion - ResourceEstimation
1.10 Timing Risk - TimingPathExtractor

## Phase 2: 风险评估 (待实现)

2.1 Probability Calc - 规则引擎
2.2 Impact Assessment - 规则引擎
2.3 Severity Ranking - 风险矩阵
2.4 Likelihood Calc - 复杂度计算
2.5 Risk Scoring - 评分模型

## Phase 3: 风险缓解 (待实现)

3.1 Test Suggestion - 规则库
3.2 Priority Setting - 人工+规则
3.3 Action Item - 模板
3.4 Escalation - 升级决策
3.5 Track Progress - 周期性检查

======================================================================

======================================================================
附录 E: 点子收集方法论 - 从实际工作场景出发
======================================================================

## 核心思想

"工程师在实际写代码的过程中，会遇到哪些不稳定因素？"

通过观察工程师的日常工作流程发现问题点，然后自动化解决。

## 发现问题的方法

### 方法1: 工作流程观察
```
1. 工程师在做什么?
2. 哪里最花时间?
3. 哪里最容易出错?
4. 哪里最无聊?
```

### 方法2: 常见场景分析
```
1. 写测试用例时遇到的问题
2. Debug时遇到的问题
3. 覆盖率分析时遇到的问题
4. 回归测试时遇到的问题
5. 交接项目时遇到的问题
```

### 方法3: 不稳定因素识别
```
1. 手动操作 -> 容易出错
2. 重复操作 -> 浪费时间
3. 容易忘记 -> 需要提醒
4. 难以判断 -> 需要辅助
5. 难以观察 -> 需要可视化
```

======================================================================
## 不稳定因素分类
======================================================================

### A. 信息不稳定性

| 因素 | 描述 | 解决思路 |
|------|------|----------|
| 路径不准确 | Hier path 记忆模糊 | Fuzzy matcher |
| 信号名不确认 | 不确定信号全名 | Auto-complete |
| 接口不清晰 | 不确定信号方向 | 自动分析 |
| 时钟域不明确 | 不确定时钟关系 | 自动分析 |
| 复位域不明确 | 不确定复位关系 | 自动分析 |

### B. 操作不稳定性

| 因素 | 描述 | 解决思路 |
|------|------|----------|
| 重复操作 | 每次都手动做同样的事 | 模板生成 |
| 边界值遗忘 | 忘记边界测试 | 自动生成 |
| 漏覆盖 | 忘记某些case | 自动检查 |
| 配置错误 | 配置参数写错 | 规则检查 |
| 复制错误 | 复制粘贴写错 | 自动转换 |

### C. 判断不稳定性

| 因素 | 描述 | 解决思路 |
|------|------|----------|
| 覆盖完整性 | 不知道是否覆盖完整 | 自动分析 |
| 时序正确性 | 不知道是否正确 | 自动检查 |
| CDC风险 | 不知道是否有风险 | 自动检测 |
| 资源估算 | 不知道用多少 | 自动估算 |
| 性能预估 | 不知道是否达标 | 自动分析 |

### D. 可视化不稳定性

| 因素 | 描述 | 解决思路 |
|------|------|----------|
| 进度不清晰 | 不知道进度如何 | 自动报告 |
| 风险不清楚 | 不知道有什么风险 | 自动报告 |
| 关系不清晰 | 不知道信号间关系 | 可视化 |
| 结构不清晰 | 模块关系不清楚 | 可视化 |
| 瓶颈不清晰 | 不知道性能瓶颈 | 可视化 |

======================================================================
## 点子收集模板
======================================================================

当发现一个问题时，记录以下信息：

```markdown
### 问题: [简短描述]

**场景**: [什么情况下发生]
**影响**: [有什么后果]
**频率**: [高/中/低]
**现有方案**: [如果有的话]

**自动化方案**: [建议的自动化方式]
**难点**: [关键技术点]
**价值**: [高/中/低]
```

### 例子记录

```
### 问题: 采样条件判断

**场景**: 写coverage时不确定信号应该什么时候sample
**影响**: 可能覆盖不对或过度覆盖
**频率**: 中
**现有方案**: 人工分析

**自动化方案**: 自动分析valid/ready/clock关系，建议sample时机
**难点**: 多种协议的sample时机不同
**价值**: 高
```

======================================================================
## 持续收集点子的��法
======================================================================

1. **日常观察**: 记录每天工作中遇到的问题
2. **代码审查**: 从review中提取共性问题
3. **测试复盘**: 从测试失败中发现问题
4. **用户反馈**: 从其他工程师收集问题
5. **效率分析**: 识别耗时最多的操作

======================================================================

======================================================================
附录 F: 工程师日常工作问题收集
======================================================================

## 1. 写测试时的常见问题

| 问题 | 影响 | 频率 | 解决方案 |
|------|------|------|----------|
| "这个信号怎么sample?" | 覆盖不对 | 高 | SampleConditionAnalyzer |
| "边界值是多少?" | 漏覆盖 | 高 | DataPathBoundaryAnalyzer |
| "这个case覆盖了吗?" | 不知道 | 高 | CoverageGapAnalyzer |
| "激励怎么写?" | 费时间 | 中 | TestTemplateGenerator |
| "随机约束怎么写?" | 费时间 | 中 | ConstraintAutoGenerator |

## 2. Debug时的常见问题

| 问题 | 影响 | 频率 | 解决方案 |
|------|------|------|----------|
| "为什么X值?" | 定位慢 | 高 | XPropagationTracer |
| "为什么没有输出?" | 定位慢 | 高 | DataflowTracer |
| "为什么仿真这么慢?" | 效率低 | 中 | ComplexityAnalyzer |
| "波形看不到?" | 效率低 | 中 | WaveformTimeFinder |

## 3. 覆盖率分析时的问题

| 问题 | 影响 | 频率 | 解决方案 |
|------|------|------|----------|
| "哪些没覆盖?" | 不知道 | 高 | CoverageGapAnalyzer |
| "怎么提高?" | 不知道 | 中 | TestSuggestion |
| "coverage怎么这么低?" | 进度慢 | 中 | CoverageTrendAnalyzer |

## 4. 回归测试时的问题

| 问题 | 影响 | 频率 | 解决方案 |
|------|------|------|----------|
| "为什么fail?" | 定位慢 | 高 | FailureClassifier |
| "哪个case fail?" | 不知道 | 中 | TestResultVisualizer |
| "回归太慢?" | 效率低 | 中 | SmartRegression |

## 5. 交接项目时的问题

| 问题 | 影响 | 频率 | 解决方案 |
|------|------|------|----------|
| "这个signal是什么?" | 沟通成本 | 高 | AutoDocumentation |
| "这个module干啥的?" | 沟通成本 | 中 | ModuleSummaryGenerator |
| "怎么run这个test?" | 沟通成本 | 中 | TestRunGuideGenerator |

======================================================================
