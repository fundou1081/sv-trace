# sv-trace Test Runner

PYTHON := python3
PYTEST := pytest
TESTDIR := tests

.PHONY: test test-unit test-int test-e2e test-clean test-coverage
.PHONY: build dist publish-test publish dist-clean

# 默认运行全部测试
test:
	@$(PYTEST) $(TESTDIR)/ -v --tb=short

# 只跑单元测试
test-unit:
	@$(PYTEST) $(TESTDIR)/unit/ -v --tb=short

# 只跑集成测试
test-int:
	@$(PYTEST) $(TESTDIR)/integration/ -v --tb=short

# 只跑端到端测试
test-e2e:
	@$(PYTEST) $(TESTDIR)/e2e/ -v --tb=short

# 只跑边界测试
test-edge:
	@$(PYTEST) $(TESTDIR)/edge_cases/ -v --tb=short

# 清理缓存
test-clean:
	@find . -type d -name __pycache__ -exec rm -rf {} +
	@find . -type d -name .pytest_cache -exec rm -rf {} +

# 测试覆盖率
test-coverage:
	@$(PYTEST) $(TESTDIR)/ -v --tb=short --cov=src --cov-report=html

# Driver 测试
test-driver:
	@$(PYTEST) $(TESTDIR)/unit/trace/test_driver*.py -v --tb=short

# Semantic 测试
test-semantic:
	@$(PYTEST) $(TESTDIR)/unit/semantic/ -v --tb=short

# ---------- Release (PyPI) ----------

PYPI_REPO ?= pypi
TEST_PYPI_REPO ?= testpypi

# Build sdist + wheel
build:
	@$(PYTHON) -m build

# Clean build artifacts
dist-clean:
	@rm -rf build/ dist/ *.egg-info src/*.egg-info
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Verify built dist can be installed and imports work
# 注意: 必须在项目根目录跑 (tests 用相对路径 tests/fixtures/...)
dist-verify: build
	@$(PYTHON) -m venv /tmp/sv-trace-verify
	@/tmp/sv-trace-verify/bin/pip install --quiet "pyslang>=10.0,<11" pytest
	@/tmp/sv-trace-verify/bin/pip install --quiet --force-reinstall --no-deps dist/sv_trace-*.whl
	@/tmp/sv-trace-verify/bin/python -c "from signal_tracer import SignalTracer, trace_signal, __version__; print(f'sv-trace {__version__} OK')"
	@/tmp/sv-trace-verify/bin/python -m pytest tests/ -q 2>&1 | tail -3
	@rm -rf /tmp/sv-trace-verify

# Publish to TestPyPI first (validates full upload flow)
publish-test: dist-clean build
	@echo "Uploading to TestPyPI..."
	@$(PYTHON) -m twine upload --repository $(TEST_PYPI_REPO) dist/*

# Publish to production PyPI
publish: dist-clean build
	@echo "Uploading to PyPI..."
	@$(PYTHON) -m twine upload --repository $(PYPI_REPO) dist/*

# Yank old versions (0.1.0, 0.1.1) — these are legacy multi-tool packages
# and the 1.0.0 line is a full rewrite. Run this AFTER 1.0.0 is live.
yank-legacy:
	@$(PYTHON) -m twine yank --repository $(PYPI_REPO) sv-trace==0.1.0 || true
	@$(PYTHON) -m twine yank --repository $(PYPI_REPO) sv-trace==0.1.1 || true
