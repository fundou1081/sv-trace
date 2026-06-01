# ADR-021: LoadTracer 合并

## 状态

**已通过** - 2026-04-26

## 背景

LoadTracer模块有两个实现:
- `LoadTracer`: 基于pyslang visit API (15行开始)
- `LoadTracerRegex`: 基于正则表达式 (原296行)

两者功能重复但实现不同,LoadTracerRegex更准确(6 vs 0 loads for clk)。

## 决策

**合并为单一实现**

 LoadTracer内部使用LoadTracerRegex实现,LoadTracerRegex作为别名。

## 架构变化

### 旧架构 (441行)

```
load.py (441行)
├── class LoadTracer (15行)      # pyslang visit实现
│   └── find_load()
│   └── get_all_signals()
└── class LoadTracerRegex (296行)   # 正则表达式实现
    └── find_load()
    └── _find_in_file()
    └── get_all_signals()
```

### 新架构 (174行)

```
load.py (174行)
├── class LoadTracer           # 主入口
│   ├── find_load()         # 委托给_LoadTracerRegexImpl
│   └── get_all_signals()
├── class _LoadTracerRegexImpl # 内部实现
│   ├── find_load()
│   ├── _find_in_file()
│   └── get_all_signals()
└── class LoadTracerRegex   # 别名,向后兼容
```

## 后果

### 改进

- 代码行数减少60% (441 → 174)
- 统一入口,减少维护成本
- 保持向后兼容

### 使用方式

```python
# 两种方式都可用
lt = LoadTracer(parser)
loads = lt.find_load('clk')

# 别名保持向后兼容
lt = LoadTracerRegex(parser)  
loads = lt.find_load('clk')
```

## 验证

- 10/10测试文件通过
- ~156个信号测试
- ~58个Load测试

## 相关

- 继承自 ADR-015 (Driver/Load追踪修复)
- 相关 TODO 项目
