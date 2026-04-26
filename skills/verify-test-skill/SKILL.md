---
name: verify-test-manager
description: 测试用例管理系统，用于管理芯片验证过程中的测试用例。支持增删改查、测试套件管理、结果记录和统计分析。当用户需要管理验证测试、追踪测试状态、组织测试套件时使用。
---

# Verify Test Manager Skill

测试用例管理系统

## 功能

- **测试用例CRUD**: 添加、查询、更新、删除测试用例
- **测试套件管理**: 创建测试套件、管理套件中的测试
- **结果记录**: 记录每次测试的执行结果
- **统计分析**: 统计测试覆盖率、状态分布

## CLI工具

```bash
# 测试用例管理
verify-test add --name <name> --module <module> --level P0|P1|P2
verify-test list [--module <module>] [--level <level>] [--status <status>]
verify-test get <test_id>
verify-test update <test_id> [--status <status>] [--owner <owner>]
verify-test remove <test_id>
verify-test record <test_id> --status pass|fail [--duration <ms>] [--seed <seed>]
verify-test stats

# 测试套件管理
verify-suite create --name <name> [--tests <id1,id2,...>]
verify-suite list
verify-suite get <suite_id>
verify-suite add-test <suite_id> <test_id>
verify-suite remove-test <suite_id> <test_id>
verify-suite remove <suite_id>
```

## Python API

```python
from verify.test_manager import TestManager
from verify.test_case import TestLevel, TestStatus

# 初始化
tm = TestManager('./test_db')

# 添加测试用例
test = tm.add_test(
    name='uart_baud_rate',
    module='uart',
    level='P0',
    owner='john'
)

# 查询
tests = tm.list_tests(module='uart', level='P0')
test = tm.get_test('1')

# 更新
tm.update_test('1', status='pass')

# 记录结果
tm.record_result('1', status='pass', duration_ms=1500, seed='0x12345678')

# 统计
stats = tm.get_stats()
# {'total_tests': 10, 'status_counts': {...}, 'level_counts': {...}}
```

## 数据模型

### TestCase
```python
{
    'id': '1',
    'name': 'uart_baud_rate',
    'module': 'uart',
    'level': 'P0',  # P0/P1/P2
    'status': 'pass',  # pass/fail/blocked/not_run/skipped
    'owner': 'john',
    'tags': ['uart', 'baud'],
    'description': '测试波特率精度',
    'coverage_items': ['cov_baud_115200', 'cov_baud_9600'],
    'related_bugs': ['bug_001'],
    'related_spec': 'SPEC-001',
    'seed': '0x12345678',
    'run_count': 5,
    'last_run': '2026-04-27T00:00:00'
}
```

### TestSuite
```python
{
    'id': 's1',
    'name': 'uart_basic',
    'test_ids': ['1', '2', '3'],
    'description': 'UART基础功能测试'
}
```

## 环境变量

```bash
export VERIFY_DB_PATH=/path/to/test_db  # 数据库路径
```

## 示例会话

```
用户: 添加一个测试用例，测试UART的115200波特率精度
助手: 
```bash
verify-test add --name "uart_baud_115200" --module uart --level P0 --desc "测试115200波特率精度" --owner john --tags uart baud
```

用户: 列出所有UART模块的测试
助手:
```bash
verify-test list --module uart
```

用户: 标记第一个测试通过
助手:
```bash
verify-test update 1 --status pass
```
