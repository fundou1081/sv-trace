import sys
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

#!/usr/bin/env python3
"""
ModuleDependencyAnalyzer 单元测试
"""
import sys
import os
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

from parse.parser import SVParser
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
            
            parser = SVParser()
            parser.parse_file(f.name)
            
            analyzer = ModuleDependencyAnalyzer(parser)
            graph = analyzer.analyze()
            
            self.assertIn('single', graph.modules)
        
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
            
            parser = SVParser()
            parser.parse_file(f.name)
            
            analyzer = ModuleDependencyAnalyzer(parser)
            graph = analyzer.analyze()
            
            self.assertIn('top', graph.modules)
            self.assertIn('leaf', graph.modules)
            
            top = graph.modules['top']
            self.assertIn('leaf', top.depends_on)
            
            leaf = graph.modules['leaf']
            self.assertIn('top', leaf.depended_by)
        
        os.unlink(f.name)
    
    def test_multi_instance(self):
        """测试多实例"""
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
            
            parser = SVParser()
            parser.parse_file(f.name)
            
            analyzer = ModuleDependencyAnalyzer(parser)
            graph = analyzer.analyze()
            
            top = graph.modules['top']
            self.assertEqual(len(top.instances), 3)
            instance_names = [i.instance_name for i in top.instances]
            self.assertIn('u0', instance_names)
            self.assertIn('u1', instance_names)
            self.assertIn('u2', instance_names)
        
        os.unlink(f.name)
    
    def test_root_leaf_detection(self):
        """测试根/叶子模块检测"""
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
            
            parser = SVParser()
            parser.parse_file(f.name)
            
            analyzer = ModuleDependencyAnalyzer(parser)
            graph = analyzer.analyze()
            
            self.assertIn('top', graph.root_modules)
            self.assertIn('leaf_a', graph.leaf_modules)
            self.assertIn('leaf_b', graph.leaf_modules)
        
        os.unlink(f.name)


if __name__ == '__main__':
    unittest.main()
