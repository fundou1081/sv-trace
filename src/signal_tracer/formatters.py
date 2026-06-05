"""
formatters.py — 人类友好的箭头式输出

设计目标: 让 trace 输出的"信号流向"用箭头直接可视化,
人在终端 / 文档 / 聊天里一眼能看明白谁驱动谁, 谁被谁读。

箭头语义 (固定, 全模块统一):
  ←   driver (信号被这个表达式驱动, 数据从右往左流到 LHS)
  →   load   (信号被这个表达式读取, 数据从左往右流到 RHS)
  ⚠   多驱动冲突
  ✓   verified (credibility >= 0.8)
  ✗   not verified (credibility < 0.8)
  ⤴   cross-file 跨文件
  ↻   cycle detected

设计原则:
  - 跟 summary() / to_dict() 并存, 不破坏现有 API
  - 字符串宽度自适配 (signal 名短时用紧凑, 长时截断 + '…')
  - 任何字段缺失都优雅降级, 不会 KeyError
  - 颜色: 默认无 (TTY 检测可选 ANSI), agent 输出关掉
"""
from __future__ import annotations

from typing import List, Optional, Sequence, Union

# === 箭头符号 (固定常量, 改了破坏所有用户) ===
ARROW_DRIVER = "←"   # DRIVER: signal_name ← source_expr
ARROW_LOAD = "→"     # LOAD:   signal_name → expr_using_it
ARROW_BOTH = "↔"     # 既被驱动又被读取 (少见, 只在循环里)
WARN = "⚠"
CHECK = "✓"
CROSS = "✗"
CROSS_FILE = "⤴"
CYCLE = "↻"
PIPE = "|"           # 多 driver 之间分隔


def _truncate(s: str, max_len: int = 40) -> str:
    """智能截断: 超长加 …, 保留开头 (通常更有信息量)"""
    if s is None:
        return ""
    if len(s) <= max_len:
        return s
    return s[:max_len - 1] + "…"


def _file_basename(path: str) -> str:
    """从 path 里取文件名, 没路径就原样返回"""
    if not path:
        return ""
    return path.rsplit("/", 1)[-1]


def format_driver(driver, max_expr_len: int = 40, show_location: bool = True,
                  show_credibility: bool = True) -> str:
    """单个 driver 的人类友好输出

    driver 可以是 TraceResult/DriverTrace 实例，也可以是 dump_multi_drivers 返回的 dict。
    两种都兼容。

    例:
      count ← count + data_in @ counter.sv:11
      count ← 8'h00 @ counter.sv:9 ✓ cred=1.0
      count ← count + data_in ⤴ @ sub.sv:42 ✓
    """
    # 适配 dict 输入
    if isinstance(driver, dict):
        d = driver
        sig = d.get("signal_name", "?")
        expr = _truncate(d.get("source_expr", "?"), max_expr_len)
        file_ = d.get("file", "")
        line = d.get("line", 0)
        hier = d.get("hierarchical_path", "")
        is_cross = d.get("is_cross_file", False)
        cred = d.get("credibility_score", d.get("credibility"))
    else:
        sig = getattr(driver, "signal_name", "") or "?"
        expr = _truncate(getattr(driver, "source_expr", "") or "?", max_expr_len)
        file_ = getattr(driver, "file", "") or ""
        line = getattr(driver, "line", 0) or 0
        hier = getattr(driver, "hierarchical_path", "") or ""
        is_cross = getattr(driver, "is_cross_file", False)
        cred = getattr(driver, "_credibility", None)
        if cred is None and hasattr(driver, "to_context"):
            try:
                ctx = driver.to_context()
                cred = ctx.to_dict().get("credibility_score")
            except Exception:
                cred = None

    parts = [f"{sig} {ARROW_DRIVER} {expr}"]

    if show_location and file_:
        loc = f"@ {_file_basename(file_)}:{line}"
        if hier:
            loc += f" [{hier}]"
        if is_cross:
            loc += f" {CROSS_FILE}"
        parts.append(loc)

    if show_credibility and cred is not None:
        try:
            cred_f = float(cred)
            mark = CHECK if cred_f >= 0.8 else CROSS
            parts.append(f"{mark} cred={cred_f:.2f}")
        except (TypeError, ValueError):
            pass

    return " ".join(parts)


