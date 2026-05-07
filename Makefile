# sv-trace Test Runner

PYTHON := python3
PYTEST := pytest
SRCDIR := src/trace
TESTDIR := tests

.PHONY: test test-unit test-int test-e2e test-clean test-coverage

# 默认运行全部测试
test:
	@$(PYTEST) $(TESTDIR)/ -v --tb=short

# 只跑单元测试
test-unit:
	@$(PYTEST) $(TESTDIR)/unit/ -v --tb=short -m unit

# 只跑集成测试
test-int:
	@$(PYTEST) $(TESTDIR)/integration/ -v --tb=short -m integration

# 只跑 E2E 测试
test-e2e:
	@$(PYTEST) $(TESTDIR)/e2e/ -v --tb=short -m e2e

# 指定工具测试
test-%:
	@tool=$$(echo "$*" | tr '_' '-'); \
	find $(TESTDIR)/unit -name "test_$$tool*.py" -o -name "test_*$$tool*.py" | xargs -I {} $(PYTEST) {} -v

# 清理缓存
test-clean:
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete

# 覆盖率报告
test-coverage:
	@$(PYTEST) $(TESTDIR)/ --cov=$(SRCDIR) --cov-report=html --cov-report=term

# 单独运行某个工具的测试（通过关键字）
test-tools:
	@echo "Usage: make test-tools TOOLS=driver"
	@if [ -n "$(TOOLS)" ]; then \
		find $(TESTDIR)/unit -name "test_*.py" | xargs grep -l "$(TOOLS)" | xargs -I {} $(PYTEST) {} -v; \
	fi
