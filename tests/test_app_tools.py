"""
测试Coverage激励建议器和Constraint检测器
使用OpenTitan项目
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from verify.coverage_guide.stimulus_suggester import (
    CoverageStimulusSuggester, 
    CoverageTarget, 
    CoverageType
)

from verify.constraint_check.constraint_analyzer import ConstraintAnalyzer

# OpenTitan路径
OPENTITAN_RTL = [
    "/Users/fundou/my_dv_proj/opentitan/hw/top_earlgrey/ip_autogen/rv_core_ibex/rtl/rv_core_ibex_peri.sv",
]

def test_coverage_suggester():
    """测试Coverage激励建议"""
    print("=" * 60)
    print("测试1: Coverage激励建议")
    print("=" * 60)
    
    suggester = CoverageStimulusSuggester()
    
    # 加载设计
    result = suggester.load_design(OPENTITAN_RTL)
    print(f"加载结果: {result}")
    
    if not result:
        print("❌ 加载失败")
        return
    
    # 分析一个Coverage目标
    target = CoverageTarget(
        coverage_type=CoverageType.BRANCH,
        file=OPENTITAN_RTL[0],
        line=30,  # 任意行
    )
    
    result = suggester.suggest_stimulus(target)
    print(result)

def test_constraint_analyzer():
    """测试Constraint分析"""
    print("\n" + "=" * 60)
    print("测试2: Constraint Corner Case检测")
    print("=" * 60)
    
    analyzer = ConstraintAnalyzer()
    
    # 测试约束
    test_constraint = """
    class test_data_constraint;
        rand bit[7:0] value;
        rand bit[7:0] count;
        
        constraint value_c {
            value inside {[10:50]};
        }
        
        constraint count_c {
            count inside {[20:60]};
            count < value;  // count < value可能冲突
        }
    endclass
    """
    
    issues = analyzer.analyze_constraint(test_constraint)
    print(f"发现问题: {len(issues)} 个")
    
    for issue in issues:
        print(f"  - {issue.issue_type.value}: {issue.description}")
    
    # 生成报告
    report = analyzer.generate_report(test_constraint)
    print("\n" + report)

if __name__ == "__main__":
    test_coverage_suggester()
    test_constraint_analyzer()
