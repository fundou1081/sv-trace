"""Schema 验证器 - 验证工具输出是否符合 Schema 规范"""
from typing import Dict, List, Any, Tuple


class SchemaValidator:
    """验证 Schema 输出"""
    
    REQUIRED_FIELDS = ['schema_version', 'modules', 'classes', 'fsm', 'coverage', 'constraints', 'parameters']
    MODULE_FIELDS = ['module', 'ports']
    PORT_FIELDS = ['name', 'direction', 'width']
    COVERAGE_FIELDS = ['points', 'covergroup']
    FSM_FIELDS = ['module', 'states', 'state_var', 'reset_state', 'transitions']
    CONSTRAINT_FIELDS = ['name', 'class', 'expr']
    PARAM_FIELDS = ['name', 'value']
    
    def validate(self, schema: Dict) -> Tuple[bool, List[str]]:
        """验证 schema，返回 (是否通过, 错误列表)"""
        errors = []
        
        # 1. 检查顶层字段
        for field in self.REQUIRED_FIELDS:
            if field not in schema:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return False, errors
        
        # 2. 验证 modules
        for i, mod in enumerate(schema.get('modules', [])):
            for field in self.MODULE_FIELDS:
                if field not in mod:
                    errors.append(f"modules[{i}]: missing '{field}'")
        
        # 3. 验证 ports
        for i, mod in enumerate(schema.get('modules', [])):
            for j, port in enumerate(mod.get('ports', [])):
                for field in self.PORT_FIELDS:
                    if field not in port:
                        errors.append(f"modules[{i}].ports[{j}]: missing '{field}'")
        
        # 4. 验证 coverage
        cov = schema.get('coverage', {})
        for field in self.COVERAGE_FIELDS:
            if field not in cov:
                errors.append(f"coverage: missing '{field}'")
        
        # 5. 验证 fsm items
        for i, fsm in enumerate(schema.get('fsm', [])):
            for field in self.FSM_FIELDS:
                if field not in fsm:
                    errors.append(f"fsm[{i}]: missing '{field}'")
        
        # 6. 验证 constraints
        for i, c in enumerate(schema.get('constraints', [])):
            for field in self.CONSTRAINT_FIELDS:
                if field not in c:
                    errors.append(f"constraints[{i}]: missing '{field}'")
        
        # 7. 验证 parameters
        for i, p in enumerate(schema.get('parameters', [])):
            for field in self.PARAM_FIELDS:
                if field not in p:
                    errors.append(f"parameters[{i}]: missing '{field}'")
        
        return len(errors) == 0, errors
    
    def validate_and_print(self, schema: Dict) -> bool:
        """验证并打印结果"""
        valid, errors = self.validate(schema)
        if valid:
            print("✅ Schema 验证通过!")
        else:
            print("❌ Schema 验证失败:")
            for e in errors:
                print(f"  - {e}")
        return valid


def validate_schema(schema: Dict) -> bool:
    """便捷函数"""
    validator = SchemaValidator()
    return validator.validate_and_print(schema.data if hasattr(schema, 'data') else schema)