def format_load(load, max_expr_len: int = 40, show_location: bool = True) -> str:
    """单个 load 的人类友好输出

    例:
      count → mem[rd_ptr] @ fifo.sv:42
    """
    sig = load.signal_name or "?"
    expr = _truncate(load.source_expr or "?", max_expr_len)
    parts = [f"{sig} {ARROW_LOAD} {expr}"]

    if show_location and load.file:
        loc = f"@ {_file_basename(load.file)}:{load.line}"
        if load.hierarchical_path:
            loc += f" [{load.hierarchical_path}]"
        parts.append(loc)

    return " ".join(parts)


def format_trace_arrow(trace, max_expr_len: int = 40) -> str:
    """自动判 DRIVER/LOAD, 选箭头方向

    用在 for 循环里, 不管 trace_type 都能 print
    """
    if getattr(trace, "trace_type", None) is not None and trace.trace_type.value == "load":
        return format_load(trace, max_expr_len=max_expr_len)
    return format_driver(trace, max_expr_len=max_expr_len)


def format_driver_chain(chain: Sequence, signal: str = "", direction: str = "driver",
                        has_cycle: bool = False, cross_files: Optional[list] = None,
                        style: str = "arrow") -> str:
    """链追踪的输出 (M5.1k)

    chain 可以是 List[str] (老 API) 或 List[TraceResult] (新 API)。
    自动提取 signal_name。

    style 选:
      - "arrow" (默认): 一行箭头式
          data_out ← c ← b ← a
      - "tree": tree 风格 (长链友好)
          Driver chain: data_out (3 hops)
          ├─ data_out    [top.sv:5]
          │  ← c         [sub.sv:12] ✓ cred=1.00
          │  ← b         [sub.sv:8]  ✓ cred=1.00
          │  ← a         [top.sv:3]  ✓ cred=1.00
      - "ascii": 同 tree 但用 ASCII (没 box-drawing)
      - "vertical": 每行一个信号 + 连接符
          data_out  [top.sv:5]
              ← c      [sub.sv:12] ✓
              ← b      [sub.sv:8]  ✓
              ← a      [top.sv:3]  ✓
      - "all" / "both": arrow + tree 两个都返回 (多行)
    """
    if not chain:
        return f"(no {'driver' if direction == 'driver' else 'load'} chain)"

    if style == "tree":
        return _format_chain_tree(chain, signal=signal, direction=direction,
                                  has_cycle=has_cycle, cross_files=cross_files,
                                  use_box=True)
    if style == "ascii":
        return _format_chain_tree(chain, signal=signal, direction=direction,
                                  has_cycle=has_cycle, cross_files=cross_files,
                                  use_box=False)
    if style == "vertical":
        return _format_chain_vertical(chain, direction=direction, signal=signal)
    if style in ("all", "both"):
        arrow_out = format_driver_chain(
            chain, signal=signal, direction=direction,
            has_cycle=has_cycle, cross_files=cross_files, style="arrow",
        )
        tree_out = format_driver_chain(
            chain, signal=signal, direction=direction,
            has_cycle=has_cycle, cross_files=cross_files, style="tree",
        )
        return f"{arrow_out}\n{tree_out}"

    # 默认 arrow
    chain_names = [getattr(c, "signal_name", str(c)) for c in chain]
    arrow = ARROW_DRIVER if direction == "driver" else ARROW_LOAD
    sep = f" {arrow} "
    out = sep.join(chain_names)

    markers = []
    if cross_files and len(cross_files) > 1:
        markers.append(f"{CROSS_FILE} cross-file")
    if has_cycle:
        markers.append(f"{CYCLE} cycle detected")

    if markers:
        out += "  (" + ", ".join(markers) + ")"

    return out


