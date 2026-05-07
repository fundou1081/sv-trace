# SV-Trace 实施优先级分析

**时间**: 2026-04-26
**版本**: v1.0
**依据**: 已有代码能力 + 需求优先级 + 技术方案评估

---

## 一、已有能力盘点

### 1.1 代码结构

```
src/
├── parse/           # RTL解析 (90%)
│   ├── parser.py    # 核心解析器
│   ├── constraint.py # 约束解析
│   └── ...
├── trace/          # 数据流追踪 (70%)
│   ├── driver.py   # Driver分析
│   ├── load.py     # Load分析
│   └── ...
├── debug/          # 调试分析 (75%)
│   ├── analyzers/
│   │   ├── cdc.py              # CDC分析 (80%)
│   │   ├── fsm_analyzer.py     # FSM分析 (85%)
│   │   ├── multi_driver_detector.py  # 多驱动检测 (75%)
│   │   ├── coverage_generator.py     # 覆盖率生成 (60%)
│   │   ├── project_analyzer.py       # 项目分析 (50%)
│   │   ├── reset_domain_analyzer.py  # 复位分析 (70%)
│   │   └── power_estimator.py       # 功耗估算 (50%)
│   ├── fsm/         # FSM相关
│   └── iospec/      # 接口解析
├── lint/           # 代码检查 (60%)
└── apps/           # 应用层
```

### 1.2 能力矩阵

| 能力 | 模块 | 完成度 | 对应需求 |
|------|------|--------|----------|
| RTL解析 | parse/parser.py | 90% | R01基础 |
| FSM分析 | debug/fsm/ | 85% | R10部分 |
| CDC分析 | debug/analyzers/cdc.py | 80% | R54-R56 |
| 多驱动检测 | multi_driver_detector.py | 75% | R87 |
| 数据流追踪 | trace/driver.py, load.py | 70% | R01部分 |
| 覆盖率分析 | coverage_generator.py | 60% | R10部分 |
| 功耗估算 | power_estimator.py | 50% | R99部分 |
| 复位分析 | reset_domain_analyzer.py | 70% | R57-R59 |
| 项目分析 | project_analyzer.py | 50% | R03部分 |
| 约束解析 | constraint.py | 40% | R07部分 |
| SVA生成 | formal_verification.py | 60% | R42部分 |

---

## 二、需求优先级与匹配度

### 2.1 P0 需求匹配度

| ID | 需求 | 已有能力 | 差距 | 优先级 |
|----|------|----------|------|--------|
| **R01** | 信号分类与可视化 | RTL解析Driver/Load | 缺分类规则+可视化 | ⭐⭐⭐ 高 |
| **R03** | 测试管理CRUD | project_analyzer部分 | 需完整CRUD实现 | ⭐⭐⭐ 高 |
| **R05** | Bug追踪系统 | 无 | 需数据库设计 | ⭐⭐⭐ 高 |
| R02 | Interface生成 | connection trace | 缺代码生成 | ⭐⭐ 中 |
| R04 | 增量测试识别 | 无 | 需git集成 | ⭐ 低(依赖R03) |
| R119 | CDC协议文档 | cdc.py已有 | 缺文档模板 | ⭐⭐ 中 |

### 2.2 P1 需求匹配度

| ID | 需求 | 已有能力 | 差距 | 优先级 |
|----|------|----------|------|--------|
| **R87** | 多驱动检测 | multi_driver_detector.py | 需完善+报告 | ⭐⭐⭐ 高 |
| **R88** | 死代码检测 | 代码分析能力 | 需完善逻辑 | ⭐⭐⭐ 高 |
| **R54-R56** | CDC覆盖增强 | cdc.py已有 | 需增强+文档 | ⭐⭐⭐ 高 |
| R10 | 覆盖模型生成 | coverage_generator.py | 需增强 | ⭐⭐ 中 |
| R07 | 约束自动生成 | constraint.py | 需完善 | ⭐⭐ 中 |
| R99 | 功耗热点识别 | power_estimator.py | 需报告增强 | ⭐⭐ 中 |
| R72 | 版本标签系统 | 无 | 需git tag集成 | ⭐⭐ 中 |

---

## 三、推荐实施路线图

