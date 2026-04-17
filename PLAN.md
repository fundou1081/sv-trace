# SV Trace Library 规划

## 阶段一：底层 Parse & Trace 库

### 1. 核心数据模型

| 组件 | 功能 |
|------|------|
| **Signal** | 信号元数据 (name, width, type, range, signed, constness) |
| **Driver** | 信号驱动源 (always/assign, source expr, timing, blocking/non-blocking) |
| **Load** | 信号加载点 |
| **Connection** | port 连接 |
| **Parameter** | 参数/本地参数 |

### 2. Parse 能力

| 组件 | 功能 |
|------|------|
| **Parser** | 解析 SV → SyntaxTree + Compilation |
| **Preprocessor** | `define / `ifdef / `include |
| **ModuleExtractor** | 模块/interface/package |
| **PortAnalyzer** | port 定义 |
| **SignalExtractor** | signal 提取 |
| **ClassExtractor** | class |
| **ConstraintExtractor** | constraint |
| **CovergroupExtractor** | covergroup |
| **AssertionExtractor** | property/sequence/assume/cover |

### 3. Trace 能力

| 组件 | 功能 |
|------|------|
| **DriverTracer** | 驱动源追踪 |
| **LoadTracer** | 加载点追踪 |
| **ConnectionTracer** | port 连接追踪 |
| **DataFlowTracer** | 数据流分析 |
| **ControlFlowTracer** | 控制流分析 |
| **AssertionTracer** | assertion → 信号依赖追踪 |
| **UVMTracer** | UVM 组件追踪 |

### 4. 查询接口

| 组件 | 功能 |
|------|------|
| **SignalQuery** | 信号查询 |
| **PathQuery** | hierarchical path |
| **HierarchyQuery** | 实例化关系 |
| **ClassQuery** | 类查询 |
| **ConstraintQuery** | 约束查询 |
| **AssertionQuery** | assertion 查询 |

### 5. 辅助工具

| 组件 | 功能 |
|------|------|
| **SVFileSet** | 多文件项目 |
| **ParamResolver** | 参数化解析 |
| **Cache** | 缓存 (LRU) |

---

### 6. 特殊场景

- `define / 参数化 / class / constraint / covergroup / assertion / UVM / interface

### 7. 性能考虑

| 策略 | 说明 |
|------|------|
| **延迟解析** | 懒加载，用到时才 parse |
| **增量缓存** | 只 reparse 变更文件 |
| **批量操作** | 一次性获取多个信号信息 |
| **并行处理** | 多文件并行 parse |
| **内存池** | 复用 Object，减少 GC |

---

## 开发日志

### v0.1 (2026-04-17)
- 初始化项目
- 克隆 slang 库到 ~/my_dv_proj/slang
- 安装 pyslang Python binding
- 克隆 sv-tests 测试素材
