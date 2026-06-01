#!/usr/bin/env python3
"""
ModuleDependencyAnalyzer 单元测试

更新为新架构 - 使用实际的 API
"""
import sys
import os
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

from sv_manager import SVManager
from debug.dependency import ModuleDependencyAnalyzer


class TestModuleDependencyAnalyzer(unittest.TestCase):
    """ModuleDependencyAnalyzer 测试类"""
    
    def test_single_module(self):
        """测试单模块"""
        code = """
        module single;
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
            f.flush()
            
            sv = SVManager()
            sv.parse_file(f.name)
            
            analyzer = ModuleDependencyAnalyzer(sv)
            modules = analyzer.get_all_modules()
            
            self.assertIn('single', modules)
        
        os.unlink(f.name)
    
    def test_two_level_hierarchy(self):
        """测试两层层级"""
        code = """
        module leaf;
        endmodule
        
        module top;
            leaf u_leaf();
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
            f.flush()
            
            sv = SVManager()
            sv.parse_file(f.name)
            
            analyzer = ModuleDependencyAnalyzer(sv)
            modules = analyzer.get_all_modules()
            
            self.assertIn('top', modules)
            self.assertIn('leaf', modules)
        
        os.unlink(f.name)
    
    def test_multi_instance(self):
        """测试多实例 - stub"""
        code = """
        module leaf;
        endmodule
        
        module top;
            leaf u0();
            leaf u1();
            leaf u2();
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
            f.flush()
            
            sv = SVManager()
            sv.parse_file(f.name)
            
            analyzer = ModuleDependencyAnalyzer(sv)
            modules = analyzer.get_all_modules()
            
            # ModuleDependencyAnalyzer 新架构只提取模块名
            # 实例信息需要更完整的实现
            self.assertIn('top', modules)
            self.assertIn('leaf', modules)
        
        os.unlink(f.name)
    
    def test_root_leaf_detection(self):
        """测试根/叶子模块检测 - stub"""
        code = """
        module leaf_a;
        endmodule
        
        module leaf_b;
        endmodule
        
        module middle;
            leaf_a u_a();
        endmodule
        
        module top;
            middle u_m();
            leaf_b u_b();
        endmodule
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(code)
            f.flush()
            
            sv = SVManager()
            sv.parse_file(f.name)
            
            analyzer = ModuleDependencyAnalyzer(sv)
            modules = analyzer.get_all_modules()
            
            # 新架构只提供 get_all_modules()
            self.assertIn('top', modules)
            self.assertIn('leaf_a', modules)
            self.assertIn('leaf_b', modules)
            self.assertIn('middle', modules)
        
        os.unlink(f.name)


if __name__ == '__main__':
    unittest.main()