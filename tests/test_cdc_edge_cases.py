# CDCAnalyzer 边界测试用例

## 测试结果: 9/12 (75%)

### ✅ 通过用例

| # | 用例 | 预期 | 实际 | 说明 |
|---|------|------|------|------|
| 1 | 双时钟always_ff多驱动 | CRITICAL | CRITICAL | ✅ 核心CDC检测 |
| 2 | 三时钟always_ff | CRITICAL | CRITICAL | ✅ 多CDC冲突 |
| 3 | 双always_comb跨块 | HIGH | HIGH | ✅ 组合逻辑多驱动 |
| 4 | 单always_ff | None | None | ✅ 无问题 |
| 5 | 条件always_ff(单块) | None | None | ✅ 单驱动 |
| 7 | 多信号无交叉 | None | None | ✅ 正确识别 |
| 10 | 单比特多驱动 | CRITICAL | CRITICAL | ✅ 单比特CDC |
| 11 | 大位宽多驱动 | CRITICAL | CRITICAL | ✅ 大数据CDC |
| 12 | 子模块CDC | CRITICAL | CRITICAL | ✅ 模块内CDC |

### ⚠️ 已知限制

| # | 用例 | ���际行为 | 原因 |
|---|------|----------|------|
| 6 | case语句(同块) | 检测为多驱动 | Parser将case分支解析为多个独立驱动 |
| 8 | always_latch + always_ff | MEDIUM | AlwaysLatch被归类为组合逻辑 |
| 9 | 时钟门控双always | CRITICAL | 两个always块都被识别 |

## 建议改进

1. **Case分支处理**: 需要识别同always块内的多个驱动
2. **AlwaysLatch严重性**: 提升到CRITICAL（latch更危险）
3. **同一时钟多驱动**: 区分"同时钟域"和"跨时钟域"

## 核心检测能力

✅ **必须检测 (CRITICAL)**:
- 多个always_ff块驱动同一信号
- 不同时钟域的always_ff驱动

✅ **应该检测 (HIGH)**:
- 多个always_comb块驱动同一信号
- 同一时钟域的always_ff多驱动

⚠️ **已知限制**:
- Case分支可能误报（需要同always块判断）
- AlwaysLatch检测需要加强
- Assign多驱动暂不支持
