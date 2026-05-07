# SV-Trace 项目概览

**版本**: v1.0
**时间**: 2026-04-27
**状态**: 核心功能完成

---

## 一、项目概述

SV-Trace 是一个 SystemVerilog RTL 分析工具集，旨在帮助验证工程师和设计工程师快速理解、分析和追踪RTL设计。

### 1.1 目标

- 快速理解陌生RTL设计结构
- 自动化验证流程中的重复工作
- 建立跨部门协作的标准化文档

### 1.2 技术栈

| 组件 | 技术 |
|------|------|
| 解析器 | pyslang |
| 语言 | Python 3.11+ |
| 存储 | JSON |
| CLI | 原生Python argparse |

---

## 二、需求实现状态

### 2.1 已完成需求 (51个)

#### P0 核心需求 (4/4)

| ID | 需求 | 模块 | 文件 |
|----|------|------|------|
| R01 | 信号分类与可视化 | trace | signal_classifier.py |
| R03 | 测试管理CRUD | verify | test_manager.py |
| R05 | Bug追踪系统 | bugs | bug_tracker.py |
| R119 | CDC协议文档 | templates | cdc_protocol.md |

#### P1 高优先级需求 (22/47)

| ID | 需求 | 模块 | 文件 |
|----|------|------|------|
| R87 | 多驱动检测 | lint | code_quality.py |
| R88 | 死代码检测 | lint | code_quality.py |
| R84 | Spec模板 | templates | spec_template.md |
| R105 | 对接检查清单 | templates | delivery_checklist.md |
| R107 | RDL寄存器模板 | templates | rdl_template.md |
| R123 | 时钟约束模板 | templates | sdc_template.md |
| R127 | IO约束模板 | templates | io_constraint_template.md |
| R29 | 规格边界检测 | skills | spec-corner-case/ |
| R34 | Feature分级 | skills | feature-prioritizer/ |
| R36 | Spec完整性检查 | skills | spec-checker/ |
| R52 | Spec一致性验证 | skills | spec-checker/ |
| R100 | 时钟门控建议 | skills | clock-gating-advisor/ |
| R14 | Debug知识库 | skills | debug-knowledge-base/ |
| R38 | 跨团队沟通 | skills | team-communication-log/ |
| R98 | 时序修复建议 | skills | timing-fix-guide/ |
| R08 | 回归结果数据库 | regression | regression_db.py |
| R72 | 版本标签系统 | vcs | version_tag.py |
| R73 | 变更日志 | changelog | change_log.py |
| R06 | Spec变更追踪 | spec | spec_tracker.py |
| R10 | 覆盖模型生成 | verify | coverage_model.py |
| R42 | DFT覆盖检查 | dft | dft_coverage.py |
| R31 | 代码所有权 | vcs | code_ownership.py |

#### P2 中优先级需求 (5/28)

| ID | 需求 | 模块 | 文件 |
|----|------|------|------|
| R13 | 报告自动生成 | reports | report_generator.py |
| R28 | 语法兼容性检查 | lint | syntax_check.py |
| R07 | 约束自动生成 | verify | constraint_generator.py |
| R119 | CDC协议文档 | skills | cdc-doc-skill/ |
| R119 | CDC验证清单 | skills | cdc-doc-skill/ |

#### Skill类需求 (12个)

| Skill | 用途 |
|-------|------|
| verify-test-manager | 测试管理 |
| bug-tracker | Bug追踪 |
| signal-classifier | 信号分类 |
| code-quality-checker | 代码质量 |
| cdc-documentation | CDC文档 |
| spec-checker | Spec检查 |
| feature-prioritizer | Feature分级 |
| spec-corner-case | 边界条件 |
| clock-gating-advisor | 时钟门控 |
| timing-fix-guide | 时序修复 |
| debug-knowledge-base | Debug知识 |
| team-communication-log | 沟通记录 |

### 2.2 待实现需求 (36个)

