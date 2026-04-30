#!/usr/bin/env python3
"""
Test runner for sv-trace project
Runs all unit tests and parse module tests
"""
import sys
import os
import unittest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def run_tests():
    """Run all tests"""
    print("=" * 60)
    print("sv-trace Test Runner")
    print("=" * 60)
    print()
    
    # Discover and run unit tests
    loader = unittest.TestLoader()
    start_dir = 'tests/unit'
    
    if os.path.exists(start_dir):
        suite = loader.discover(start_dir, pattern='test_*.py')
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Print summary
        print()
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        
        if result.wasSuccessful():
            print("\n✅ ALL TESTS PASSED")
            return 0
        else:
            print("\n❌ SOME TESTS FAILED")
            return 1
    else:
        print(f"Tests directory '{start_dir}' not found")
        return 1


def test_parse_module():
    """Test parse module directly"""
    print()
    print("=" * 60)
    print("Testing Parse Module")
    print("=" * 60)
    print()
    
    # Test imports
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Core parsers
    try:
        from parse import SVParser, ModuleExtractor
        print("✅ Core parsers import OK")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Core parsers: {e}")
        tests_failed += 1
    
    # Test 2: SV Syntax parsers
    try:
        from parse import (
            InterfaceExtractor,
            PackageExtractor,
            GenerateExtractor,
        )
        print("✅ SV Syntax parsers import OK")
        tests_passed += 1
    except Exception as e:
        print(f"❌ SV Syntax parsers: {e}")
        tests_failed += 1
    
    # Test 3: Verification parsers
    try:
        from parse import (
            VerificationSyntaxExtractor,
            AdvancedVerificationExtractor,
        )
        print("✅ Verification parsers import OK")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Verification parsers: {e}")
        tests_failed += 1
    
    # Test 4: Other parsers
    try:
        from parse import (
            ClassExtractor,
            ConstraintExtractor,
            CovergroupExtractor,
            AssertionExtractor,
        )
        print("✅ Other parsers import OK")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Other parsers: {e}")
        tests_failed += 1
    
    # Test 5: Run actual parsing
    try:
        import pyslang
        from parse.interface import InterfaceExtractor
        
        code = '''interface i; modport m(input a); endinterface'''
        ext = InterfaceExtractor(None)
        ext._extract_from_tree(pyslang.SyntaxTree.fromText(code).root)
        
        if 'i' in ext.interfaces:
            print("✅ InterfaceExtractor functional test OK")
            tests_passed += 1
        else:
            print("⚠️ InterfaceExtractor: no interfaces found")
            tests_failed += 1
    except Exception as e:
        print(f"❌ Functional test: {e}")
        tests_failed += 1
    
    print()
    print(f"Parse module tests: {tests_passed} passed, {tests_failed} failed")
    
    return 0 if tests_failed == 0 else 1


if __name__ == '__main__':
    # Run parse module tests first (faster)
    exit_code = test_parse_module()
    
    # Then run full test suite
    exit_code = max(exit_code, run_tests())
    
    sys.exit(exit_code)