def _format_chain_vertical(chain: Sequence, direction: str = "driver",
                            signal: str = "") -> str:
    """vertical 风格: 每行一个信号 + 上一层连接 (最紧凑, 适合 chat/邮件)

    例:
      data_out        [top.sv:5]  ✓
        ← c           [sub.sv:12] ✓
        ← b           [sub.sv:8]  ✓
        ← a           [top.sv:3]  ✓
    """
    if not chain:
        return "(no chain)"

    arrow = ARROW_DRIVER if direction == "driver" else ARROW_LOAD
    lines = []

    for i, c in enumerate(chain):
        # 拿 signal_name
        if hasattr(c, "signal_name"):
            name = c.signal_name
            file_ = getattr(c, "file", "")
            line_no = getattr(c, "line", 0)
            cred = getattr(c, "_credibility", None)
            if cred is None and c.__class__.__name__ != "str":
                try:
                    ctx = c.to_context()
                    cred = ctx.to_dict().get("credibility_score")
                except Exception:
                    cred = None
        else:
            name = str(c)
            file_ = ""
            line_no = 0
            cred = None

        location = ""
        if file_:
            location = f"@ {_file_basename(file_)}:{line_no}"

        cred_str = ""
        if cred is not None:
            try:
                mark = CHECK if float(cred) >= 0.8 else CROSS
                cred_str = f" {mark} cred={float(cred):.2f}"
            except (TypeError, ValueError):
                pass

        # 缩进
        prefix = "  " * i
        if i == 0:
            # 第一行: 起点信号
            lines.append(f"{prefix}{name} {location}{cred_str}")
        else:
            # 后续行: 箭头
            lines.append(f"{prefix}{arrow} {name} {location}{cred_str}")

    return "\n".join(lines)


def _format_chain_tree(chain: Sequence, signal: str = "", direction: str = "driver",
                        has_cycle: bool = False, cross_files: Optional[list] = None,
                        use_box: bool = True) -> str:
    """tree 风格: box-drawing 字符表示层级

    例 (use_box=True):
      Driver chain: data_out (3 hops)
      ├─ data_out    [top.sv:5]      ✓
      │  ← c         [sub.sv:12]     ✓
      │  ← b         [sub.sv:8]      ✓
      └─ a           [top.sv:3]      ✓
      (cycle detected, cross-file)

    例 (use_box=False, ASCII):
      +-- data_out   [top.sv:5]      ok
      |   <- c       [sub.sv:12]     ok
      |   <- b       [sub.sv:8]      ok
      +-- a          [top.sv:3]      ok
    """
    if not chain:
        return "(no chain)"

    # box-drawing 字符 (Unicode) vs ASCII
    if use_box:
        T = "├─"   # tee (非末节点)
        L = "│"   # vertical line
        C = "└─"   # corner (末节点)
    else:
        T = "+--"
        L = "|"
        C = "+--"

    arrow = ARROW_DRIVER if direction == "driver" else ARROW_LOAD

    # 提取每跳信息
    rows = []
    for c in chain:
        if hasattr(c, "signal_name"):
            name = c.signal_name
            file_ = getattr(c, "file", "")
            line_no = getattr(c, "line", 0)
            cred = getattr(c, "_credibility", None)
            if cred is None:
                try:
                    ctx = c.to_context()
                    cred = ctx.to_dict().get("credibility_score")
                except Exception:
                    cred = None
        else:
            name = str(c)
            file_ = ""
            line_no = 0
            cred = None
        rows.append({
            "name": name,
            "file": file_,
            "line": line_no,
            "cred": cred,
        })

    n = len(rows)
    head_signal = signal or rows[0]["name"]

    # 拼链名
    lines = []
    head = f"{'Driver' if direction == 'driver' else 'Load'} chain: {head_signal} ({n} hops"
    if cross_files and len(cross_files) > 1:
        head += f", {CROSS_FILE} cross-file"
    if has_cycle:
        head += f", {CYCLE} cycle"
    head += ")"
    lines.append(head)

    # 拼每行
    for i, row in enumerate(rows):
        is_last = (i == n - 1)
        # 节点连线符号
        if i == 0:
            # 起点
            prefix = f"  {T} "
        elif is_last:
            prefix = f"  {C} "
        else:
            prefix = f"  {L}  "

        # 节点内容
        if i == 0:
            # 第一行只显示 signal + location
            content = row["name"]
            if row["file"]:
                content += f"  [{_file_basename(row['file'])}:{row['line']}]"
            if row["cred"] is not None:
                try:
                    mark = CHECK if float(row["cred"]) >= 0.8 else CROSS
                    content += f"  {mark} cred={float(row['cred']):.2f}"
                except (TypeError, ValueError):
                    pass
        else:
            # 后续行: 箭头 + signal + location
            content = f"{arrow} {row['name']}"
            if row["file"]:
                content += f"  [{_file_basename(row['file'])}:{row['line']}]"
            if row["cred"] is not None:
                try:
                    mark = CHECK if float(row["cred"]) >= 0.8 else CROSS
                    content += f"  {mark} cred={float(row['cred']):.2f}"
                except (TypeError, ValueError):
                    pass

        lines.append(prefix + content)

    return "\n".join(lines)


