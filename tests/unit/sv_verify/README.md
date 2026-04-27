# sv-verify 测试套件

## 定位
验证 IP 开发支持、约束分析、TB 质量评估

## 对应源码
- `src/verify/` - 验证工具
- `src/debug/` - 调试分析

## 测试文件
| test_app_tools.py | test_fsm.py | test_hierarchy.py |
| test_targeted.py | test_corners.py | test_cdc_edge_cases.py |

## 运行
```bash
cd tests/unit/sv_verify
PYTHONPATH=../../src python3 test_*.py
```
