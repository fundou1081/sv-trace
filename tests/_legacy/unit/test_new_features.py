"""
新功能综合测试 - 测试所有新增功能
使用真实开源项目验证
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parse import SVParser
from debug.analyzers.fsm_analyzer import FSMAnalyzer, SVAGenerator, VerificationPlanGenerator
from debug.analyzers.cdc import CDCAnalyzer, CDCExtendedAnalyzer
from debug.analyzers.reset_domain_analyzer import ResetDomainAnalyzer, ResetIntegrityChecker
from debug.analyzers.timed_path_analyzer import TimedPathAnalyzer
from debug.analyzers.condition_coverage import ConditionCoverageAnalyzer
from trace.dependency import FanoutAnalyzer, FaninAnalyzer


# 真实项目路径
TEST_PROJECTS = {
    "tiny-gpu": "/Users/fundou/my_dv_proj/tiny-gpu/src",
    "basic-verilog": "/Users/fundou/my_dv_proj/basic_verilog",
    "neorv32": "/Users/fundou/my_dv_proj/neorv32/rtl",
    "picorv32": "/Users/fundou/my_dv_proj/picorv32",
    "serv": "/Users/fundou/my_dv_proj/serv/rtl",
}


def find_sv_files(directory, limit=50):
    """查找SV文件"""
    files = []
    for root, dirs, filenames in os.walk(directory):
        for f in filenames:
            if f.endswith('.sv') or f.endswith('.v'):
                files.append(os.path.join(root, f))
                if len(files) >= limit:
                    return files
    return files


def test_fsm_analyzer():
    """测试FSM分析器"""
    print("\n" + "="*60)
    print("FSM Analyzer 测试")
    print("="*60)
    
    results = {"passed": 0, "failed": 0, "errors": []}
    
    for proj_name, proj_path in TEST_PROJECTS.items():
        if not os.path.exists(proj_path):
            continue
            
        print(f"\n--- {proj_name} ---")
        sv_files = find_sv_files(proj_path, limit=10)
        
        for f in sv_files[:3]:
            try:
                parser = SVParser()
                parser.parse_file(f)
                
                analyzer = FSMAnalyzer(parser)
                report = analyzer.analyze()
                
                print(f"  ✓ {os.path.basename(f)}: {len(report.state_names)} states")
                results["passed"] += 1
                
            except Exception as e:
                print(f"  ✗ {os.path.basename(f)}: {e}")
                results["failed"] += 1
                results["errors"].append({
                    "test": "FSMAnalyzer",
                    "file": f,
                    "error": str(e)
                })
    
    return results


def test_cdc_extended():
    """测试CDC扩展分析"""
    print("\n" + "="*60)
    print("CDC Extended Analyzer 测试")
    print("="*60)
    
    results = {"passed": 0, "failed": 0, "errors": []}
    
    for proj_name, proj_path in TEST_PROJECTS.items():
        if not os.path.exists(proj_path):
            continue
            
        print(f"\n--- {proj_name} ---")
        sv_files = find_sv_files(proj_path, limit=10)
        
        for f in sv_files[:3]:
            try:
                parser = SVParser()
                parser.parse_file(f)
                
                analyzer = CDCExtendedAnalyzer(parser)
                report = analyzer.analyze()
                
                print(f"  ✓ {os.path.basename(f)}: {len(report.clock_domains)} domains, {len(report.cdc_paths)} CDC paths")
                results["passed"] += 1
                
            except Exception as e:
                print(f"  ✗ {os.path.basename(f)}: {e}")
                results["failed"] += 1
                results["errors"].append({
                    "test": "CDCExtendedAnalyzer",
                    "file": f,
                    "error": str(e)
                })
    
    return results


def test_reset_integrity():
    """测试复位完整性检查"""
    print("\n" + "="*60)
    print("Reset Integrity Checker 测试")
    print("="*60)
    
    results = {"passed": 0, "failed": 0, "errors": []}
    
    for proj_name, proj_path in TEST_PROJECTS.items():
        if not os.path.exists(proj_path):
            continue
            
        print(f"\n--- {proj_name} ---")
        sv_files = find_sv_files(proj_path, limit=10)
        
        for f in sv_files[:3]:
            try:
                parser = SVParser()
                parser.parse_file(f)
                
                checker = ResetIntegrityChecker(parser)
                report = checker.check()
                
                print(f"  ✓ {os.path.basename(f)}: {len(report.reset_tree)} resets, coverage={report.coverage:.1f}%")
                results["passed"] += 1
                
            except Exception as e:
                print(f"  ✗ {os.path.basename(f)}: {e}")
                results["failed"] += 1
                results["errors"].append({
                    "test": "ResetIntegrityChecker",
                    "file": f,
                    "error": str(e)
                })
    
    return results


def test_fanout_analyzer():
    """测试Fanout分析"""
    print("\n" + "="*60)
    print("Fanout Analyzer 测试")
    print("="*60)
    
    results = {"passed": 0, "failed": 0, "errors": []}
    
    for proj_name, proj_path in TEST_PROJECTS.items():
        if not os.path.exists(proj_path):
            continue
            
        print(f"\n--- {proj_name} ---")
        sv_files = find_sv_files(proj_path, limit=10)
        
        for f in sv_files[:3]:
            try:
                parser = SVParser()
                parser.parse_file(f)
                
                analyzer = FanoutAnalyzer(parser)
                high_fanout = analyzer.find_high_fanout_signals(threshold=2)
                
                print(f"  ✓ {os.path.basename(f)}: {len(high_fanout)} high-fanout signals")
                results["passed"] += 1
                
            except Exception as e:
                print(f"  ✗ {os.path.basename(f)}: {e}")
                results["failed"] += 1
                results["errors"].append({
                    "test": "FanoutAnalyzer",
                    "file": f,
                    "error": str(e)
                })
    
    return results


def test_condition_coverage():
    """测试条件覆盖分析"""
    print("\n" + "="*60)
    print("Condition Coverage Analyzer 测试")
    print("="*60)
    
    results = {"passed": 0, "failed": 0, "errors": []}
    
    for proj_name, proj_path in TEST_PROJECTS.items():
        if not os.path.exists(proj_path):
            continue
            
        print(f"\n--- {proj_name} ---")
        sv_files = find_sv_files(proj_path, limit=10)
        
        for f in sv_files[:3]:
            try:
                parser = SVParser()
                parser.parse_file(f)
                
                analyzer = ConditionCoverageAnalyzer(parser)
                report = analyzer.analyze()
                
                print(f"  ✓ {os.path.basename(f)}: {report.total_if_count} ifs, {report.total_conditions} conditions")
                results["passed"] += 1
                
            except Exception as e:
                print(f"  ✗ {os.path.basename(f)}: {e}")
                results["failed"] += 1
                results["errors"].append({
                    "test": "ConditionCoverageAnalyzer",
                    "file": f,
                    "error": str(e)
                })
    
    return results


def test_timed_path():
    """测试Timed Path分析"""
    print("\n" + "="*60)
    print("Timed Path Analyzer 测试")
    print("="*60)
    
    results = {"passed": 0, "failed": 0, "errors": []}
    
    for proj_name, proj_path in TEST_PROJECTS.items():
        if not os.path.exists(proj_path):
            continue
            
        print(f"\n--- {proj_name} ---")
        sv_files = find_sv_files(proj_path, limit=10)
        
        for f in sv_files[:3]:
            try:
                parser = SVParser()
                parser.parse_file(f)
                
                analyzer = TimedPathAnalyzer(parser)
                report = analyzer.analyze()
                
                print(f"  ✓ {os.path.basename(f)}: {len(report.paths)} paths")
                results["passed"] += 1
                
            except Exception as e:
                print(f"  ✗ {os.path.basename(f)}: {e}")
                results["failed"] += 1
                results["errors"].append({
                    "test": "TimedPathAnalyzer",
                    "file": f,
                    "error": str(e)
                })
    
    return results


def test_sva_generator():
    """测试SVA生成器"""
    print("\n" + "="*60)
    print("SVA Generator 测试")
    print("="*60)
    
    results = {"passed": 0, "failed": 0, "errors": []}
    
    for proj_name, proj_path in TEST_PROJECTS.items():
        if not os.path.exists(proj_path):
            continue
            
        print(f"\n--- {proj_name} ---")
        sv_files = find_sv_files(proj_path, limit=10)
        
        for f in sv_files[:2]:
            try:
                parser = SVParser()
                parser.parse_file(f)
                
                generator = SVAGenerator(parser)
                report = generator.generate()
                
                print(f"  ✓ {os.path.basename(f)}: {len(report.properties)} properties, {len(report.sequences)} sequences")
                results["passed"] += 1
                
            except Exception as e:
                print(f"  ✗ {os.path.basename(f)}: {e}")
                results["failed"] += 1
                results["errors"].append({
                    "test": "SVAGenerator",
                    "file": f,
                    "error": str(e)
                })
    
    return results


def test_verification_plan():
    """测试验证计划生成器"""
    print("\n" + "="*60)
    print("Verification Plan Generator 测试")
    print("="*60)
    
    results = {"passed": 0, "failed": 0, "errors": []}
    
    for proj_name, proj_path in TEST_PROJECTS.items():
        if not os.path.exists(proj_path):
            continue
            
        print(f"\n--- {proj_name} ---")
        sv_files = find_sv_files(proj_path, limit=10)
        
        for f in sv_files[:2]:
            try:
                parser = SVParser()
                parser.parse_file(f)
                
                generator = VerificationPlanGenerator(parser)
                plan = generator.generate()
                
                print(f"  ✓ {os.path.basename(f)}: {plan.total_tests} testpoints")
                results["passed"] += 1
                
            except Exception as e:
                print(f"  ✗ {os.path.basename(f)}: {e}")
                results["failed"] += 1
                results["errors"].append({
                    "test": "VerificationPlanGenerator",
                    "file": f,
                    "error": str(e)
                })
    
    return results


def run_all_tests():
    """运行所有测试"""
    print("="*60)
    print("新功能综合测试")
    print("="*60)
    
    all_results = {}
    
    # 运行各项测试
    all_results["FSM Analyzer"] = test_fsm_analyzer()
    all_results["CDC Extended"] = test_cdc_extended()
    all_results["Reset Integrity"] = test_reset_integrity()
    all_results["Fanout Analyzer"] = test_fanout_analyzer()
    all_results["Condition Coverage"] = test_condition_coverage()
    all_results["Timed Path"] = test_timed_path()
    all_results["SVA Generator"] = test_sva_generator()
    all_results["Verification Plan"] = test_verification_plan()
    
    # 汇总
    print("\n" + "="*60)
    print("测试汇总")
    print("="*60)
    
    total_passed = 0
    total_failed = 0
    all_errors = []
    
    for name, result in all_results.items():
        total_passed += result["passed"]
        total_failed += result["failed"]
        all_errors.extend(result["errors"])
        
        status = "✓ PASS" if result["failed"] == 0 else "✗ FAIL"
        print(f"{name}: {result['passed']}/{result['passed']+result['failed']} {status}")
    
    print(f"\n总计: {total_passed}/{total_passed+total_failed}")
    
    # 错误详情
    if all_errors:
        print("\n" + "="*60)
        print("错误详情")
        print("="*60)
        
        for i, err in enumerate(all_errors, 1):
            print(f"\n[{i}] {err['test']}")
            print(f"  文件: {err['file']}")
            print(f"  错误: {err['error'][:200]}")
    
    return all_results, all_errors


if __name__ == "__main__":
    results, errors = run_all_tests()
    
    # 保存结果
    import json
    report_file = os.path.join(os.path.dirname(__file__), "test_results.json")
    with open(report_file, 'w') as f:
        json.dump({
            "results": {k: {"passed": v["passed"], "failed": v["failed"]} 
                       for k, v in results.items()},
            "errors": errors
        }, f, indent=2)
    print(f"\n结果已保存到: {report_file}")
