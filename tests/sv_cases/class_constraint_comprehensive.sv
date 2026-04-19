// Comprehensive constraint test cases for sv-trace class extraction
// Tests various constraint types and combinations

// Test 1: Basic simple constraints
class simple_constraints;
    rand bit [7:0] data;
    rand bit [7:0] addr;
    
    constraint c_data_range { data > 0; data < 256; }
    constraint c_addr_range { addr >= 0; addr <= 255; }
    constraint c_data_addr { data != addr; }
endclass

// Test 2: Implication constraints
class implication_constraints;
    rand bit valid;
    rand bit [7:0] data;
    
    constraint c_valid_implies { valid -> data > 0; }
    constraint c_invalid_implies { !valid -> data == 0; }
endclass

// Test 3: Soft constraints
class soft_constraints;
    rand bit [7:0] value;
    
    constraint c_soft_range { soft value > 10; }
    constraint c_soft_value { soft value < 100; }
endclass

// Test 4: Distribution constraints
class dist_constraints;
    rand bit [7:0] data;
    
    constraint c_dist_basic { data dist { 0 := 1, [1:3] := 2, [4:7] := 1 }; }
endclass

class dist_weighted;
    rand int x;
    
    constraint c_dist_weighted { x dist { [0:100] :/ 5, [101:200] := 10, [201:255] :/ 1 }; }
endclass

// Test 5: Conditional if-else constraints
class conditional_constraints;
    rand bit [7:0] mode;
    rand bit [7:0] data;
    
    constraint c_mode_data { 
        if (mode == 0) 
            data < 128; 
        else if (mode == 1) 
            data >= 128; 
        else 
            data == 0; 
    }
endclass

// Test 6: Foreach constraints
class foreach_constraints;
    rand int arr [4];
    
    constraint c_foreach_arr { foreach (arr[i]) arr[i] > 0; }
    constraint c_foreach_sum { foreach (arr[i]) arr[i] < 100; }
endclass

class foreach_2d;
    rand int matrix [2][3];
    
    constraint c_foreach_2d { foreach (matrix[i,j]) matrix[i][j] >= 0; }
endclass

// Test 7: Solve before constraints
class solve_before_constraints;
    rand bit [3:0] a;
    rand bit [7:0] b;
    
    constraint c_solve { solve a before b; }
    constraint c_range { b > a; }
endclass

// Test 8: Inline constraints
class inline_constraints;
    rand bit [7:0] x;
    rand bit [7:0] y;
endclass

// Test 9: Complex constraint expressions
class complex_constraints;
    rand bit [7:0] a;
    rand bit [7:0] b;
    rand bit [7:0] c;
    
    constraint c_complex_or { (a > 10) || (b > 10) || (c > 10); }
    constraint c_complex_and { (a > 5) && (a < 20); }
    constraint c_complex_mixed { (a + b) == c; }
endclass

// Test 10: Default constraints
class default_constraints;
    rand bit [7:0] data;
    
    constraint c_default { data == 8'hFF; }
endclass

// Test 11: Constraint with external function calls
class constraint_with_func;
    rand bit [7:0] value;
    
    constraint c_func { value > 5 && value < 50; }
    
    function bit is_valid(bit [7:0] v);
        return v > 0;
    endfunction
endclass

// Test 12: Multiple constraints on same variable
class multi_constraint;
    rand bit [7:0] data;
    
    constraint c1 { data > 0; }
    constraint c2 { data < 256; }
    constraint c3 { data != 128; }
endclass

// Test 13: Constraint inheritance
class base_constraint_class;
    rand bit [7:0] base_data;
    
    constraint c_base { base_data > 10; }
endclass

class derived_constraint_class extends base_constraint_class;
    rand bit [7:0] derived_data;
    
    constraint c_derived { derived_data > base_data; }
endclass

// Test 14: randc variable
class randc_constraints;
    randc bit [2:0] cycle;
    
    constraint c_cycle { cycle < 8; }
endclass

// Test 15: Constraint with array randomize
class array_constraint;
    rand int data[];
    rand int len;
    
    constraint c_size { len inside { [1:10] }; }
    constraint c_array { data.size() == len; foreach (data[i]) data[i] > 0; }
endclass

// Test 16: Constraint mode control
class constraint_mode_ctrl;
    rand bit [7:0] data;
    
    constraint c_on { data > 0; }
    constraint c_off { data < 256; }
    
    function void disable_c_off();
        c_off.constraint_mode(0);
    endfunction
    
    function void enable_c_off();
        c_off.constraint_mode(1);
    endfunction
endclass

// Test 17: Static constraint
class static_constraint_class;
    static rand bit [7:0] static_data;
    
    constraint c_static { static_data > 5; }
endclass

// Test 18: Pure virtual class with constraints
virtual class virtual_constraint_class;
    pure virtual function void randomize_props();
endclass

// Test 19: Post-randomize function
class post_randomize_class;
    rand bit [7:0] data;
    
    function void post_randomize();
        $display("Randomized data: %h", data);
    endfunction
endclass

// Test 20: Pre-randomize function  
class pre_randomize_class;
    rand bit [7:0] data;
    
    function void pre_randomize();
        $display("About to randomize");
    endfunction
endclass
