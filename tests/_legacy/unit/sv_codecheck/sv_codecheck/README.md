# sv-codecheck 测试套件

## 定位
代码质量检查、Linting、Style 检查

## 对应源码
- `src/lint/` - Linting 模块

## 测试文件
| test_limitation.py | test_quality_performance.py | test_real_projects.py |

## 运行
```bash
cd tests/unit/sv_codecheck
PYTHONPATH=../../src python3 test_*.py
```
