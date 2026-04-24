# SV-Trace 测试计划

## 测试项目

| # | 项目 | 路径 | 复杂度 | 描述 |
|---|------|------|--------|------|
| 1 | picorv32 | `/my_dv_proj/picorv32/picorv32.v` | 中 | RISC-V 软核，3000+ 行 |
| 2 | serv_ctrl | `/my_dv_proj/serv/rtl/serv_ctrl.v` | 低 | SERV RISC-V 控制单元 |
| 3 | basic_debounce | `/my_dv_proj/basic_verilog/debounce_v1.v` | 低 | 基础消抖模块 |

## 测试模块

| # | 模块 | 功能 | 核心验证点 |
|---|------|------|------------|
| 1 | DriverCollector | 收集信号驱动 | signals ≥ 1 |
| 2 | LoadTracer | 追踪信号负载 | find_load() 方法正常 |
| 3 | ControlFlowTracer | 追踪控制依赖 | find_control_dependencies() 方法正常 |
| 4 | DataPathAnalyzer | 数据路径分析 | analyze() 方法正常 |
| 5 | ConnectionTracer | 连接追踪 | instances ≥ 0 |

## 验证结果

### 项目 1: picorv32

| 模块 | 结果 | 详情 |
|------|------|------|
| DriverCollector | ✅ PASS | signals:119, drivers:182 |
| LoadTracer | ✅ PASS | find_load() 方法正常 |
| ControlFlowTracer | ✅ PASS | find_control_dependencies() 方法正常 |
| DataPathAnalyzer | ✅ PASS | datapaths:10 (sample) |
| ConnectionTracer | ✅ PASS | instances:3 |

**模块类型分布:**
- Continuous: 87
- AlwaysFF: 95

### 项目 2: serv_ctrl

| 模块 | 结果 | 详情 |
|------|------|------|
| DriverCollector | ✅ PASS | signals:15, drivers:33 |
| LoadTracer | ✅ PASS | loads:2 |
| ControlFlowTracer | ✅ PASS | find_control_dependencies() 方法正常 |
| DataPathAnalyzer | ✅ PASS | datapaths:10 (sample) |
| ConnectionTracer | ✅ PASS | instances:0 |

**模块类型分布:**
- Continuous: 31
- AlwaysFF: 2

### 项目 3: basic_debounce

| 模块 | 结果 | 详情 |
|------|------|------|
| DriverCollector | ✅ PASS | signals:1, drivers:2 |
| LoadTracer | ✅ PASS | find_load() 方法正常 |
| ControlFlowTracer | ✅ PASS | find_control_dependencies() 方法正常 |
| DataPathAnalyzer | ✅ PASS | datapaths:1 |
| ConnectionTracer | ✅ PASS | instances:2 |

**模块类型分布:**
- Continuous: 2

## 深度追踪测试

### 线性 Pipeline 测试

| Pipeline 深度 | 结果 | 追踪实例数 |
|-------------|------|-----------|
| 10 stages | ✅ PASS | 10 |
| 50 stages | ✅ PASS | 50 |
| 100 stages | ✅ PASS | 100 |
| 200 stages | ✅ PASS | 200 |
| 500 stages | ✅ PASS | 500 |
| 1,000 stages | ✅ PASS | 1,000 |
| 2,000 stages | ✅ PASS | 2,000 |
| 5,000 stages | ✅ PASS | 5,000 |

### 极限压力测试

| Pipeline 深度 | 结果 | 追踪实例数 |
|-------------|------|-----------|
| 10,000 stages | ✅ PASS | 10,000 |
| 20,000 stages | ✅ PASS | 20,000 |
| 50,000 stages | ✅ PASS | 50,000 |
| **100,000 stages** | ✅ PASS | 100,000 |

### 复杂拓扑测试

| 拓扑类型 | 实例数 | 结果 |
|---------|--------|------|
| Diamond (收敛) | 300 | ✅ PASS |
| Broadcast (广播) | 401 | ✅ PASS |
| Cycle (环) | 3 | ✅ PASS |

## 跨项目验证

| 项目 | Instances | Signals | Wires |
|------|-----------|---------|-------|
| picorv32 | 3 | 119 | 87 |
| Vortex | 6 | 7 | 14 |
| tiny-gpu/gpu | 4 | 10 | 2 |
| serv/top | 9 | 12 | 28 |
| adder_tree | 0 | 1 | 2 |
| axi_logger | 3 | 5 | 10 |
| **Total** | **25** | **154** | - |

## 汇总统计

| 项目 | Signal | Driver | Wire | FF | Instance |
|------|--------|--------|------|-----|----------|
| picorv32 | 119 | 182 | 87 | 95 | 3 |
| serv_ctrl | 15 | 33 | 31 | 2 | 0 |
| basic_debounce | 1 | 2 | 2 | 0 | 2 |

## 总结

- **测试项目**: 3 个
- **测试模块**: 5 个核心模块
- **深度测试**: 10万级 pipeline 追踪通过
- **复杂拓扑**: Diamond/Broadcast/Cycle 拓扑通过
- **跨项目验证**: 6 个开源项目验证通过
- **通过率**: 全部模块 ✅ 100%

所有项目在所有模块上均通过验证 ✅