```
┌─────────────────────────────────────────────────────────────────────┐
│                     推荐开发顺序                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Step 1: R03 测试管理CRUD (编译工具)                                │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                              │
│  理由: 测试管理是所有验证流程的基础                                  │
│  依赖: 无                                                           │
│  价值: 高 - 解决"测试用例管理混乱"问题                              │
│                                                                     │
│  Step 2: R05 Bug追踪系统 (编译工具)                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                              │
│  理由: Bug追踪是质量保障的基础                                      │
│  依赖: 无                                                           │
│  价值: 高 - 解决"Bug丢失/重复/追踪混乱"问题                         │
│                                                                     │
│  Step 3: R01 信号分类 (Hybrid)                                      │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                              │
│  理由: 利用已有RTL解析能力，增强理解RTL                             │
│  依赖: 已有RTL解析 + 新增分类规则Skill                              │
│  价值: 高 - 解决"127个信号难以理解"问题                             │
│                                                                     │
│  Step 4: R119 CDC协议文档 (Skill)                                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                              │
│  理由: 利用已有cdc.py，添加文档模板                                 │
│  依赖: 已有cdc.py                                                   │
│  价值: 中 - 解决"CDC信息难以文档化"问题                             │
│                                                                     │
│  Step 5: R87/R88 代码质量检查增强 (编译工具)                       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                              │
│  理由: 增强现有multi_driver_detector                                │
│  依赖: 已有代码                                                     │
│  价值: 高 - 解决"RTL质量问题难以发现"问题                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 四、详细实施方案

### Step 1: R03 测试管理CRUD

#### 目标
建立测试用例的增删改查能力

#### 目录结构
```
src/verify/
├── __init__.py
├── test_manager.py      # 核心CRUD
├── test_case.py         # 测试用例数据模型
├── test_suite.py        # 测试套件
├── test_result.py       # 测试结果
└── reports/
    ├── __init__.py
    └── test_report.py   # 报告生成
```

#### 数据模型
```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class TestCase:
    """测试用例"""
    id: str
    name: str
    module: str
    level: str  # P0/P1/P2
    status: str  # pass/fail/blocked/not_run
    coverage_items: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    owner: str = ""
    tags: List[str] = field(default_factory=list)
    description: str = ""
    seed: Optional[str] = None
    
    # 关联
    related_bugs: List[str] = field(default_factory=list)
    related_spec: str = ""

@dataclass
class TestSuite:
    """测试套件"""
    id: str
    name: str
    test_ids: List[str]
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
```

#### CLI工具
```bash
# 测试用例管理
verify-test add --name "uart_baud_rate" --module uart --level P0
verify-test list --module uart
verify-test update 001 --status pass
verify-test remove 001
verify-test get 001

# 测试套件
verify-suite create --name "regression_basic" --tests "001,002,003"
verify-suite add-test regression_basic 004
verify-suite list
verify-suite run regression_basic

# 报告
verify-test report --format html --output report.html
verify-test report --format json --output report.json
```

#### Skill模板
```yaml
# verify-test-skill/SKILL.md
name: verify-test-manager
description: 测试用例管理系统，用于管理验证过程中的测试用例

commands:
  add: 添加测试用例
  list: 列出测试用例
  update: 更新测试用例状态
  remove: 删除测试用例
  report: 生成测试报告
```

---

### Step 2: R05 Bug追踪系统

#### 目标
建立Bug的全生命周期管理

#### 目录结构
```
src/bugs/
├── __init__.py
├── bug_tracker.py       # 核心CRUD
├── bug_case.py         # Bug数据模型
├── bug_status.py       # 状态机
├── bug_stats.py        # 统计分析
└── reports/
    ├── __init__.py
    └── bug_report.py   # 报告
```

#### 数据模型
```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

class BugSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class BugStatus(Enum):
    NEW = "new"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    FIXED = "fixed"
    CLOSED = "closed"
    WONTFIX = "wontfix"

@dataclass
class BugCase:
    """Bug用例"""
    id: str
    title: str
    severity: BugSeverity
    status: BugStatus
    module: str
    
    # 详情
    description: str = ""
    reproduce_steps: str = ""
    
    # 关联
    test_case_id: Optional[str] = None
    related_spec: str = ""
    related_bugs: List[str] = field(default_factory=list)
    
    # 复现
    seed: Optional[str] = None
    reproduce_count: int = 0
    reproduce_rate: float = 0.0
    
    # 时间
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # 人员
    reporter: str = ""
    assignee: str = ""
    owner: str = ""
    
    # 附件
    waveforms: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
