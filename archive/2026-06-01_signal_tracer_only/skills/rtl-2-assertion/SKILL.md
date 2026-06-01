---
name: rtl-to-assertion-generator
description: |
  RTL自动生成SVA断言 AI策略框架。
  本框架提供从RTL代码自动生成SystemVerilog Assertion的方法论。
---

# RTL转SVA断言 AI策略框架

## 1. 目的

从RTL代码自动生成SystemVerilog Assertion (SVA)，提高验证效率。

## 2. 方法论

### 2.1 输入

```
RTL代码 (SystemVerilog)
├── 模块定义
├── 端口声明
├── 时序逻辑
└── 组合逻辑
```

### 2.2 输出

```
SVA Assertions
├── 协议断言
│   ├── APB协议
│   ├── AXI协议
│   └── 握手协议
├── 约束断言
│   ├── 范围检查
│   ├── 有效性检查
│   └── 一致性检查
└── 覆盖率断言
    ├── 状态覆盖
    └── 转移覆盖
```

## 3. 转换流程

```
┌─────────────┐
│  RTL输入   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  代码解析   │  ← pyslang/SVParser
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  模式识别   │  ← LLM/Pattern
│  - 协议    │
│  - 状态机  │
│  - 计数器  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  断言生成   │  ← LLM/Template
│  - 属性    │
│  - 序列    │
│  - 约束    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  断言优化   │  ← LLM/Refine
│  - 简化    │
│  - 去重    │
│  - 覆盖    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  SVA输出   │
└─────────────┘
```

## 4. 断言类型

### 4.1 协议断言

```systemverilog
// APB协议
property p_apb_setup;
    @(posedge clk) disable iff (!rst_n)
        psel && !penable |-> ##1 penable[->1];
endproperty

// 握手协议
property p_handshake;
    @(posedge clk)
        req && !ack |-> until(ack);
endproperty
```

### 4.2 约束断言

```systemverilog
// 范围检查
assert property (@(posedge clk) data inside {[0:255]});

// 有效性检查
assert property (@(posedge clk) valid |-> data != 'x);
```

### 4.3 时序断言

```systemverilog
// 超时检查
assert property (@(posedge clk) 
    req |-> ##[1:100] ack);

// 延迟检查
assert property (@(posedge clk) 
    start |-> ##latency done);
```

## 5. Prompt模板

### 5.1 协议识别Prompt

```markdown
你是一个验证工程师。
请识别以下RTL中的协议模式:

```systemverilog
{code}
```

识别:
1. 协议类型 (APB/AXI/握手/自定义)
2. 协议信号
3. 协议时序
4. 建议的断言属性

输出格式:
{
  "protocol_type": "...",
  "signals": [...],
  "properties": [...]
}
```

### 5.2 断言生成Prompt

```markdown
你是一个SVA专家。
请为以下协议生成SVA断言:

{protocol_description}

要求:
1. 生成sequence
2. 生成property
3. 生成assert/cover
4. 考虑corner case

输出SystemVerilog格式。
```

## 6. 实现策略

### 6.1 方案A: 规则+模板

```
优点:
- 速度快
- 一致性好
- 无需LLM

缺点:
- 覆盖率有限
- 需要手工规则

适用场景:
- 标准协议 (APB/AXI)
- 简单逻辑
```

### 6.2 方案B: LLM辅助

```
优点:
- 泛化能力强
- 可处理复杂逻辑

缺点:
- 成本高
- 可能生成错误断言

适用场景:
- 自定义协议
- 复杂状态机
```

### 6. 3 方案C: 混合

```
规则处理标准协议
LLM处理自定义逻辑
```

## 7. 质量保证

### 7.1 静态检查

- 语法检查
- 语义检查
- 覆盖率分析

### 7.2 仿真验证

- 在仿真中运行断言
- 检查误报
- 调整敏感度

## 8. 当前状态

⚠️ 本Skill只提供方法论框架，具体实现需要:
- 选择解析器 (pyslang)
- 设计规则库
- 构建Prompt库
- 集成LLM (可选)

## 9. 参考实现

后续可参考:
- SVA到Propman转换
- JasperGold Auto-Formal
- VC Formal SVA Generator
