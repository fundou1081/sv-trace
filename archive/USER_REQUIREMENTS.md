# 用户需求记录

> 归档时间: 2026-05-06

---

## 已归档的需求脚本

以下脚本是从用户需求衍生出来的功能，已移至 `archive/deprecated/`：

### 1. 接口变更检测
**文件**: `interface_change.py`
**需求来源**: 用户需要检测接口模块的变化
**功能**: InterfaceChange 类
**状态**: 53行，未维护

### 2. 简化版驱动提取
**文件**: `driver_simple.py`
**需求来源**: 简化场景下的驱动提取
**功能**: DriverCollector 简化版
**状态**: 429行，已被 driver.py 取代？

### 3. VCD 波形分析
**文件**: `vcd_analyzer.py`
**需求来源**: 用户需要分析 VCD 波形文件
**功能**: VCD 解析、信号值变化追踪
**状态**: 535行，需要外部 VCD 数据源

### 4. 可视化
**文件**: `visualize.py`
**需求来源**: 需要图形化显示分析结果
**功能**: GraphNode, 图可视化
**状态**: 207行，无下游数据源

### 5. 性能估算
**文件**: `performance_estimator.py`
**需求来源**: 性能分析需求
**功能**: 性能数据估算
**状态**: 113行，可合并到 performance.py

### 6. 仿真性能
**文件**: `sim_performance.py`
**需求来源**: 仿真相关性能分析
**功能**: SimulationMetrics 时钟周期统计
**状态**: 342行

### 7. 吞吐量估算
**文件**: `throughput_estimation.py`
**需求来源**: 数据吞吐分析
**功能**: ThroughputMetrics
**状态**: 182行

### 8. 功耗计算
**文件**: `power_estimator.py`
**需求来源**: 功耗评估
**功能**: PowerEstimate 功耗计算
**状态**: 176行

### 9. 位选择操作
**文件**: `bitselect.py`
**需求来源**: 位级操作分析
**功能**: BitSelect 位选信息
**状态**: 300行，可能已合并到 semantic

### 10. 数据路径分析
**文件**: `datapath.py`
**需求来源**: 数据流路径分析
**功能**: DataPathNode 数据路径
**状态**: 418行

---

## 待评估（未归档）

以下脚本功能待进一步评估后再决定是否归档：

| 文件 | 功能 | 待确认 |
|------|------|--------|
| signal_classifier.py | 信号分类 | May 4 更新，可能核心 |
| area_estimator.py | 面积估算 | 资源分析相关 |
| timing_depth.py | 时序深度 | 时序分析相关 |
| pipeline_analyzer.py | 流水线分析 | Pipeline 相关 |
| power_estimation.py | 功耗估算 | 与 power_estimator 重叠？ |
| resource_estimation.py | 资源估算 | 与 area_estimator 重叠？ |
| performance.py | 性能指标 | May 6 更新，可能核心 |

---

## 归档原则

1. **无上游依赖**：没有调用者的脚本优先归档
2. **功能重叠**：功能与其他模块重复的优先归档
3. **长期无更新**：超过 3 个月无修改的需评估
4. **外部数据源**：需要 VCD 等额外输入的优先归档

---
