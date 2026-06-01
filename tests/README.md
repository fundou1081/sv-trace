# sv-trace 测试总览

> 更新时间: 2026-06-01

## 状态

**当前 pytest 套件几乎没有通过的真测试。** 公开 API `trace_signal` 暂未测试。

```
$ python -m pytest tests/ -v
8 failed, 3 passed, 1 warning in 0.40s
```

3 个"通过"都是无关的纯 parse 烟测（不验证追踪功能），其中 1 个还有 warning。

## 目录说明

| 路径 | 内容 | 是否维护 |
|------|------|---------|
| `tests/unit/` | 当前可发现的真测试 | ✅ 维护（待补 10 个） |
| `tests/targeted/` | 40 个 .sv fixture（来自旧测试） | 📦 保留作未来用例 |
| `tests/unit/trace/sv_cases/` | 50+ 个 .sv fixture（按 cdc/driver/fsm 等分类） | 📦 保留 |
| `tests/advanced/test.sv` | 1 个 .sv | 📦 保留 |
| `tests/testbed/cpu.sv` | 1 个 .sv | 📦 保留 |
| `tests/_legacy/` | 167 个失效 .py + 7 .md + 1 .json | 🗄️ 归档，不再维护 |
| `tests/archive/` | 19 个早期失效 .py | 🗄️ 归档 |
| `benchmarks/` | 12 个精心设计的 .sv（顶层 fixture） | ✅ 用作手动验证 |

## 当前测试文件

- `tests/unit/test_real_projects.py` — 11 个 test，9 个 fail（import 旧模块）
- `tests/unit/sv_trace/test_all_tiers_extended.py` — 7 个 test，6 个 fail

## 待写（M1 阶段）

详见 `TEST_PLAN.md`：10 个测试覆盖 `trace_signal` 公开 API。

## 跑测试

```bash
cd ~/my_dv_proj/sv-trace

# 当前（基本 fail）
python -m pytest tests/

# 只跑真测试
python -m pytest tests/unit/

# 看 collection 错误
python -m pytest tests/ --collect-only 2>&1 | head
```

## 手动验证（推荐）

修 P0 bug 之前，可以直接用 benchmark 手动验证：

```python
import sys
sys.path.insert(0, 'src')
from signal_tracer import trace_signal

code = open('benchmarks/01_basic_registers.sv').read()
result = trace_signal('data_out', code, '01.sv')
print(f"drivers={len(result.drivers)}, loads={len(result.loads)}")
for d in result.drivers:
    print(f"  DRV: {d.source_expr} @ line {d.line}")
```

预期修完 P0 bug 后能看到：
```
drivers=2, loads=0
  DRV: 8'h00 @ line 8
  DRV: data_in @ line 10
```