def format_multi_driver(signal: str, drivers: Sequence, show_credibility: bool = True) -> str:
    """多驱动冲突的箭头输出

    例:
      data ⚠ 2 drivers:
        data ← 8'hAA @ multi.sv:10 ✓ cred=1.0
        data ← 8'h55 @ multi.sv:15 ✓ cred=1.0
    """
    n = len(drivers)
    if n == 0:
        return f"{signal} (no drivers)"
    if n == 1:
        return format_driver(drivers[0], show_credibility=show_credibility)

    lines = [f"{signal} {WARN} {n} drivers:"]
    for d in drivers:
        lines.append("  " + format_driver(d, show_credibility=show_credibility))
    return "\n".join(lines)


def format_evidence_chain(trace, max_expr_len: int = 40) -> str:
    """evidence 完整链 (driver/load + location + verification)

    例:
      count ← count + data_in @ counter.sv:11 ✓ verified (cred=1.0)
        Evidence: count + data_in 真在该行 (source_expr ✓, signal ✓)
    """
    sig = trace.signal_name or "?"
    expr = _truncate(trace.source_expr or "?", max_expr_len)
    base = f"{sig} {ARROW_DRIVER} {expr}"

    # location
    if trace.file:
        loc = f" @ {_file_basename(trace.file)}:{trace.line}"
        if trace.hierarchical_path:
            loc += f" [{trace.hierarchical_path}]"
        base += loc

    # evidence
    cred = getattr(trace, "_credibility", None)
    if cred is None and hasattr(trace, "to_context"):
        ctx = trace.to_context()
        d = ctx.to_dict()
        cred = d.get("credibility_score")
        verified = d.get("is_verified")
        if verified is not None:
            mark = CHECK if verified else CROSS
            base += f" {mark} {'verified' if verified else 'unverified'} (cred={cred:.2f})" if cred is not None else f" {mark} verified"

    return base


def format_dump_summary(dump: dict, style: str = "arrow") -> str:
    """dump_driver_chain / dump_multi_drivers 的 summary 部分转箭头式 (M5.1k)

    style 选 (仅 chain dump 有用, multi-driver dump 不走 style):
      - "arrow" (默认): 一行箭头 + summary
      - "tree": tree 风格
      - "ascii": ASCII tree
      - "vertical": 每行一个信号
      - "all" / "both": arrow + tree 两个都返

    例 (arrow):
      Chain data_out: 4 hops, avg_cred=0.95, cross-file ✗, cycle ✗
        data_out ← c ✓ ← b ✓ ← a ✓

    例 (tree):
      Driver chain: data_out (4 hops)
      ├─ data_out    [top.sv:5]    ✓
      │  ← c         [sub.sv:12]   ✓
      │  ← b         [sub.sv:8]    ✓
      │  ← a         [top.sv:3]    ✓
    """
    if not dump:
        return "(empty dump)"

    # dump 可能是 chain dump 或 multi-driver dump
    if "hops" in dump:
        if style in ("all", "both"):
            arrow_out = _format_chain_dump(dump, style="arrow")
            tree_out = _format_chain_dump(dump, style="tree")
            return f"{arrow_out}\n{tree_out}"
        return _format_chain_dump(dump, style=style)
    if "conflicts" in dump or "summary" in dump:
        return _format_multi_dump(dump)
    return f"(unknown dump format: keys={list(dump.keys())})"


