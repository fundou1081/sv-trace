#!/usr/bin/env python3
"""
sv-tests 完整测试集 - 830+ SV 文件
"""
import sys
import os

sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.driver import DriverTracer
from trace.load import LoadTracer


SV_TESTS_DIR = '/Users/fundou/my_dv_proj/sv-tests/tests'


def parse_sv_file(filepath):
    """解析单个 SV 文件"""
    parser = SVParser()
    try:
        parser.parse_file(filepath)
        return True, parser
    except Exception as e:
        return False, str(e)[:50]


def test_chapter(chapter_name):
    """测试单个章节"""
    chapter_dir = os.path.join(SV_TESTS_DIR, chapter_name)
    if not os.path.isdir(chapter_dir):
        return 0, 0, []
    
    sv_files = [f for f in os.listdir(chapter_dir) if f.endswith('.sv')]
    
    passed = 0
    failed = 0
    errors = []
    
    for sv_file in sv_files:
        filepath = os.path.join(chapter_dir, sv_file)
        ok, result = parse_sv_file(filepath)
        if ok:
            passed += 1
        else:
            failed += 1
            errors.append(f"{sv_file}: {result}")
    
    return passed, failed, errors


def main():
    print("=" * 60)
    print("sv-tests 完整测试集")
    print("=" * 60)
    
    # 获取所有章节
    chapters = sorted([d for d in os.listdir(SV_TESTS_DIR) 
                       if os.path.isdir(os.path.join(SV_TESTS_DIR, d)) 
                       and d.startswith('chapter-')])
    
    total_passed = 0
    total_failed = 0
    
    for chapter in chapters:
        passed, failed, errors = test_chapter(chapter)
        total_passed += passed
        total_failed += failed
        
        status = "✅" if failed == 0 else "❌"
        print(f"{status} {chapter}: {passed}/{passed+failed}")
        
        if errors and failed < 5:
            for e in errors[:3]:
                print(f"    {e}")
    
    print("=" * 60)
    print(f"总计: {total_passed} 通过, {total_failed} 失败")
    print("=" * 60)
    
    return total_failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
