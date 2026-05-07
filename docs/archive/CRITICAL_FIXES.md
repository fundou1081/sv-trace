# 关键问题修复任务

> 基于技术审计发现的严重问题

---

## 🔴 P0 - 必须立即修复

### 1. timing_path.py - 使用正则分析源码

**问题**: 直接用 `re.findall` 分析源码文本

**当前代码**:
```python
for m in re.findall(r'assign\s+(\w+)\s*=\s*([^;]+);', code):
```

**修复方案**: 改用 AST 遍历 `AssignmentExpression`

### 2. controlflow.py - 设计缺陷

**问题**: 从信号名列表反向搜索控制结构，无法工作

**修复方案**: 基于 AST 的控制依赖记录

---

## 🟠 P1 - 高优先级

### 3. driver.py - 位选择截断

**问题**: `data[7:0]` 被截断成 `data`

**修复方案**: 保留 Range 字段

### 4. dataflow.py - 硬编码深度限制

**问题**: `max_depth=5` 硬编码

**修复方案**: 可配置深度

---

## 🟡 P2 - 中优先级

### 5. 缺失功能

- Generate块支持
- Interface支持
- 参数化模块支持
- 跨模块追踪
- force/release支持

---

## 检查清单

- [ ] timing_path.py 改用 AST
- [ ] controlflow.py 重写为 AST 驱动
- [ ] driver.py 位精确性
- [ ] dataflow.py 动态深度
- [ ] 添加 Generate 块支持
- [ ] 添加 Interface 支持

---

## 当前代码状态

| 文件 | AST使用 | 正则使用 | 数据准确 |
|------|---------|----------|----------|
| driver.py | ✅ | 仅例外 | ⚠️ 位截断 |
| timing_path.py | ❌ | 🔴 严重 | ❌ |
| controlflow.py | ❌ | 🔴 严重 | ❌ |
| dataflow.py | ⚠️ | 🟠 | ⚠️ |
| fsm_analyzer.py | ✅ | 仅例外 | ✅ |
