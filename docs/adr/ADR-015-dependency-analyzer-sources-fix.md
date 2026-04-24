# ADR-015: DependencyAnalyzer - driver.sources 类型修复

## 状态
已接受

## 日期
2026-04-25

## 问题
DependencyAnalyzer 在调用 `analyze()` 时抛出 TypeError：
```
TypeError: expected string or bytes-like object, got 'list'
```

## 原因分析

在 `src/trace/dependency.py` 的 `_find_forward_dependencies()` 方法中：

```python
def _find_forward_dependencies(self, signal_name: str, module_name: str = None):
    tracer = DriverTracer(self.parser)
    drivers = tracer.find_driver(signal_name, module_name)
    
    for driver in drivers:
        # 错误：driver.sources 是 List[str]，不是 string
        signals = self._extract_signals(driver.sources)  # ← 这里出错
```

问题在于：
1. `Driver.sources` 在 `driver.py` 中定义为 `List[str]`
2. `_extract_signals()` 方法使用 regex 处理 string 输入
3. 传入 List[str] 导致 regex 操作失败

## 解决方案

由于 `Driver.sources` 已经是 `List[str]`，无需调用 `_extract_signals()` 进行解析，直接使用即可：

```python
def _find_forward_dependencies(self, signal_name: str, module_name: str = None) -> List[str]:
    tracer = DriverTracer(self.parser)
    drivers = tracer.find_driver(signal_name, module_name)
    
    forward_deps = set()
    
    for driver in drivers:
        # driver.sources 已经是 List[str]，直接使用
        for src in driver.sources:
            if src and src != signal_name:
                forward_deps.add(src)
    
    return list(forward_deps)
```

## 修改文件
- `src/trace/dependency.py`

## 影响
- 修复后 DependencyAnalyzer.analyze() 正常工作