```

#### CLI工具
```bash
# Bug管理
bug-tracker create --title "TX数据错误" --severity high --module uart
bug-tracker list --status new --severity high
bug-tracker update 001 --status confirmed --assignee john
bug-tracker close 001

# 复现追踪
bug-tracker reproduce 001 --seed 0x12345678 --count 100
bug-tracker stats --severity

# 报告
bug-tracker report --format html --output bug_report.html
bug-tracker report --trend --days 30
```

---

### Step 3: R01 信号分类 (Hybrid)

#### 目标
将信号自动分类为 clock/reset/data/control/port

#### 目录结构
```
src/trace/
├── signal_classifier.py   # Hybrid核心
├── classification_rules.py # 分类规则 (Skill)
├── signal_categories.py   # 分类结果
└── visualization.py      # 可视化
```

#### 分类规则 (Skill)
```python
# classification_rules.py

# Clock信号识别模式
CLOCK_PATTERNS = [
    r'.*clk.*',
    r'.*clock.*',
    r'i_.*_clk',
    r'.*_clk_i$',
    r'clk_.*',
]

# Reset信号识别模式
RESET_PATTERNS = [
    r'.*rst.*',
    r'.*reset.*',
    r'.*_n$',        # active low
    r'.*async.*',   # async reset
]

# Data信号识别模式
DATA_PATTERNS = [
    r'.*data.*',
    r'.*din.*',
    r'.*dout.*',
    r'.*q$',         # register output
    r'.*d$',         # register input
    r'.*wr_data.*',
    r'.*rd_data.*',
]

# Control信号识别模式
CONTROL_PATTERNS = [
    r'.*en.*',
    r'.*enable.*',
    r'.*valid.*',
    r'.*ready.*',
    r'.*load.*',
    r'.*wr.*',
    r'.*rd.*',
    r'.*req.*',
    r'.*ack.*',
]

# Status信号识别模式
STATUS_PATTERNS = [
    r'.*flag.*',
    r'.*status.*',
    r'.*busy.*',
    r'.*done.*',
    r'.*empty.*',
    r'.*full.*',
    r'.*error.*',
    r'.*irq.*',
]
```

#### 输出示例
```markdown
=== 信号分类报告: uart_controller ===

Clock Signals (3):
├── i_clk              [input, 100MHz]
├── uart_clk           [generated, 115200Hz]
└── i_clk_gated       [gated]

Reset Signals (2):
├── i_rst_n            [input, active low, async]
└── core_rst_n         [synchronized, 2FF]

Data Signals (45):
├── rx_data[7:0]       [input, 8bit]
├── tx_data[7:0]       [output, 8bit]
├── fifo_din[7:0]      [internal, 8bit]
└── ...

Control Signals (12):
├── tx_en              [input, tx enable]
├── rx_valid           [output, rx data valid]
├── fifo_full          [output]
└── ...

Status Signals (8):
├── tx_busy            [output]
├── rx_busy            [output]
├── parity_err         [output]
└── ...

Port Summary:
├── Inputs: 23
├── Outputs: 18
├── Bidirs: 0
└── Internal: 86
```

---

### Step 4: R119 CDC协议文档

#### 目标
将CDC分析结果输出为标准文档

#### 目录结构
```
templates/
├── cdc_protocol_template.md
└── cdc_checklist.md
```

#### CDC文档模板
```markdown
# CDC协议文档

## 模块: {{module_name}}
## 版本: {{version}}
## 日期: {{date}}

---

## 1. 时钟域概览

| 时钟域 | 频率 | 来源 | 用途 |
|--------|------|------|------|
| {{domain}} | {{freq}} | {{source}} | {{purpose}} |

## 2. CDC路径清单

### 2.1 跨时钟域路径

| 路径 | 源时钟 | 目标时钟 | 同步器类型 | 风险等级 |
|------|--------|----------|------------|----------|
| {{path}} | {{src}} | {{dst}} | {{sync}} | {{risk}} |

### 2.2 同步器配置

#### 2.2.1 {{sync_name}}
- **类型**: {{sync_type}} (1-bit/2-bit/握手)
- **级数**: {{stages}}级FF
- **数据宽度**: {{width}} bits
- **冒险条件**: {{hazard}}

#### 验证要点:
{{verification_points}}

