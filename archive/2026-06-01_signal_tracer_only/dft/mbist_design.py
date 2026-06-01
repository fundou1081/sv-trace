"""
MBISTDesign - MBIST设计指导
MBIST插入指导
"""
from typing import List

class MBISTDesignGuide:
    """MBIST设计指导"""
    
    def suggest_mbist(self, memory_list: List[str]) -> str:
        """建议MBIST配置"""
        guide = """# MBIST设计指导

## 内存列表
"""
        for mem in memory_list:
            guide += f"- {mem}\n"
        
        guide += """
## MBIST建议

### RAM
- 建议使用BIST控制器
- 覆盖所有地址
- 测试所有故障模型

### ROM
- 功能测试即可
- 边界扫描

## 插入位置
-靠近内存
- 通过MBIST控制器访问

## 使能控制
- 功能模式: BIST bypass
- 测试模式: BIST enable
"""
        return guide
    
    def generate_checklist(self) -> str:
        return """# MBIST检查清单

- [ ] 所有RAM有MBIST
- [ ] MBIST能检测所有故障
- [ ] BIST覆盖率>95%
- [ ] 使能控制正确
"""
