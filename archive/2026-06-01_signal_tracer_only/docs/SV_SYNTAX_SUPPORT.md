# SystemVerilog 语法支持度分析

> 2026-05-08 更新

## 1. Driver 语法支持度

### 已支持的语法

| 语法类别 | 语法元素 | 支持状态 | 备注 |
|----------|----------|----------|------|
| **过程块** | always_ff | ✅ 完全支持 | 时钟/复位提取 |
| **过程块** | always_comb | ✅ 完全支持 | 组合逻辑 |
| **过程块** | always @ | ✅ 完全支持 | 旧语法兼容 |
| **过程块** | always @* | ✅ 完全支持 | 组合逻辑 |
| **赋值** | <= (非阻塞) | ✅ 完全支持 | 时序逻辑 |
| **赋值** | = (阻塞) | ✅ 完全支持 | 组合逻辑 |
| **赋值** | assign (连续) | ✅ 完全支持 | 连续赋值 |
| **时钟** | posedge clk | ✅ 完全支持 | 上升沿 |
| **时钟** | negedge clk | ✅ 完全支持 | 下降沿 |
| **复位** | async (or negedge) | ✅ 完全支持 | 异步复位 |
| **复位** | sync (if rst) | ✅ 完全支持 | 同步复位 |
| **控制流** | if/else | ✅ 完全支持 | 条件赋值 |
| **控制流** | case | ✅ 完全支持 | 多路选择 |
| **控制流** | for loop | ✅ 完全支持 | 循环赋值 |
| **控制流** | while loop | ✅ 完全支持 | 循环赋值 |
| **控制流** | do while | ✅ 完全支持 | 循环赋值 |
| **控制流** | repeat | ✅ 完全支持 | 循环赋值 |
| **控制流** | foreach | ✅ 完全支持 | 循环赋值 |
| **生成** | generate for | ✅ 完全支持 | 循环生成 |
| **生成** | generate if | ✅ 完全支持 | 条件生成 |
| **函数** | function | ✅ 完全支持 | 函数内的赋值 |
| **任务** | task | ✅ 完全支持 | 任务内的赋值 |
| **类** | class | ✅ 完全支持 | 面向对象 |
| **接口** | interface | ✅ 完全支持 | 接口赋值 |
| **断言** | assert | ❌ 不支持 | 验证断言 |

### 支持度统计

- **总语法数**: 25
- **已支持**: 24 (96%)
- **不支持**: 1 (4%)

## 2. Load 语法支持度

### 已支持的语法

| 语法类别 | 语法元素 | 支持状态 | 备注 |
|----------|----------|----------|------|
| **赋值右值** | a + b | ✅ 完全支持 | 表达式 |
| **赋值右值** | a[i] | ✅ 完全支持 | 数组索引 |
| **赋值右值** | a.field | ✅ 完全支持 | 结构体字段 |
| **条件** | if (cond) | ✅ 完全支持 | 条件读取 |
| **条件** | case (sel) | ✅ 完全支持 | 多路读取 |
| **时钟/复位** | @(posedge clk) | ✅ 完全支持 | 事件控制 |
| **端口连接** | .port(signal) | ✅ 完全支持 | 命名连接 |
| **端口连接** | .port() | ✅ 完全支持 | 空连接 |
| **函数调用** | func(a, b) | ✅ 完全支持 | 函数参数读取 |
| **任务调用** | task(a, b) | ✅ 完全支持 | 任务参数读取 |
| **类方法** | obj.method() | ✅ 完全支持 | 面向对象 |

### 支持度统计

- **总语法数**: 11
- **已支持**: 11 (100%)
- **不支持**: 0 (0%)

## 3. 语义验证测试

### 验证点

| 验证项 | 测试用例 | 状态 |
|--------|----------|------|
| 驱动信号名称 | test_basic_ff_signal_name | ✅ |
| 时钟信号名称 | test_basic_ff_clock_name | ✅ |
| 异步复位名称 | test_async_reset_signal_name | ✅ |
| 同步复位名称 | test_sync_reset_signal_name | ✅ |
| 多信号驱动 | test_multi_signal_names | ✅ |
| 组合逻辑驱动 | test_comb_driver_signal | ✅ |
| 连续赋值驱动 | test_assign_driver_signal | ✅ |
| 语义一致性 | test_semantic_consistency | ✅ |
| 时钟提取一致性 | test_clock_extraction_consistency | ✅ |
| 复位提取一致性 | test_reset_extraction_consistency | ✅ |

## 4. 测试覆盖

| 测试文件 | 用例数 | 状态 |
|----------|--------|------|
| test_driver_boundary.py | 8 | ✅ |
| test_driver_grammar_coverage.py | 18 | ✅ |
| test_driver_edge_cases.py | 8 | ✅ |
| test_driver_p1_syntax.py | 6 | ✅ |
| test_driver_p2_syntax.py | 6 | ✅ |
| test_driver_semantic_validation.py | 10 | ✅ |
| test_load_tracer.py | 4 | ✅ |
| **总计** | **60** | **✅ 全部通过** |

## 5. 修复记录

| 日期 | 问题 | 修复 |
|------|------|------|
| 2026-05-08 | 时钟提取失败 | 修复 extract_events_from_block (SignalEventExpression) |
| 2026-05-08 | 同步复位提取失败 | 修复 _extract_from_always_ff (ConditionalStatement) |
| 2026-05-08 | 异步复位提取失败 | 修复 ClockDomainItem.__post_init__ |
