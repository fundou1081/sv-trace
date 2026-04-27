# SV-Trace 真实RTL测试策略

## 目标

用真实开源项目验证 sv-trace 的可靠性和正确性。

## 测试项目清单

| 项目 | 特点 | 测试价值 |
|------|-------|----------|
| tiny-gpu | 简单GPU | 入门测试 |
| basic_verilog | 基础模块 | 简单结构 |
| picorv32 | RISC-V | 中等复杂度 |
| XiangShan | 高性能RISC-V | 大型SoC |
| opentitan | 安全MCU | 复杂UVM |

## 当前测试

```bash
# 运行当前测试
python -m pytest tests/unit/test_real_projects.py -v
```

## 添加新测试

### 1. 克隆项目到 tests/fixtures/

```bash
git clone https://github.com/YosysHQ/picorv32.git tests/fixtures/picorv32
git clone https://github.com/OpenXiangShan/XiangShan.git tests/fixtures/xiangshan
```

### 2. 创建测试用例

```python
# tests/integration/test_xiangshan.py
import pytest

class TestXiangShan:
    """测试XiangShan大型SoC"""
    
    def test_parse_cpu_core(self):
        """解析CPU核心"""
        # ...
    
    def test_trace_alu_signals(self):
        """追踪ALU信号"""
        # 验证结果
```

## 验证方法

### 黑盒测试
- 解析成功 = 通过
- 不崩溃 = 通过

### 白盒测试（关键！）
- 已知信号路径是否存在
- 已知驱动关系是否正确
- 已知时钟域是否识别

### 回归测试
```bash
# 每次PR必须通过
pytest tests/integration/ -v
```

## CI集成

```yaml
# .github/workflows/test.yml
- name: Test on real projects
  run: |
    pytest tests/integration/ -v --tb=short
```

## 已知限制

- 需要克隆大型项目（约2GB）
- XiangShan完整代码需单独获取
- 部分项目有子模块依赖
