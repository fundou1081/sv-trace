# ADR-0001: 使用 pyslang 作为解析引擎

## 状态
Accepted

## 背景
需要为 SV Trace 库选择一个 SystemVerilog 解析引擎，要求：
1. 支持完整的 SystemVerilog 语法
2. 提供 Python binding
3. 能够处理大型项目
4. 活跃维护

## 决策
使用 [pyslang](https://github.com/MikePopoloski/slang) 作为解析引擎。

### 备选方案考虑
1. **sv-lang/slang** - 选择原因：Python binding 成熟，解析鲁棒，活跃开发
2. **Verilator** - 不支持 Python binding
3. **其他开源 parser** - 功能或维护状态不足

## 后果
- 依赖 pyslang (通过 pip 安装)
- 需要处理 pyslang API 的限制

## 相关
- 安装：`pip install pyslang`
- 源码：`~/my_dv_proj/slang`
