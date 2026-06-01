"""真实项目测试 - 用开源项目验证解析能力

使用真实的SystemVerilog项目来验证sv-trace的可靠性。
所有项目都是从开源仓库克隆的。

更新为新架构 (pyslang 重构后的 API)
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# 项目本地路径
TEST_PROJECTS = {
    'tiny-gpu': '/Users/fundou/my_dv_proj/tiny-gpu',
    'basic_verilog': '/Users/fundou/my_dv_proj/basic_verilog',
}

def get_project_path(name):
    """获取项目路径，不存在则跳过"""
    path = TEST_PROJECTS.get(name)
    if path and os.path.exists(path):
        return path
    pytest.skip(f"Project {name} not found at {path}")


class TestTinyGPU:
    """TinyGPU项目测试"""
    
    @pytest.fixture
    def project_path(self):
        return get_project_path('tiny-gpu')
    
    def test_parse_all_files(self, project_path):
        """解析所有SV文件"""
        from sv_manager import SVManager
        
        sv = SVManager()
        
        for root, dirs, files in os.walk(project_path):
            for f in files:
                if f.endswith('.sv'):
                    fpath = os.path.join(root, f)
                    try:
                        sv.parse_file(fpath)
                    except Exception as e:
                        pytest.fail(f"Failed to parse {fpath}: {e}")
        
        assert len(sv.trees) > 0, "No files parsed"
    
    def test_drive_load_tracing(self, project_path):
        """测试驱动追踪"""
        from sv_manager import SVManager
        from trace import DriverTracer
        
        sv = SVManager()
        
        # 找第一个模块
        for root, dirs, files in os.walk(project_path):
            for f in files:
                if f.endswith('.sv'):
                    fpath = os.path.join(root, f)
                    sv.parse_file(fpath)
                    if sv.trees:
                        break
            if sv.trees:
                break
        
        if not sv.trees:
            pytest.skip("No files parsed")
        
        tree = list(sv.trees.values())[0]
        tracer = DriverTracer()
        tracer.collect(tree, list(sv.trees.keys())[0])
        
        # 验证：driver 结果应该是确定的
        assert tracer.drivers is not None
        assert isinstance(tracer.drivers, dict)


class TestBasicVerilog:
    """Basic Verilog项目测试"""
    
    @pytest.fixture
    def project_path(self):
        return get_project_path('basic_verilog')
    
    def test_parse_verilog(self, project_path):
        """解析Verilog文件"""
        from sv_manager import SVManager
        
        sv = SVManager()
        
        for root, dirs, files in os.walk(project_path):
            for f in files:
                if f.endswith('.v') or f.endswith('.sv'):
                    fpath = os.path.join(root, f)
                    try:
                        sv.parse_file(fpath)
                    except Exception as e:
                        # 跳过编码错误的文件
                        if 'UnicodeDecodeError' in str(type(e)):
                            continue
                        pytest.fail(f"Failed to parse {fpath}: {e}")
        
        assert len(sv.trees) > 0, "No files parsed"


class TestConstraintAnalysis:
    """约束分析测试 - 用项目中的SV文件"""
    
    @pytest.fixture
    def project_path(self):
        return get_project_path('basic_verilog')
    
    def test_constraint_parsing(self, project_path):
        """测试约束解析"""
        from debug.constraint_parser_v2 import parse_constraints
        from sv_manager import SVManager
        
        sv = SVManager()
        
        # 扫描项目中的 SV 文件
        sv_files = []
        for root, dirs, files in os.walk(project_path):
            for f in files:
                if f.endswith('.sv'):
                    sv_files.append(os.path.join(root, f))
        
        if not sv_files:
            pytest.skip("No .sv files found")
        
        sv.parse_file(sv_files[0])
        cp = parse_constraints(sv)
        
        # 验证：约束分析不应该崩溃
        assert cp is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])