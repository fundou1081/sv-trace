# ADR-008: CDC 分析增强

> **状态**: Completed (Phase 1)
> **日期**: 2026-04-19
> **版本**: v0.1

---

## 1. 问题定义

### 1.1 什么是 CDC 问题

Clock Domain Crossing (CDC) 是指信号从一个时钟域跨越到另一个时钟域的情况。如果处理不当，会导致亚稳态、数据丢失等问题。

### 1.2 需要检测的问题类型

| 问题类型 | 描述 | 严重程度 |
|----------|------|----------|
| **单bit跨域** | 单bit信号跨域但未同步 | 高 |
| **多bit跨域** | 多bit总线跨域未使用握手 | 高 |
| **异步复位跨域** | 复位信号跨域 | 中 |
| **无同步器** | 跨域信号缺少 2-ff 同步器 | 高 |
| **扇出过大** | 同步器驱动过多负载 | 中 |
| **格雷码违规** | 跨域计数器未使用格雷码 | 中 |

---

## 2. 当前实现状态

已有的 `CDCAnalyzer` 是简化版：
- 基础连接检测
- 缺少同步器检测 (基于信号命名)

需要增强为完整的 CDC 分析器。

---

## 3. 算法方案

### Option A: 规则匹配 (Rule-Based)

```
步骤:
1. 定义 CDC 问题模式规则:
   - 规则1: 信号从 clock_a 到 clock_b，且无同步器
   - 规则2: 多bit信号跨域无握手
   - 规则3: 异步信号跨域
2. 扫描所有信号跨域路径
3. 匹配问题模式
4. 报告问题
```

**优点**:
- 实现简单
- 快速
- 易于理解和调试

**缺点**:
- 可能漏掉复杂模式
- 规则覆盖不全面

**复杂度**: O(n × r) where r = rules

---

### Option B: 路径追踪 (Path Tracing)

```
步骤:
1. 构建时钟域图
2. 对每个信号:
   a. 从驱动源开始追踪
   b. 记录经过的时钟域
   c. 检测域切换点
3. 分析切换点:
   - 是否有同步器
   - 是否是握手协议
   - 是否是格雷码
4. 报告问题
```

**优点**:
- 能发现隐藏的 CDC 问题
- 准确追踪信号路径

**缺点**:
- 实现复杂
- 性能可能较差

**复杂度**: O(n × d) where d = depth

---

### Option C: 约束求解 (Constraint Solving)

```
步骤:
1. 形式化 CDC 约束:
   - "信号 S 从域 A 到域 B"
   - "同步器在 S 的路径上"
2. 使用约束求解器验证
3. 生成问题报告
```

**优点**:
- 准确度最高
- 可验证复杂场景

**缺点**:
- 需要额外工具
- 性能最差

**复杂度**: O(n²) 或更高

---

### Option D: 层次化分析 (Hierarchical Analysis)

```
步骤:
1. 模块层次分析:
   a. 识别每个模块的时钟输入
   b. 确定模块属于哪个时钟域
2. 实例连接分析:
   a. 跟踪跨域信号
   b. 检查同步器/握手
3. 问题聚合:
   a. 从底层向上聚合问题
   b. 标记问题严重程度
```

**优点**:
- 支持多层级设计
- 能处理复杂 SoC

**缺点**:
- 最复杂
- 需要完整模块信息

**复杂度**: O(n²)

---

## 4. 推荐方案

**选择 Option A (规则匹配) 作为 Phase 1**

理由:
- 实现快速
- 足够处理常见 CDC 问题
- 易于扩展

**后续可增强 Option D (层次化分析)**

---

## 5. 实现计划

### Phase 1: 基础 CDC 检测

| 任务 | 预估时间 |
|------|----------|
| 时钟域识别 | 2h |
| 跨域路径检测 | 2h |
| 同步器检测 | 1h |
| 问题报告 | 1h |

### Phase 2: 高级 CDC 检测

| 任务 | 预估时间 |
|------|----------|
| 握手协议检测 | 2h |
| 格雷码验证 | 1h |
| 异步跨域处理 | 2h |

---

## 6. 详细设计

### CDC 分析器 API

```python
class CDCAnalyzer:
    def __init__(self, parser):
        self.parser = parser
        self._clock_analyzer = None
    
    def analyze(self) -> CDCReport:
        """执行完整 CDC 分析"""
        pass
    
    def detect_issues(self) -> List[CDCIssue]:
        """检测所有 CDC 问题"""
        pass
    
    def check_crossing(self, signal: str) -> CrossingResult:
        """检查单个信号的跨域情况"""
        pass


@dataclass
class CDCIssue:
    signal: str
    from_domain: str
    to_domain: str
    issue_type: str
    severity: str
    description: str
    mitigation: str  # 建议的修复方法


@dataclass
class CrossingResult:
    signal: str
    is_crossing: bool
    from_domain: str
    to_domain: str
    has_synchronizer: bool
    protection_type: str  # none, synchronizer, handshake, gray
```

### 问题类型定义

```python
class CDCIssueType(Enum):
    UNPROTECTED_CROSSING = "unprotected_crossing"
    MULTI_BIT_WITHOUT_HANDSHAKE = "multi_bit_without_handshake"
    ASYNC_RESET_CROSSING = "async_reset_crossing"
    GRAY_CODE_VIOLATION = "gray_code_violation"
    HIGH_FANOUT = "high_fanout"
    METASTABILITY_RISK = "metastability_risk"


class ProtectionType(Enum):
    NONE = "none"
    TWO_FF_SYNC = "two_ff_synchronizer"
    THREE_FF_SYNC = "three_ff_synchronizer"
    HANDSHAKE = "handshake"
    GRAY_CODE = "gray_code"
    FIFO = "fifo"
```

---

## 7. 规则示例

### 规则1: 无保护跨域

```
条件: 信号从域 A 到域 B，无同步器
问题: 可能产生亚稳态
建议: 添加 2-ff 同步器
```

### 规则2: 多bit无握手

```
条件: 多bit信号跨域，无握手协议
问题: 数据可能错位
建议: 使用 FIFO 或握手协议
```

### 规则3: 异步复位

```
条件: 复位信号跨域
问题: 可能导致亚稳态
建议: 同步复位或使用同步器
```

---

## 8. 性能考虑

1. **缓存**: 缓存时钟域分析结果
2. **增量**: 只分析新添加的跨域路径
3. **并行**: 可并行分析不同模块

---

## 9. 风险与缓解

| 风险 | 缓解 |
|------|------|
| 规则不完整 | 提供规则扩展接口 |
| 漏检 | 添加置信度评分 |
| 误报多 | 验证后报告 |

---

*最后更新: 2026-04-19*


---

## 实现完成

### 实现的算法: Option B (路径追踪)

### 功能:
- 从 AST 直接提取 always_ff 时钟信息
- 检测跨时钟域信号
- 识别保护类型 (同步器/握手/FIFO/格雷码)
- 报告无保护的跨域问题

### 测试结果:
```
data_b: clk_a -> clk_b (unprotected) - HIGH severity issue
```

---

*最后更新: 2026-04-19*
