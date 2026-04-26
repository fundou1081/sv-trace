---
name: bug-tracker
description: Bug追踪系统，用于管理芯片验证过程中发现的Bug。
---

# Bug Tracker Skill

## CLI

```bash
bug-tracker create --title "TX错误" --module uart --severity high
bug-tracker list --module uart
bug-tracker update B1 --status fixed
bug-tracker stats
```

## Python API

```python
from bugs.bug_tracker import BugTracker
bt = BugTracker('./bug_db')
bug = bt.create_bug(title="TX错误", module="uart", severity="high")
bugs = bt.list_bugs(module="uart")
bt.record_reproduce("B1", seed="0x1234", attempt_count=100, success_count=5)
```
