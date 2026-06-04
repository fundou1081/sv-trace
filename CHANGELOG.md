# Changelog

All notable changes to **sv-trace** are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

## [1.0.0] - 2026-06-04

**sv-trace 1.0.0** is a full rewrite. The previous 0.1.x line (a multi-tool static analysis library, including `sv-constraint`, `sv-datapath`, `sv-tb-complexity` CLIs and `z3-solver` dependency) has been **yanked from PyPI**. The 1.0.0 line is a focused, single-purpose library: signal tracing with full evidence chain.

### What 1.0.0 is
- A Python library that, given a SystemVerilog signal name, returns all its **drivers** and **loads** with full context (file, line, scope source, clock/reset, condition stack, hierarchical path, port connection).
- Built on [pyslang](https://github.com/MikePopoloski/slang).
- Validated on OpenTitan 6 modules (30,218 drivers, 0 warning, 0 empty driver).
- 160 unit tests, ~7s runtime.

### What 1.0.0 is not
- Not CDC analysis, area/power/timing estimation, lint, FSM extraction, SVA generation, coverage suggestions, TB complexity scoring, code quality scoring, dependency graphs, or visualization. (These were the scope of 0.1.x, intentionally dropped.)

### Highlights

#### M5.1 - Code Evidence Chain
- Every trace carries **verifiable code evidence**: reads back the source file, verifies `source_expr` and `signal_name` actually appear on that line.
- `credibility_score` (0–1) quantifies how much of the trace was verified.
- `is_verified` boolean for fast filtering.
- LLM / user can audit any trace: "show me why this driver is real".

#### M5.1b / c / d / e / f / g - Evidence integration everywhere
- `find_multi_drivers(verify=True)` — multi-driver conflicts with evidence per driver.
- `get_driver_chain(verify=True)` / `get_load_chain(verify=True)` — recursive chain, every hop carries evidence.
- `trace()` / `trace_drivers()` / `trace_loads()` — drivers and loads both auto-verify.
- `dump_driver_chain()` / `dump_load_chain()` — dump the whole chain as one dict (LLM-friendly).
- `dump_multi_drivers()` — dump all conflict signals + their evidence in one call.

#### M5.1h - Syntax-based evidence (NEW in 1.0.0)
- New evidence path that pulls snippet/line directly from the **pyslang syntax tree**, not the file system.
- Cross-file safe: line and snippet are always correct relative to the parsed syntax.
- Works on in-memory SV code (no file required).
- `SyntaxNodeSnapshot` wrapper freezes the syntax text to defend against pyslang buffer reuse bugs.

#### M4 - Real project validation
- Validated on **OpenTitan 6 modules**: uart (418 drivers), spi_device (3,229), dma (401), i2c (1,235), aes (24,065), hmac (870). **30,218 total drivers, 0 warning, 0 empty driver.**

#### M4.1 - Interface / Modport
- Full HierarchicalValue tracking across interface and modport boundaries.
- Bit-select on interface signals (`m.data[3:0]`) supported.

#### M0–M3 - Foundations
- `M0` always_ff/comb/latch procedural block handling.
- `M1` complete TraceResult fields, multi-driver detection, clock/reset extraction, driver-chain recursion with cycle detection.
- `M2` ContextBundle data structure, line / scope-text accuracy.
- `M3` multi-file compilation, hierarchical path tracing (`top.u_sub.signal`), suffix matching.

### Migration from 0.1.x
The 0.1.x API is **not compatible** with 1.0.0. The scope and the dependency surface (z3-solver, graphviz) are gone. If you depend on the old `sv-constraint` / `sv-datapath` / `sv-tb-complexity` CLIs, they will not return with this package. They were experimental, and the project has been refocused on signal tracing.

### Install
```bash
pip install sv-trace
```

### Verified
- 160/160 unit tests pass
- OpenTitan 6 modules parse cleanly (30,218 drivers, 0 warning, 0 empty)
- Python 3.11+ (uses `X | Y` union syntax and `match` statements)
- pyslang >= 10.0

[1.0.0]: https://github.com/fundou1081/sv-trace/releases/tag/v1.0.0
