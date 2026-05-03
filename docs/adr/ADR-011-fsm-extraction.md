# ADR-011: 状态机提取

> **状态**: Completed
> **日期**: 2026-04-19
> **更新**: 2026-05-03

---

## 需求概述

从 SystemVerilog 代码中自动识别状态机:
1. 识别状态寄存器
2. 提取状态转换逻辑
3. 计算复杂度
4. 检测不可达状态和死锁

---

## 实现方案

### 技术选择

**结论**: 使用 pyslang AST 实现，不使用正则表达式

原因：
- pyslang 解析 SystemVerilog 生成完整 AST
- AST 可以准确获取状态机结构和枚举定义
- 符合 IEEE 1800-2017 标准

---

## IEEE 1800-2017 Section 40.4 FSM Recognition

根据 IEEE 1800-2017 LRM Section 40.4，状态机识别优先级如下：

### 1. Pragma 方式 (最高优先级)

```systemverilog
/* tool state_vector state_q */
module fsm;

/* tool enum my_fsm_state */
typedef enum logic [1:0] {IDLE, RUN, DONE} my_fsm_state;
```

### 2. 标准识别方式

| Section | 模式 | 示例 |
|---------|------|------|
| 40.4.1 | `tool state_vector signal` | `/* tool state_vector state_q */` |
| 40.4.2 | Part-select | `state[1:0]` 用于 one-hot |
| 40.4.3 | Concatenation | `{state, ctrl}` 多位宽 |
| 40.4.4 | Enum | 从 typedef enum 识别 |
| 40.4.5 | 双信号 | current + next 声明 |
| Fallback | Pattern | case + always_ff 模式 |

---

## 实现架构

### 核心方法

```python
class FSMAnalyzer:
    def _walk(node)           # 遍历 AST 节点
    def _check_pragma(root)   # 检查 40.4 pragma
    def _check_enum(root)     # 40.4.4 枚举识别
    def extract_fsm(module)   # 提取 FSM
    def analyze(fsm)         # 分析复杂度
```

### 实现流程

```
1. _check_pragma()
   - 检查 /* tool state_vector */ 注释
   - 提取信号名和枚举名
   
2. _check_enum() (40.4.4)
   - 遍历 EnumDeclaration 节点
   - 提取枚举常量作为状态列表
   
3. _extract_fsm_from_ast()
   - CaseStatement_first: 优先识别 case 表达式作为 state_var
   - Fallback: 优先级 _current > _q > _state
   - 从 StandardCaseItem.expressions 提取状态名
   - 从 StandardCaseItem.clause 提取跳转目标
   
4. analyze()
   - 计算复杂度 = 状态数 × 平均跳转数
   - BFS 查找不可达状态
   - Grade 评分 (A/B/C/D)
```

---

## 测试结果

### 1. Corner Case 测试 (test_fsm_corners.sv)

| Module | States | Transitions | Grade |
|--------|--------|-------------|-------|
| fsm_onehot | 4 | 4 | A |
| fsm_three_seg | 4 | 4 | A |
| fsm_multi | 4 | 4 | A |
| fsm_complex_cond | 4 | 4 | A |
| fsm_illegal_recover | 4 | 4 | A |
| fsm_with_counter | 4 | 4 | A |

### 2. OpenTitan 真实项目

| Module | States | Transitions | Grade |
|--------|--------|-------------|-------|
| pwrmgr_fsm | 17 | 16 | D |
| pwrmgr_slow_fsm | 12 | 11 | D |

---

## 输出示例

```
============================================================
FSM ANALYSIS: state_q
============================================================

IEEE 1800-2017 Section 40.4 Source: pattern
Statistics: States=17, Transitions=16
Complexity=16, Grade=D
Reset State=FastPwrStateLowPower

Unreachable: FastPwrStateNvmIdleChk, FastPwrStateResetPrep

Encoding: {'FastPwrStateLowPower': '000', ...}

States:
  FastPwrStateLowPower [INIT] (in:1 out:1)
  ...
```

---

## 代码位置

- 实现: `src/debug/analyzers/fsm_analyzer.py`
- 测试: `tests/targeted/test_fsm_corners.sv`

---

## 相关文档

- IEEE 1800-2017 LRM Section 40.4
- SV_FSM_Recognition.md (标准参考)