| ID | 需求 | 方案 | 难度 |
|----|------|------|------|
| R02 | Interface代码生成 | Hybrid | 高 |
| R04 | 增量测试识别 | Hybrid | 高 |
| R09 | Reference model生成 | Hybrid | 极高 |
| R11 | 波形集成 | 工具 | 极高 |
| R12 | 失败用例聚类 | Hybrid | 中 |
| R15 | 用例抽象分层 | Skill | 中 |
| R16 | Spec文本转验证点 | Skill+ML | 极高 |
| R17 | 风险评估报告 | Skill | 中 |
| R18 | Git工作流集成 | 工具 | 中 |
| R19 | 场景矩阵工具 | Skill | 中 |
| R20 | 随机种子管理 | 工具 | 低 |
| R22 | 测试适配自动化 | Hybrid | 高 |
| R24 | Bug复现率统计 | 工具 | 低 |
| R25 | Seed数据库 | 工具 | 低 |
| R26 | Regression对比 | 工具 | 中 |
| R27 | 仿真器抽象层 | 工具 | 高 |
| R30 | 遗漏测试识别 | Hybrid | 中 |
| R35 | 影响评估 | Skill | 中 |
| R37 | 边界条件提取 | Skill | 中 |
| R40 | 接口时序变更检测 | 工具 | 中 |
| R41 | 验证工作评估 | Skill | 中 |
| R44 | 模式切换测试 | Hybrid | 高 |
| R45 | 时序路径文档 | 工具 | 中 |
| R47 | 时序等效性检查 | Skill | 高 |
| R48 | 功耗域定义 | Skill | 中 |
| R49 | 使能信号清单 | Skill | 低 |
| R50 | 门控覆盖率 | Hybrid | 中 |
| R51 | 功耗模式状态机 | Hybrid | 高 |
| R54 | CDC协议规范 | Skill | 中 |
| R55 | CDC验证清单 | Skill | 低 |
| R56 | CDC覆盖率 | Hybrid | 中 |
| R57 | 复位策略文档 | Skill | 低 |
| R58 | 复位覆盖率 | Hybrid | 中 |
| R59 | 复位时序测试 | Skill | 中 |

---

## 三、项目结构

```
sv-trace/
├── src/
│   ├── parse/              # RTL解析
│   │   ├── parser.py       # 核心解析器
│   │   └── ...
│   ├── trace/             # 数据流追踪
│   │   ├── signal_classifier.py   # 信号分类
│   │   ├── driver.py      # Driver分析
│   │   └── load.py        # Load分析
│   ├── debug/             # 调试分析
│   │   ├── analyzers/
│   │   │   ├── cdc.py    # CDC分析
│   │   │   └── ...
│   │   └── fsm/          # FSM分析
│   ├── lint/              # 代码检查
│   │   ├── code_quality.py      # 质量检查
│   │   └── syntax_check.py      # 语法兼容
│   ├── verify/            # 验证工具
│   │   ├── test_manager.py      # 测试管理
│   │   ├── coverage_model.py    # 覆盖模型
│   │   └── constraint_generator.py # 约束生成
│   ├── bugs/              # Bug追踪
│   │   └── bug_tracker.py      # Bug管理
│   ├── regression/         # 回归数据库
│   │   └── regression_db.py    # 回归结果
│   ├── vcs/               # 版本控制
│   │   ├── version_tag.py      # 版本标签
│   │   └── code_ownership.py  # 代码所有权
│   ├── changelog/         # 变更日志
│   │   └── change_log.py      # 变更记录
│   ├── spec/              # Spec追踪
│   │   └── spec_tracker.py     # Spec变更
│   ├── dft/              # DFT检查
│   │   └── dft_coverage.py    # DFT覆盖
│   └── reports/           # 报告生成
│       └── report_generator.py  # 报告生成
├── bin/                   # CLI工具
│   ├── svtrace            # 主入口
│   ├── sv-parse          # 解析
│   ├── sv-fsm            # FSM分析
│   ├── sv-cdc            # CDC分析
│   ├── sv-analyze        # 批量分析
│   ├── sv-signal        # 信号分类
│   ├── sv-quality        # 质量检查
│   ├── verify-test       # 测试管理
│   ├── verify-suite      # 测试套件
│   └── bug-tracker       # Bug追踪
├── skills/               # Agent Skills
│   ├── verify-test-skill/
│   ├── bug-tracker-skill/
│   ├── signal-classifier-skill/
│   ├── code-quality-skill/
│   ├── cdc-doc-skill/
│   ├── spec-checker/
│   ├── feature-prioritizer/
│   ├── spec-corner-case/
│   ├── clock-gating-advisor/
│   ├── timing-fix-guide/
│   ├── debug-knowledge-base/
│   └── team-communication-log/
├── templates/             # 文档模板
│   ├── spec_template.md
│   ├── delivery_checklist.md
│   ├── rdl_template.md
│   ├── sdc_template.md
│   ├── io_constraint_template.md
│   ├── cdc_protocol_template.md
│   └── cdc_checklist.md
└── docs/                 # 文档
    ├── VERIFICATION_SCENARIOS.md
    ├── REQUIREMENTS_ABSTRACTION.md
    ├── TECHNICAL_SOLUTION_ASSESSMENT.md
    ├── PRIORITY_ANALYSIS.md
    └── PROJECT_OVERVIEW.md  # 本文档
```

