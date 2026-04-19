"""Unit tests for class-related extractors."""

import sys
import os
import unittest
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from parse.parser import SVParser
from debug.class_extractor import ClassExtractor
from debug.class_hierarchy import ClassHierarchyBuilder
from debug.class_usage import ClassInstantiationTracer


def write_temp_file(code):
    """Helper to write code to a temp file and return the path."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code)
        return f.name


class TestClassExtractor(unittest.TestCase):
    """Test ClassExtractor functionality."""

    def test_basic_class(self):
        """Test basic class extraction."""
        code = 'class packet; rand bit [7:0] data; rand bit valid; endclass'
        fname = write_temp_file(code)
        
        try:
            parser = SVParser()
            parser.parse_file(fname)
            
            extractor = ClassExtractor(parser)
            classes = extractor.extract()
            
            self.assertIn('packet', classes)
            self.assertEqual(len(classes['packet'].properties), 2)
            
            p = classes['packet']
            self.assertEqual(p.name, 'packet')
            self.assertEqual(p.extends, None)
            self.assertEqual(len(p.get_rand_properties()), 2)
        finally:
            os.unlink(fname)

    def test_class_with_constraints(self):
        """Test class constraint extraction."""
        code = 'class packet; rand bit [7:0] data; rand bit valid; constraint c_data { data > 0; } constraint c_valid { valid -> data > 10; } endclass'
        fname = write_temp_file(code)
        
        try:
            parser = SVParser()
            parser.parse_file(fname)
            
            extractor = ClassExtractor(parser)
            classes = extractor.extract()
            
            p = classes['packet']
            self.assertEqual(len(p.constraints), 2)
            
            c_valid = p.get_constraint_by_name('c_valid')
            self.assertIsNotNone(c_valid)
            self.assertEqual(c_valid.constraint_type, 'implication')
        finally:
            os.unlink(fname)

    def test_inheritance(self):
        """Test class inheritance extraction."""
        code = 'class base; rand bit [7:0] addr; endclass class extended extends base; rand bit [15:0] data; endclass'
        fname = write_temp_file(code)
        
        try:
            parser = SVParser()
            parser.parse_file(fname)
            
            extractor = ClassExtractor(parser)
            classes = extractor.extract()
            
            self.assertEqual(classes['extended'].extends, 'base')
            self.assertEqual(len(classes['base'].properties), 1)
            self.assertEqual(len(classes['extended'].properties), 1)
        finally:
            os.unlink(fname)

    def test_class_with_methods(self):
        """Test class method extraction."""
        code = 'class my_class; function void foo(); endfunction task bar(input int x); endtask endclass'
        fname = write_temp_file(code)
        
        try:
            parser = SVParser()
            parser.parse_file(fname)
            
            extractor = ClassExtractor(parser)
            classes = extractor.extract()
            
            m = classes['my_class']
            self.assertEqual(len(m.methods), 2)
            method_names = [method.name for method in m.methods]
            self.assertIn('foo', method_names)
            self.assertIn('bar', method_names)
        finally:
            os.unlink(fname)

    def test_virtual_pure_methods(self):
        """Test virtual and pure method extraction."""
        code = 'class base; virtual function void print(); endfunction pure virtual function int get_value(); endclass'
        fname = write_temp_file(code)
        
        try:
            parser = SVParser()
            parser.parse_file(fname)
            
            extractor = ClassExtractor(parser)
            classes = extractor.extract()
            
            m = classes['base']
            methods = {method.name: method for method in m.methods}
            
            self.assertTrue(methods['print'].is_virtual())
            self.assertFalse(methods['print'].is_pure())
            
            self.assertTrue(methods['get_value'].is_virtual())
            self.assertTrue(methods['get_value'].is_pure())
        finally:
            os.unlink(fname)

    def test_property_qualifiers(self):
        """Test property qualifier extraction."""
        code = 'class my_class; rand bit [7:0] data; local rand int local_val; protected rand bit [15:0] prot_addr; static rand int static_count; const int CONST_VAL = 42; endclass'
        fname = write_temp_file(code)
        
        try:
            parser = SVParser()
            parser.parse_file(fname)
            
            extractor = ClassExtractor(parser)
            classes = extractor.extract()
            
            props = {p.name: p for p in classes['my_class'].properties}
            
            self.assertEqual(props['data'].rand_mode, 'rand')
            self.assertIn('local', props['local_val'].qualifiers)
            self.assertIn('protected', props['prot_addr'].qualifiers)
            self.assertIn('static', props['static_count'].qualifiers)
            self.assertIn('const', props['CONST_VAL'].qualifiers)
        finally:
            os.unlink(fname)

    def test_array_dimensions(self):
        """Test array property extraction."""
        code = 'class my_class; rand bit [3:0] arr [4]; rand int queue_data [$]; rand bit [7:0] dyn_array []; rand int assoc_array [*]; endclass'
        fname = write_temp_file(code)
        
        try:
            parser = SVParser()
            parser.parse_file(fname)
            
            extractor = ClassExtractor(parser)
            classes = extractor.extract()
            
            props = {p.name: p for p in classes['my_class'].properties}
            
            self.assertIn('[4]', props['arr'].dimensions)
            self.assertTrue(props['queue_data'].is_queue())
            self.assertTrue(props['dyn_array'].is_dynamic_array())
            self.assertTrue(props['assoc_array'].is_assoc_array())
        finally:
            os.unlink(fname)

    def test_constraint_types(self):
        """Test constraint type classification."""
        code = 'class packet; rand bit [7:0] data; rand bit mode; constraint c_simple { data < 256; } constraint c_implication { mode -> data > 0; } constraint c_soft { soft data > 10; } constraint c_dist { data dist { [0:127] := 1, [128:255] := 3 }; } endclass'
        fname = write_temp_file(code)
        
        try:
            parser = SVParser()
            parser.parse_file(fname)
            
            extractor = ClassExtractor(parser)
            classes = extractor.extract()
            
            p = classes['packet']
            cons = {c.name: c for c in p.constraints}
            
            self.assertEqual(cons['c_simple'].constraint_type, 'simple')
            self.assertEqual(cons['c_implication'].constraint_type, 'implication')
            self.assertEqual(cons['c_soft'].constraint_type, 'soft')
            self.assertEqual(cons['c_soft'].is_soft, True)
            self.assertEqual(cons['c_dist'].constraint_type, 'dist')
            self.assertEqual(len(cons['c_dist'].dist_items), 2)
        finally:
            os.unlink(fname)


class TestClassHierarchy(unittest.TestCase):
    """Test ClassHierarchyBuilder functionality."""

    def test_simple_hierarchy(self):
        """Test simple class hierarchy."""
        code = 'class base; endclass class child extends base; endclass'
        fname = write_temp_file(code)
        
        try:
            parser = SVParser()
            parser.parse_file(fname)
            
            extractor = ClassExtractor(parser)
            hierarchy = ClassHierarchyBuilder(extractor)
            
            self.assertIn('base', hierarchy.get_root_classes())
            self.assertIn('child', hierarchy.get_leaf_classes())
            self.assertEqual(hierarchy.get_parent('child'), 'base')
            self.assertIn('child', hierarchy.get_children('base'))
        finally:
            os.unlink(fname)

    def test_multi_level_hierarchy(self):
        """Test multi-level class hierarchy."""
        code = 'class root; endclass class level1 extends root; endclass class level2 extends level1; endclass'
        fname = write_temp_file(code)
        
        try:
            parser = SVParser()
            parser.parse_file(fname)
            
            extractor = ClassExtractor(parser)
            hierarchy = ClassHierarchyBuilder(extractor)
            
            self.assertEqual(hierarchy.get_ancestors('level2'), ['level1', 'root'])
            self.assertTrue(hierarchy.is_descendant_of('level2', 'root'))
        finally:
            os.unlink(fname)

    def test_diamond_hierarchy(self):
        """Test diamond inheritance pattern."""
        code = 'class base; endclass class a extends base; endclass class b extends base; endclass class leaf extends a; endclass'
        fname = write_temp_file(code)
        
        try:
            parser = SVParser()
            parser.parse_file(fname)
            
            extractor = ClassExtractor(parser)
            hierarchy = ClassHierarchyBuilder(extractor)
            
            self.assertTrue(hierarchy.has_common_ancestor('leaf', 'b'))
            self.assertIn('base', hierarchy.get_common_ancestors('leaf', 'b'))
        finally:
            os.unlink(fname)


class TestClassInstantiation(unittest.TestCase):
    """Test ClassInstantiationTracer functionality."""

    def test_class_handles(self):
        """Test class handle declaration extraction."""
        code = 'class packet; rand bit [7:0] data; endclass module test; packet p1; packet p2 = new(); endmodule'
        fname = write_temp_file(code)
        
        try:
            parser = SVParser()
            parser.parse_file(fname)
            
            extractor = ClassExtractor(parser)
            tracer = ClassInstantiationTracer(parser, extractor)
            
            usage = tracer.get_module_usages('test')
            self.assertIsNotNone(usage)
            self.assertEqual(len(usage.instances), 2)
            
            instances = {inst.instance_name: inst for inst in usage.instances}
            self.assertEqual(instances['p1'].handle_type, 'handle')
            self.assertEqual(instances['p2'].handle_type, 'new')
        finally:
            os.unlink(fname)

    def test_method_calls(self):
        """Test method call extraction."""
        code = 'class packet; rand bit [7:0] data; function void print(); endfunction endclass module test; packet p = new(); initial begin void (p.randomize()); p.print(); end endmodule'
        fname = write_temp_file(code)
        
        try:
            parser = SVParser()
            parser.parse_file(fname)
            
            extractor = ClassExtractor(parser)
            tracer = ClassInstantiationTracer(parser, extractor)
            
            usage = tracer.get_module_usages('test')
            self.assertIsNotNone(usage)
            self.assertIn('p.randomize()', usage.method_calls)
            self.assertIn('p.print()', usage.method_calls)
        finally:
            os.unlink(fname)

    def test_inherited_class_instance(self):
        """Test instance of inherited class."""
        code = 'class base; endclass class extended extends base; endclass module test; base b = new(); extended e = new(); endmodule'
        fname = write_temp_file(code)
        
        try:
            parser = SVParser()
            parser.parse_file(fname)
            
            extractor = ClassExtractor(parser)
            tracer = ClassInstantiationTracer(parser, extractor)
            
            usage = tracer.get_module_usages('test')
            self.assertIsNotNone(usage)
            self.assertEqual(len(usage.instances), 2)
            
            instances = {inst.instance_name: inst for inst in usage.instances}
            self.assertEqual(instances['b'].class_name, 'base')
            self.assertEqual(instances['e'].class_name, 'extended')
        finally:
            os.unlink(fname)


if __name__ == '__main__':
    unittest.main()
