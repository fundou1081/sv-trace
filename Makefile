# sv-trace Test Runner

PYTHON := python3
PYTEST := pytest
TESTDIR := tests

.PHONY: test test-unit test-int test-e2e test-clean test-coverage

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
