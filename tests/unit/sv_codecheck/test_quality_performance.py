import sys
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

"""
Quality & Performance Tools Test Suite
"""

import sys
import os
import tempfile
sys.path.insert(0, 'src')

from parse import SVParser
from debug.analyzers.multi_driver_detector import MultiDriverDetector
from debug.analyzers.code_quality_scorer import CodeQualityScorer
from trace.performance_estimator import PerformanceEstimator


def test_multi_driver_detector():
    code = '''module test;
        logic clk_a, clk_b;
        logic [7:0] data;
        always_ff @(posedge clk_a) data <= 8'hAA;
        always_ff @(posedge clk_b) data <= 8'hBB;
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code)
        tmp = f.name
    
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        detector = MultiDriverDetector(parser)
        report = detector.analyze()
        assert report.statistics['multi_driver_signals'] > 0
        print("✅ MultiDriverDetector test passed")
    finally:
        os.unlink(tmp)


def test_code_quality_scorer():
    code = '''module test;
        logic clk;
        logic [7:0] data;
        always_ff @(posedge clk) data <= 8'hAA;
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code)
        tmp = f.name
    
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        scorer = CodeQualityScorer(parser)
        score, issues = scorer.analyze()
        assert score.total > 0
        print("✅ CodeQualityScorer test passed")
        print(f"   Score: {score.total:.1f}/100")
    finally:
        os.unlink(tmp)


def test_performance_estimator():
    code = '''module test;
        logic clk;
        logic [7:0] data;
        always_ff @(posedge clk) data <= 8'hAA;
    endmodule'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code)
        tmp = f.name
    
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        perf = PerformanceEstimator(parser)
        est = perf.analyze()
        assert est.max_frequency_mhz > 0
        print("✅ PerformanceEstimator test passed")
        print(f"   Max freq: {est.max_frequency_mhz:.1f} MHz")
    finally:
        os.unlink(tmp)


if __name__ == '__main__':
    test_multi_driver_detector()
    test_code_quality_scorer()
    test_performance_estimator()
    print("\nAll tests passed!")