def _format_chain_dump(dump: dict, style: str = "arrow") -> str:
    sig = dump.get("signal_name", "?")
    raw_dir = dump.get("direction", "driver")
    # dump 用 upstream/downstream, 我们统一为 driver/load
    if raw_dir == "upstream":
        direction = "driver"
    elif raw_dir == "downstream":
        direction = "load"
    else:
        direction = raw_dir
    arrow = ARROW_DRIVER if direction == "driver" else ARROW_LOAD
    summary = dump.get("summary", {})
    hops = dump.get("hops", [])

    n = summary.get("total_hops", len(hops))
    avg = summary.get("avg_credibility")
    cross = summary.get("cross_files", False)
    cycle = summary.get("has_cycle", False)

    # 如果 tree/vertical 风格, 复用 _format_chain_tree/vertical
    if style in ("tree", "ascii") and hops:
        # 从 dump["hops"] (list of dict) 还原伪 TraceResult-like
        pseudo_chain = []
        for h in hops:
            class _Pseudo:
                pass
            p = _Pseudo()
            p.signal_name = h.get("signal_name", "?")
            p.file = h.get("file", "")
            p.line = h.get("line", 0)
            p._credibility = h.get("credibility_score")
            p.to_context = lambda: type("_C", (), {"to_dict": lambda self: {"credibility_score": p._credibility}})()
            pseudo_chain.append(p)
        cross_files = ["multi-file"] if cross else None
        return _format_chain_tree(
            pseudo_chain, signal=sig, direction=direction,
            has_cycle=cycle, cross_files=cross_files,
            use_box=(style == "tree"),
        )

    if style == "vertical" and hops:
        pseudo_chain = []
        for h in hops:
            class _Pseudo:
                pass
            p = _Pseudo()
            p.signal_name = h.get("signal_name", "?")
            p.file = h.get("file", "")
            p.line = h.get("line", 0)
            p._credibility = h.get("credibility_score")
            p.to_context = lambda: type("_C", (), {"to_dict": lambda self: {"credibility_score": p._credibility}})()
            pseudo_chain.append(p)
        return _format_chain_vertical(pseudo_chain, direction=direction, signal=sig)

    # 默认 arrow
    head = f"Chain {sig}: {n} hops"
    if avg is not None:
        head += f", avg_cred={avg:.2f}"
    head += f", cross-file {'✓' if cross else '✗'}"
    head += f", cycle {'✓' if cycle else '✗'}"

    if not hops:
        return head

    # 拼箭头链
    parts = [hops[0].get("signal_name", "?")]
    for h in hops[1:]:
        cred = h.get("credibility_score")
        mark = ""
        if cred is not None:
            mark = f" {CHECK if cred >= 0.8 else CROSS}"
        parts.append(f"{arrow}{mark}")
        parts.append(h.get("signal_name", "?"))
    chain_str = " ".join(parts)

    return f"{head}\n  {chain_str}"


def _format_multi_dump(dump: dict) -> str:
    summary = dump.get("summary", {})
    conflicts = dump.get("conflicts", [])

    head = f"Multi-drivers: {summary.get('total_conflict_signals', len(conflicts))} conflict signals, "
    head += f"{summary.get('total_drivers', '?')} total drivers, "
    avg = summary.get("avg_credibility")
    if avg is not None:
        head += f"avg_cred={avg:.2f}"

    if not conflicts:
        return head + "\n  (no conflicts)"

    lines = [head]
    for c in conflicts:
        sig = c.get("signal", "?")
        drivers = c.get("drivers", [])
        lines.append("")
        lines.append(format_multi_driver(sig, drivers))
    return "\n".join(lines)


def format_all(trace_result, max_expr_len: int = 40) -> str:
    """一键格式化一个 TraceResult: drivers + loads 都用箭头输出

    例:
      DRIVERS (2):
        count ← 8'h00 @ counter.sv:9 ✓ cred=1.0
        count ← count + data_in @ counter.sv:11 ✓ cred=1.0
      LOADS (0):
        (none)
    """
    sections = []

    if trace_result.drivers:
        lines = [f"DRIVERS ({len(trace_result.drivers)}):"]
        for d in trace_result.drivers:
            lines.append("  " + format_driver(d, max_expr_len=max_expr_len))
        sections.append("\n".join(lines))
    else:
        sections.append("DRIVERS (0):\n  (none)")

    if trace_result.loads:
        lines = [f"LOADS ({len(trace_result.loads)}):"]
        for ld in trace_result.loads:
            lines.append("  " + format_load(ld, max_expr_len=max_expr_len))
        sections.append("\n".join(lines))
    else:
        sections.append("LOADS (0):\n  (none)")

    return "\n".join(sections)
