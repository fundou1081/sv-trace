# 2026-05-09 开发记录 - CLOCK 边添加计划

## pyslang API 验证完成 ✅

### 时钟提取路径 (已验证)
```
AlwaysFFBlock → statement (TimingControlStatement)
           → timingControl (EventControlWithExpression)  
           → expr (SignalEventExpression/ParenthesizedEventExpression)
           → expr.expr (IdentifierName)
           → expr.expr.identifier.value = "clk"
```

### 找到的 SyntaxKinds
- `SyntaxKind.AlwaysFFBlock`
- `SyntaxKind.AlwaysBlock`  
- `SyntaxKind.AlwaysCombBlock`
- `SyntaxKind.TimingControlStatement`
- `SyntaxKind.EventControlWithExpression`
- `SyntaxKind.ParenthesizedEventExpression`
- `SyntaxKind.SignalEventExpression`
- `SyntaxKind.BinaryEventExpression` (多个时钟用 or 连接)

### 边沿信息
- `SignalEventExpression.edge` → `PosEdgeKeyword` / `NegEdgeKeyword`

## 待实现
1. 在 `extractors/driver.py` 添加 `_extract_clock_from_always()` 方法
2. 添加 CLOCK 边到信号图
3. 支持 `posedge clk` 和 `negedge rst_n` 区分

## 开发纪律
遵守本项目的开发纪律：
1. ✅ 简化测试验证 API (已完成)
2. ⏸ 增量添加 (等待下次开发)
3. ⏸ 验证不影响现有测试 (等待下次开发)

## 当前状态
- 稳定版本保持不变
- 下次开发可使用验证的 API 路径