---

## 四、CLI工具速查

### 4.1 RTL分析

```bash
# 解析
sv-parse design.sv

# FSM分析
sv-fsm design.sv

# CDC分析
sv-cdc design.sv

# 信号分类
sv-signal classify design.sv

# 质量检查
sv-quality check design.sv
```

### 4.2 验证管理

```bash
# 测试管理
verify-test add --name test1 --module uart --level P0
verify-test list --module uart
verify-test update 1 --status pass
verify-test stats

# 测试套件
verify-suite create --name basic --tests 1,2,3
```

### 4.3 Bug追踪

```bash
bug-tracker create --title "TX错误" --module uart --severity high
bug-tracker list --status new
bug-tracker update B1 --status fixed
bug-tracker stats
```

### 4.4 批量分析

```bash
sv-analyze --batch file1.sv file2.sv
sv-analyze --dir ./rtl --pattern "*.sv"
```

---

## 五、使用示例

### 5.1 Python API

```python
# 信号分类
from trace.signal_classifier import SignalClassifier
from parse import SVParser

parser = SVParser()
parser.parse_file('design.sv')

classifier = SignalClassifier()
result = classifier.classify_from_parser(parser)
print(f"Clocks: {len(result.clocks)}")
```

### 5.2 测试管理

```python
from verify.test_manager import TestManager

tm = TestManager('./test_db')
test = tm.add_test(name='uart_test', module='uart', level='P0')
tests = tm.list_tests(module='uart')
```

### 5.3 Bug追踪

```python
from bugs.bug_tracker import BugTracker

bt = BugTracker('./bug_db')
bug = bt.create_bug(title="TX错误", module="uart", severity="high")
bt.record_reproduce("B1", seed="0x1234", attempt_count=100, success_count=5)
```

---

## 六、后续计划

### 6.1 已完成

- [x] P0 核心功能
- [x] P1 高优先级功能
- [x] Skill系统

### 6.2 进行中

- [ ] 完善CLI工具
- [ ] 增强覆盖模型
- [ ] 完善报告生成

### 6.3 待做

- [ ] Reference model生成
- [ ] 波形集成
- [ ] 仿真器抽象层

---

## 七、文档索引

| 文档 | 内容 |
|------|------|
| PROJECT_OVERVIEW.md | 项目概览 |
| VERIFICATION_SCENARIOS.md | 需求场景挖掘 |
| REQUIREMENTS_ABSTRACTION.md | 需求抽象归类 |
| TECHNICAL_SOLUTION_ASSESSMENT.md | 技术方案评估 |
| PRIORITY_ANALYSIS.md | 实施优先级分析 |

---

*最后更新: 2026-04-27*
