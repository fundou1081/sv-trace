# ADR-016: Debug Analyzers - Driver API 不匹配问题

## 状态
已接受

## 日期
2026-04-25

## 问题
多个 Debug 分析器在调用时抛出错误：
1. `MultiDriverDetector.detect_all()` - `'Driver' object has no attribute 'driver_kind'`
2. `UninitializedDetector.detect_all()` - `'Driver' object has no attribute 'driver_kind'`
3. `XValueDetector.detect()` - `'Driver' object has no attribute 'source_expr'`

## 原因分析

Driver 模型的实际 API：
```python
class Driver:
    signal: str
    kind: DriverKind           # ✓ 正确属性名
    sources: List[str]        # ✓ 正确属性名
```

但代码错误地使用：
- `d.driver_kind.name` → 应为 `d.kind.name`
- `d.source_expr` → 应为 `d.sources[0]`

枚举值名称不匹配：
- 代码期望: `ASSIGN`, `ALWAYS_FF`, `ALWAYS_COMB`
- 实际值: `Continuous`, `AlwaysFF`, `AlwaysComb`

## 解决方案

1. `d.driver_kind.name` → `d.kind.name`
2. `'ALWAYS_FF'` → `'AlwaysFF'`
3. `d.source_expr` → `d.sources[0] if d.sources else ''`

## 修改文件
- `src/debug/analyzers/multi_driver.py`
- `src/debug/analyzers/uninitialized.py`
- `src/debug/analyzers/xvalue.py`

## 影响
- MultiDriverDetector, UninitializedDetector, XValueDetector 正常工作
