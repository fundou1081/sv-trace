# ADR-013: 静态分析与 Design Rule Checking (DRC)

> **状态**: Planning
> **日期**: 2026-04-19

---

## 需求概述

实现静态分析工具，用于检查 RTL 代码质量和 Design Rule 违规:

### 设计规则类别

1. **代码风格 (Coding Style)**
   - 时钟 always_ff 应该是单个时钟
   - 异步复位应该是 negedge
   - 避免组合逻辑循环

2. **CDC 规则 (Clock Domain Crossing)**
   - 单 bit 信号跨域需要同步器
   - 多 bit 信号需要握手或 FIFO
   - 异步复位跨域检查

3. **时序规则 (Timing)**
   - 多路复用器的默认分支
   - case 语句应该有 default
   - 状态机应该有 default 状态

4. **代码质量 (Code Quality)**
   - 未使用的信号
   - 未驱动的输入
   - 未连接的输出
   - 悬空端口

5. **可综合性 (Synthesis)**
   - 避免使用三态逻辑 (inout 应该在顶层)
   - 避免 latch (应该用 FF)
   - 时钟门控建议

---

## 算法方案

### Option A: 规则模式匹配

```
1. 定义规则 (正则表达式或 AST 模式)
2. 遍历 AST
3. 匹配规则
4. 报告违规
```

| 优点 | 缺点 |
|------|------|
| 简单快速 | 规则固定 |
| 易于添加新规则 | 可能误报 |
| 可解释性强 | 覆盖率有限 |

### Option B: 数据流分析

```
1. 构建数据流图
2. 分析信号传播
3. 基于约束检查规则
4. 生成报告
```

| 优点 | 缺点 |
|------|------|
| 更准确 | 复杂 |
| 可检测复杂问题 | 性能较低 |
| 独立于编码风格 | 需要完整分析 |

### Option C: 规则引擎

```
1. 定义规则 DSL
2. 解析规则
3. 遍历 AST 应用规则
4. 返回违规列表
```

| 优点 | 缺点 |
|------|------|
| 可扩展 | 需要 DSL 设计 |
| 用户可自定义规则 | 学习成本 |
| 灵活 | 实现复杂 |

---

## 推荐方案

**Option C (规则引擎)**: 最灵活，可扩展

---

## 规则定义格式

```python
class Rule:
    name: str
    severity: str  # error, warning, info
    description: str
    check: function
    
rules = [
    Rule(
        name="case_without_default",
        severity="warning",
        description="Case statement should have default branch",
        check=lambda ast: ...
    ),
    ...
]
```

---

## 输出格式

```python
@dataclass
class DRCViolation:
    rule_name: str
    severity: str
    module: str
    location: CodeLocation
    message: str

@dataclass
class DRCReport:
    violations: List[DRCViolation]
    statistics: Dict[str, int]
    passed_rules: List[str]
```

---

## 优先级规则

| 规则 | 严重程度 | 说明 |
|------|----------|------|
| CDC_UNSYNC_SINGLE_BIT | error | 单 bit 跨域无同步器 |
| CDC_UNSYNC_MULTI_BIT | error | 多 bit 跨域无握手 |
| LATCH_INFERENCE | warning | 锁存器推断 |
| UNUSED_SIGNAL | warning | 未使用信号 |
| UNDRIVEN_INPUT | warning | 未驱动输入 |
| UNCONNECTED_OUTPUT | warning | 未连接输出 |
| CASE_NO_DEFAULT | warning | case 无 default |
| ASYNC_RESET_MULTI_FF | warning | 异步复位多个 FF |

---

*开始时间: 2026-04-19*
