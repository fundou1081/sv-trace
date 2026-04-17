# SV Trace Library 规划

## 项目结构
```
sv-trace/
├── docs/
│   └── adr/           # 架构决策记录
├── src/               # 源码
│   ├── core/          # 核心模型
│   ├── parse/         # 解析器
│   ├── trace/         # 追踪器
│   ├── query/         # 查询接口
│   └── utils/         # 工具
└── tests/             # 测试
```

## 功能清单

### 核心功能 (Core)
| 功能 | 状态 | 说明 |
|------|------|------|
| SVParser | ✅ | pyslang 解析 |
| ParameterResolver | ✅ | parameter 解析 |
| SignalQuery | ✅ | 信号查询 |

### 追踪器 (Trace)
| 功能 | 状态 | 说明 |
|------|------|------|
| DriverTracer | ✅ | assign/always_ff/comb 驱动 |
| LoadTracer | ✅ | 信号负载追踪 |
| DataFlowTracer | ✅ | 数据流连接 |
| ConnectionTracer | ✅ | 模块实例连接 |

### 提取器 (Extractors)
| 功能 | 状态 | 说明 |
|------|------|------|
| ClassExtractor | ✅ | class 成员/方法 |
| ConstraintExtractor | ✅ | constraint 块 |
| CovergroupExtractor | ✅ | covergroup/coverpoint |
| AssertionExtractor | ✅ | assertion/sequence/property |

### 测试
| 功能 | 状态 |
|------|------|
| test_all.py | ✅ 10/10 passed |

---

## 开发记录

### v0.1 (2026-04-17)
- 初始化项目
- 克隆 slang 库到 ~/my_dv_proj/slang
- 安装 pyslang Python binding
- 克隆 sv-tests 测试素材
- 实现所有核心模块
- 批量测试: 57/60 sv-tests 通过

### v0.2 (2026-04-18)
- Class/Constraint/Covergroup/Assertion 提取器
- ConnectionTracer
- 全面测试 10/10 通过
- **共 20 commits**

---

详细架构决策见 `docs/adr/` 目录
