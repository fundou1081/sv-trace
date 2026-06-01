#!/usr/bin/env python3
"""SV-Trace 技能发现CLI"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills import SKILLS, TIER_INFO, STATUS_INFO, list_skills, get_skill_tree


def main():
    args = sys.argv[1:]
    
    print("=" * 60)
    print("SV-Trace Skills Registry")
    print("=" * 60)
    
    # 显示树形结构
    tree = get_skill_tree()
    
    tier_stats = {1:0, 2:0, 3:0, 4:0}
    status_stats = {"verified": 0, "experimental": 0, "needs_fix": 0}
    
    for module, skills in sorted(tree.items()):
        print(f"\n[{module}]")
        for s in sorted(skills, key=lambda x: x["id"]):
            tier = s.get("tier", 0)
            status = s.get("test_status", "unknown")
            tier_stats[tier] = tier_stats.get(tier, 0) + 1
            status_stats[status] = status_stats.get(status, 0) + 1
            
            tier_c = TIER_INFO.get(tier, {"color": "?"})["color"]
            status_c = STATUS_INFO.get(status, {"color": "?"})["color"]
            
            print(f"  [{tier_c}{tier}] {s['id']:20s} {status_c} {status}")
    
    print("\n" + "=" * 60)
    print("Tier: G=核心 Y=重要 O=辅助 R=探索")
    print("Status: V=已验证 E=实验性 X=需修复")
    print("=" * 60)
    print(f"\nTotal: {len(SKILLS)} skills")
    print(f"  Tier1: {tier_stats.get(1,0)} | Tier2: {tier_stats.get(2,0)} | Tier3: {tier_stats.get(3,0)} | Tier4: {tier_stats.get(4,0)}")
    print(f"  Verified: {status_stats.get('verified',0)} | Experimental: {status_stats.get('experimental',0)} | Needs Fix: {status_stats.get('needs_fix',0)}")


if __name__ == "__main__":
    main()
