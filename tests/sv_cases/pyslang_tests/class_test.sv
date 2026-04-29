// ============================================================================
// Class 测试用例 - 验证 pyslang AST 解析 Class 语法
// ============================================================================

// Test 1: 简单类
class simple_class;
    rand bit [7:0] data;
    constraint c_data { data > 0; }
endclass

// Test 2: 多成员类
class multi_member_class;
    rand bit [7:0] data;
    rand bit [3:0] addr;
    bit [1:0] flags;
    constraint c_data { data > 0; }
    constraint c_addr { addr < 16; }
endclass

// Test 3: 继承类
class base_class;
    rand bit [7:0] base_data;
endclass

class derived_class extends base_class;
    rand bit [3:0] derived_data;
endclass

// Test 4: Randc
class randc_class;
    randc bit [3:0] counter;
    constraint c_counter { counter inside {[0:15]}; }
endclass

// Test 5: 软约束
class soft_constraint_class;
    rand bit [7:0] value;
    constraint c_soft { soft value > 10; }
    constraint c_hard { value < 200; }
endclass

// Test 6: Foreach 约束
class foreach_class;
    rand int arr [4];
    constraint c_foreach { foreach (arr[i]) arr[i] > 0; }
endclass

// Test 7: Dist 约束
class dist_class;
    rand bit [7:0] data;
    constraint c_dist { data dist { 0 := 1, [1:3] := 2, [4:7] := 1 }; }
endclass

// Test 8: 条件约束
class conditional_class;
    rand bit [7:0] mode;
    rand bit [7:0] data;
    constraint c_mode { 
        if (mode == 0) 
            data < 128; 
        else if (mode == 1) 
            data >= 128; 
        else 
            data == 0; 
    }
endclass

// Test 9: Solve Before
class solve_before_class;
    rand bit [3:0] a;
    rand bit [7:0] b;
    constraint c_solve { solve a before b; }
    constraint c_range { b > a; }
endclass

// Test 10: 方法类
class method_class;
    rand bit [7:0] data;
    
    function new();
        data = 0;
    endfunction
    
    function bit [7:0] get_data();
        return data;
    endfunction
    
    task reset();
        data = 0;
    endtask
endclass