## 3. 握手协议

{{handshake_protocol}}

## 4. CDC检查清单

- [ ] 所有跨时钟域路径已识别
- [ ] 同步器类型选择正确
- [ ] 复位同步释放处理正确
- [ ] 多位数据跨时钟域使用格雷码或握手
- [ ] CDC路径有相应SVA断言
- [ ] CDC覆盖率达到目标

## 5. 已知风险

{{known_risks}}

## 6. 验证状态

| CDC路径 | 验证状态 | 覆盖率 |
|---------|----------|--------|
| {{path}} | {{status}} | {{coverage}} |
```

---

### Step 5: R87/R88 代码质量增强

#### 目标
完善多驱动和死代码检测

#### 目录结构
```
src/lint/
├── enhanced_multi_driver.py   # 增强多驱动检测
├── dead_code_detector.py      # 死代码检测
├── code_quality_report.py    # 质量报告
└── rules/
    ├── __init__.py
    ├── multi_driver_rules.py
    └── dead_code_rules.py
```

#### 多驱动检测增强
```python
class EnhancedMultiDriverDetector:
    """增强版多驱动检测"""
    
    def __init__(self, parser):
        self.parser = parser
        self.driver_collector = DriverCollector(parser)
    
    def analyze(self) -> MultiDriverReport:
        """执行完整分析"""
        # 1. 收集所有驱动
        drivers = self.driver_collector.collect()
        
        # 2. 检测多驱动冲突
        conflicts = self._find_conflicts(drivers)
        
        # 3. 分类冲突类型
        classified = self._classify_conflicts(conflicts)
        
        # 4. 评估严重性
        severity = self._assess_severity(classified)
        
        # 5. 生成修复建议
        suggestions = self._generate_suggestions(severity)
        
        return MultiDriverReport(
            conflicts=classified,
            severity=severity,
            suggestions=suggestions
        )
    
    def _classify_conflicts(self, conflicts):
        """分类冲突类型"""
        # ALWAYS_FF_MULTI: 多个always_ff驱动同一信号
        # ALWAYS_COMB_MULTI: 多个always_comb驱动同一信号
        # ASSIGN_MULTI: 多个assign驱动同一信号
        # FF_COMB_MIX: always_ff和always_comb混用
        # LATCH_FF_MIX: latch和always_ff混用
        pass
    
    def _assess_severity(self, conflicts):
        """评估严重性"""
        # Critical: 多驱动导致X传播
        # High: 可能导致功能错误
        # Medium: 可能导致仿真问题
        # Low: 风格问题
        pass
```

#### 死代码检测
```python
class DeadCodeDetector:
    """死代码检测"""
    
    def __init__(self, parser):
        self.parser = parser
    
    def find_dead_code(self):
        """查找死代码"""
        results = {
            'dead_signals': [],      # 赋值但从不使用的信号
            'dead_blocks': [],       # 永远不执行的代码块
            'dead_cases': [],        # 永远不匹配的条件
            'redundant_code': [],    # 冗余代码
        }
        
        # 检测策略
        # 1. 活跃变量分析
        # 2. 控制流分析
        # 3. 条件覆盖分析
        
        return results
```

---

## 五、总结

### 5.1 推荐优先级

| 优先级 | 需求 | 技术方案 | 工作量 | 价值 |
|--------|------|----------|--------|------|
| 1 | R03 测试管理CRUD | 编译工具 | 中 | 高 |
| 2 | R05 Bug追踪系统 | 编译工具 | 中 | 高 |
| 3 | R01 信号分类 | Hybrid | 中 | 高 |
| 4 | R119 CDC协议文档 | Skill | 低 | 中 |
| 5 | R87/R88 代码质量增强 | 编译工具 | 中 | 高 |

### 5.2 技术方案分布

```
编译工具: 3个 (R03, R05, R87/R88)
Hybrid: 1个 (R01)
Skill: 1个 (R119)
```

### 5.3 实施时间估算

```
Step 1: R03 测试管理CRUD - 1周
Step 2: R05 Bug追踪系统 - 1周
Step 3: R01 信号分类 - 1周
Step 4: R119 CDC协议文档 - 2-3天
Step 5: R87/R88 代码质量 - 1周

总计: 约4-5周
```

---

*文档版本: v1.0*
*创建时间: 2026-04-26*
*最后更新: 2026-04-26 23:59*
