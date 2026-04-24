# ADR-009: Module IO Spec 提取

> **状态**: Planning
> **日期**: 2026-04-19

---

## 需求概述

提取 module 的 IO 规范，包含:
1. 基本信息
2. 每个信号每个 bit 的用途分析
3. 信号分类 (控制/数据/时钟/复位)
4. 数据链路图 (带代码位置)

---

## 任务拆解

### Phase 1: 基础信息提取

| 任务 | 描述 | 预估 |
|------|------|------|
| 1.1 端口提取 | 提取 module 的所有 input/output/inout 端口 | 1h |
| 1.2 端口属性 | 宽度、方向、有无默认值 | 1h |
| 1.3 模块属性 | 名称、参数、层级 | 0.5h |

### Phase 2: Bit 用途分析

| 任务 | 描述 | 预估 |
|------|------|------|
| 2.1 单bit分析 | 逐bit 分析使用方式 | 2h |
| 2.2 向量分析 | 分析 [x:y] 范围的每bit用途 | 2h |
| 2.3 统一性判断 | 判断每bit用途是否一致 | 1h |

### Phase 3: 信号分类

| 任务 | 描述 | 预估 |
|------|------|------|
| 3.1 时钟识别 | 识别 clk 相关信号 | 1h |
| 3.2 复位识别 | 识别 rst 相关信号 | 1h |
| 3.3 控制信号 | 识别 valid/ready/enable 等 | 1.5h |
| 3.4 数据信号 | 识别 data/addr 等 | 1h |
| 3.5 分类器设计 | 可扩展分类规则 | 1h |

### Phase 4: 数据链路图

| 任务 | 描述 | 预估 |
|------|------|------|
| 4.1 驱动追踪 | 追踪每个 input 的驱动来源 | 2h |
| 4.2 负载追踪 | 追踪每个 output 的负载目标 | 2h |
| 4.3 链路构建 | 构建完整的 IO 数据流 | 2h |
| 4.4 代码关联 | 添加文件名和行号 | 1h |
| 4.5 可视化 | 生成 DOT/文本图 | 1h |

---

## 输出格式设计

### IO Spec 结构

```python
@dataclass
class IOSpec:
    module_name: str
    parameters: Dict[str, str]
    ports: List[Port]
    
@dataclass
class Port:
    name: str
    direction: str  # input/output/inout
    width: int
    bits: List[BitUsage]  # 每bit的用途
    category: str  # clock/reset/control/data
    driver: str  # 驱动来源
    load: str  # 负载目标
    code_location: CodeLocation

@dataclass  
class BitUsage:
    bit_index: int
    usage: str  # "data", "enable", "address", "control"
    consistent: bool  # 是否与相邻bit一致

@dataclass
class DataFlow:
    input_port: str
    output_port: str
    path: List[FlowNode]
    
@dataclass
class FlowNode:
    signal: str
    code_location: CodeLocation
```

---

## 算法方案

### 信号分类算法

#### Option A: 规则匹配

```
1. 定义分类规则:
   - 时钟: 名称包含 clk, clock
   - 复位: 名称包含 rst, reset
   - 控制: 名称包含 vld, rdy, en, valid, ready, enable
   - 数据: 名称包含 data, addr, din, dout
2. 匹配规则
```

**优点**: 简单快速
**缺点**: 覆盖率依赖规则

#### Option B: 语义分析

```
1. 分析信号在代码中的使用方式:
   - always_ff @(posedge clk) -> 时钟
   - if (rst) -> 复位
   - if (valid) ... -> 控制
   - 直接赋值 -> 数据
2. 推断分类
```

**优点**: 更准确
**缺点**: 实现复杂

### 推荐: Option A + Option B 组合

---

## 实现计划

| Phase | 任务 | 预估总计 |
|-------|------|----------|
| Phase 1 | 基础信息 | 2.5h |
| Phase 2 | Bit 分析 | 5h |
| Phase 3 | 分类 | 5.5h |
| Phase 4 | 链路图 | 8h |
| **总计** | | **21h** |

---

*开始时间: 2026-04-19*
