# sv-trace 工具测试详细规范

## 核心原则
- **一工具一文件**: 每个工具模块对应一个独立的测试文件
- **三層防护**: 基础用例 → 边界用例 → 真实项目用例
- **可独立运行**: `pytest tests/unit/tools/test_driver.py -v` 即可单独测试

---

## 1. core/base.py ✅ 核心基类

**定位**: Signal, FSM, Interface 基类定义

| 测试点 | 用例 | 边界/异常 |
|--------|------|-----------|
| Signal 创建 | `test_signal_creation` 输入 name, width, signed | width=0, width<0, width>1024 |
| Signal 运算 | `test_signal_add`, `test_signal_slice` | slice out-of-range |
| Signal 比较 | `test_signal_eq`, `test_signal_ne` | 不同 width 比较 |
| FSM 构建 | `test_fsm_state`, `test_fsm_transition` | 循环状态、无效转换 |
| Interface 构造 | `test_interface_bundle` | 空 interface |

**通过标准**: 100% 覆盖 Signal/FSM 全部方法

---

## 2. core/interfaces.py ✅ 接口层

| 测试点 | 用例 | 边界/异常 |
|--------|------|-----------|
| 端口连接 | `test_port_connection` | 未连接、多驱动 |
| 层次关系 | `test_hierarchy` | 循环层次 |
| 接口映射 | `test_interface_mapping` | 不匹配 width |

---

## 3. semantic/builder.py ✅ 语义层

**关键**: SUPPORTED_KINDS 声明机制

| 测试点 | 用例 | 边界/异常 |
|--------|------|-----------|
| 语义注册 | `test_kind_registration` | 重复注册 |
| 语义构建 | `test_build_from_decl` | 未知 kind |
| 继承检查 | `test_kind_inheritance` | 中间层缺失 |

---

## 4. query/signal_chain.py 🔷 信号溯源

| 测试点 | 用例 | 边界/异常 |
|--------|------|-----------|
| 驱动追溯 | `test_trace_driver` SimpleDriver, AlwaysBlock | 多驱动冲突 |
| FSM 状态 | `test_trace_fsm_state` | 嵌套 FSM |
| 路径打印 | `test_chain_to_string` | 环回路径 |

**通过标准**: OpenTitan 项目 100% 覆盖

---

## 5. query/module_connections.py 🔷 模块连接

| 测试点 | 用例 | 边界/异常 |
|--------|------|-----------|
| 连接图构建 | `test_build_connection_graph` | 模块未实例化 |
| 实例关系 | `test_instance_relation` | 多层嵌套 |
| 跨模块连接 | `test_cross_module_connection` | 循环依赖 |

---

## 6. query/clock_domain.py 🔷 时钟域

| 测试点 | 用例 | 边界/异常 |
|--------|------|-----------|
| 时钟提取 | `test_extract_clock` | 时钟来自参数 |
| 复位提取 | `test_extract_reset` | 异步复位、同步复位 |
| 时钟关系 | `test_clock_relationship` | 派生时钟、门控时钟 |

---

## 7. query/timing_path.py 🔷 时序路径

| 测试点 | 用例 | 边界/异常 |
|--------|------|-----------|
| 关键路径 | `test_critical_path` | 无路径 |
| 路径延迟 | `test_path_delay` | 多路径合并 |
| 建立/保持 | `test_setup_hold` | 时序违例 |

---

## 8. driver.py 🛠️ 驱动提取

| 测试点 | 用例 | 边界/异常 |
|--------|------|-----------|
| 时钟检测 | `test_detect_clock` | 参数化时钟、函数生成 |
| 复位检测 | `test_detect_reset` | 复杂复位表达式 |
| AlwaysBlock | `test_extract_always` | AlwaysCombine, AlwaysFF |
| 简单驱动 | `test_simple_driver` | Assign, Force |

**通过标准**: 自建用例 + OpenTitan 覆盖

---

## 9. load.py 🛠️ 文件加载

| 测试点 | 用例 | 边界/异常 |
|--------|------|-----------|
| SV 解析 | `test_load_sv_file` | 超大文件 (>10MB) |
| 目录加载 | `test_load_directory` | 空目录、深层嵌套 |
| 模块提取 | `test_extract_module` | 多模块文件 |

---

## 10. parse_warn.py 🛠️ 警告解析

| 测试点 | 用例 | 边界/异常 |
|--------|------|-----------|
| 警告分类 | `test_classify_warning` | 新警告类型 |
| 位置定位 | `test_warning_location` | 多行警告 |

---

## 11. performance.py 🛠️ 性能分析

| 测试点 | 用例 | 边界/异常 |
|--------|------|-----------|
| 面积估算 | `test_area_estimate` | 空设计 |
| 功耗分析 | `test_power_analysis` | 无 toggle 信号 |
| 时序深度 | `test_timing_depth` | 过长路径 |

---

## 12. controlflow.py 🛠️ 控制流

| 测试点 | 用例 | 边界/异常 |
|--------|------|-----------|
| if/else | `test_if_else` | 嵌套 if |
| case | `test_case` | casez, casex |
| for/while | `test_loop` | 循环展开 |

---

## 13. dataflow.py 🛠️ 数据流

| 测试点 | 用例 | 边界/异常 |
|--------|------|-----------|
| 赋值传播 | `test_assign_propagation` | 跨模块 |
| 操作符简化 | `test_operator_simplify` | 常量折叠 |

---

## 14. dependency.py 🛠️ 依赖图

| 测试点 | 用例 | 边界/异常 |
|--------|------|-----------|
| 图构建 | `test_build_graph` | 自依赖 |
| 拓扑排序 | `test_topological_sort` | 循环依赖 |
| 关键路径 | `test_critical_path` | 多启动 |

---

## 测试状态标记

- ✅ 基座模块
- 🔷 Query 工具
- 🛠️ 分析工具

---
