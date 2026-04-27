# sv-trace 测试套件

## 定位
RTL 信号追踪、数据流分析、依赖图构建

## 对应源码
- `src/trace/` - 追踪器模块

## 测试文件
| test_driver.py | test_comprehensive.py | test_control_dependency.py |
| test_foundation.py | test_foundation_modules.py | test_dependency.py |

## 运行
```bash
cd tests/unit/sv_trace
PYTHONPATH=../../src python3 test_*.py
```
