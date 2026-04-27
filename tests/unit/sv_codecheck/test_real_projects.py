import sys
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

"""
真实项目测试 - 用开源项目验证解析能力

使用真实的SystemVerilog项目来验证sv-trace的可靠性。
所有项目都是从开源仓库克隆的。
"""

import os
import sys
import pytest

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
        from parse import SVParser
        
        parser = SVParser()
        for root, dirs, files in os.walk(project_path):
            for f in files:
                if f.endswith('.sv'):
                    fpath = os.path.join(root, f)
                    try:
                        parser.parse_file(fpath)
                    except Exception as e:
                        pytest.fail(f"Failed to parse {fpath}: {e}")
        
        assert len(parser.trees) > 0, "No files parsed"
    
    def test_drive_load_tracing(self, project_path):
        """测试驱动追踪"""
        from trace.driver import DriverTracer
        from parse import SVParser
        
        parser = SVParser()
        
        # 找第一个模块
        for root, dirs, files in os.walk(project_path):
            for f in files:
                if f.endswith('.sv'):
                    fpath = os.path.join(root, f)
                    parser.parse_file(fpath)
                    if parser.trees:
                        break
            if parser.trees:
                break
        
        tracer = DriverTracer(parser)
        drivers = tracer.trace()
        
        # 验证：driver结果应该是确定的
        assert drivers is not None


class TestBasicVerilog:
    """Basic Verilog项目测试"""
    
    @pytest.fixture
    def project_path(self):
        return get_project_path('basic_verilog')
    
    def test_parse_verilog(self, project_path):
        """解析Verilog文件"""
        from parse import SVParser
        
        parser = SVParser()
        
        for root, dirs, files in os.walk(project_path):
            for f in files:
                if f.endswith('.v') or f.endswith('.sv'):
                    fpath = os.path.join(root, f)
                    try:
                        parser.parse_file(fpath)
                    except Exception as e:
                        pytest.fail(f"Failed to parse {fpath}: {e}")
        
        assert len(parser.trees) > 0


class TestConstraintAnalysis:
    """约束分析测试 - 用项目中的SV文件"""
    
    @pytest.fixture
    def project_path(self):
        return get_project_path('basic_verilog')
    
    def test_constraint_parsing(self, project_path):
        """测试约束解析"""
        from debug.constraint_parser_v2 import parse_constraints
        from parse import SVParser
        
        parser = SVParser()
        
        # 扫描项目中的SV文件
        sv_files = []
        for root, dirs, files in os.walk(project_path):
            for f in files:
                if f.endswith('.sv'):
                    sv_files.append(os.path.join(root, f))
        
        if not sv_files:
            pytest.skip("No .sv files found")
        
        parser.parse_file(sv_files[0])
        cp = parse_constraints(parser)
        
        # 验证：约束分析不应该崩溃
        assert cp is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
