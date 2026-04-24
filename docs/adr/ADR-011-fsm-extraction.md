# ADR-011: 状态机提取

> **状态**: Completed
> **日期**: 2026-04-19

---

## 需求概述

从 SystemVerilog 代码中自动识别状态机:
1. 识别状态寄存器
2. 提取状态转换逻辑
3. 识别状态编码方式
4. 输出状态转换图

---

## pyslang/slang FSM 支持

**结论**: pyslang/slang 没有内置 FSM 类型

需要自行实现状态机检测算法。

---

## FSM 检测算法

### 状态机模式识别

根据 IEEE 1800 SystemVerilog 标准，FSM 通常具有以下特征:

#### Pattern 1: 典型状态机 (Always_ff + Case)

```systemverilog
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        state <= IDLE;
    else
        state <= next_state;
end

always_comb begin
    case (state)
        IDLE: begin
            if (start) next_state = WORK;
            else next_state = IDLE;
        end
        WORK: begin
            if (done) next_state = IDLE;
            else next_state = WORK;
        end
    endcase
end
```

#### Pattern 2: 单 always_ff 状态机

```systemverilog
always_ff @(posedge clk) begin
    case (state)
        IDLE: if (start) state <= WORK;
        WORK: if (done) state <= IDLE;
    endcase
end
```

---

## 算法方案

### Option A: 模式匹配

```
1. 查找 always_ff 块
2. 在 always_ff 中查找 case/if 语句
3. 识别状态变量 (通常是 enum 或 parameter)
4. 构建状态转换图
```

| 优点 | 缺点 |
|------|------|
| 简单快速 | 可能误判 |
| 容易实现 | 依赖代码风格 |

### Option B: 数据流分析

```
1. 追踪所有 always_ff 寄存器
2. 分析每个寄存器的驱动逻辑
3. 识别状态变量 (被 case/if 驱动)
4. 提取转换条件
```

| 优点 | 缺点 |
|------|------|
| 更准确 | 复杂 |
| 独立于编码风格 | 性能较低 |

### Option C: 综合分析

```
1. 模式匹配 + 数据流结合
2. 多重验证 FSM 假设
3. 输出置信度
```

| 优点 | 缺点 |
|------|------|
| 最准确 | 最复杂 |
| 可检测边界情况 | 需要多次遍历 |

---

## 推荐方案

**Option B (数据流分析)**: 更准确地识别状态机，不依赖编码风格

---

## 输出格式

```python
@dataclass
class FSMState:
    name: str
    encoding: int
    is_reset: bool
    transitions: List[tuple]  # (condition, next_state)

@dataclass
class FSMInfo:
    name: str
    state_var: str
    states: List[FSMState]
    reset_state: str
    encoding_type: str  # binary, onehot, gray, auto
    confidence: float
    code_locations: List[CodeLocation]
```

---

## FSM 识别标准 (IEEE 1800)

根据标准，FSM 由以下部分组成:

1. **状态寄存器** (state register)
   - 存储当前状态
   - 通常在 always_ff 块中

2. **状态转换逻辑** (state transition logic)
   - 确定下一状态
   - 通常在 always_comb 中

3. **状态输出逻辑** (state output logic)
   - 根据当前状态产生输出
   - 可能在 always_ff 或 always_comb 中

### 状态变量识别特征

- 被赋值给 `next_state` 或类似名称
- 在 case 语句的敏感列表中
- 通常使用 enum 或 parameter 定义状态

---

*开始时间: 2026-04-19*


---

## 实现完成

### 算法: Option B (数据流分析)

1. 查找 always_ff 块中的 `state <= next_state` 模式
2. 查找 always_comb 块中的 `case (state)` 模式
3. 提取状态名和转换关系
4. 识别复位状态
5. 计算置信度

### 功能:
- 自动识别状态变量
- 提取状态转换图
- 识别复位状态
- 计算置信度
- CLI 命令: `fsm`

### 测试:
```
FSM: fsm_state
State Variable: state
Reset State: IDLE
States: IDLE [RESET], WORK
Transitions: IDLE --> WORK, WORK --> IDLE
```

---

*完成时间: 2026-04-19*
