// Complex constraint test cases for sv-trace class extraction
// Tests advanced constraint patterns and edge cases

// Test 1: Multi-variable implication
class multi_var_implication;
    rand bit valid;
    rand bit enable;
    rand bit [7:0] data;
    
    constraint c_multi_imply { valid && enable -> data > 0; }
endclass

// Test 2: Nested implication (if inside if)
class nested_implication;
    rand bit [1:0] mode;
    rand bit [7:0] data;
    
    constraint c_nested { if (mode == 0) if (data > 10) data < 100; }
endclass

// Test 3: Implication with dist
class imply_with_dist;
    rand bit valid;
    rand bit [7:0] data;
    
    constraint c_imply_dist { valid -> data dist { [0:127] := 1, [128:255] := 3 }; }
endclass

// Test 4: Multiple else-if chains
class multi_elseif;
    rand bit [2:0] sel;
    rand bit [7:0] out;
    
    constraint c_sel {
        if (sel == 0) out = 8'h00;
        else if (sel == 1) out = 8'h11;
        else if (sel == 2) out = 8'h22;
        else if (sel == 3) out = 8'h33;
        else out = 8'hFF;
    }
endclass

// Test 5: Foreach with complex expressions
class foreach_complex;
    rand int arr [3];
    
    constraint c_foreach_sum {
        foreach (arr[i]) arr[i] >= 0;
        foreach (arr[i]) arr[i] <= 255;
        arr[0] + arr[1] + arr[2] < 256;
    }
endclass

// Test 6: Foreach with conditional inside
class foreach_with_if;
    rand int arr [4];
    
    constraint c_cond_foreach {
        foreach (arr[i]) if (arr[i] > 10) arr[i] < 100;
    }
endclass

// Test 7: Soft and hard constraint mix
class soft_hard_mix;
    rand bit [7:0] value;
    
    constraint c_soft { soft value > 10; }
    constraint c_soft2 { soft value < 200; }
    constraint c_hard { value != 128; }
endclass

// Test 8: Soft constraint override
class soft_override;
    rand bit [7:0] data;
    
    constraint c_soft_data { soft data > 5; }
    constraint c_hard_range { data inside { [1:10], [50:60] }; }
endclass

// Test 9: Dist with weights and ranges
class dist_complex;
    rand int x;
    
    constraint c_dist {
        x dist {
            0       := 1,
            [1:10]  :/ 5,
            11      := 2,
            [12:20]  :/ 3,
            [21:99]  := 0,
            100     := 10
        };
    }
endclass

// Test 10: Dist with solve before
class dist_with_solve;
    rand bit [2:0] a;
    rand bit [7:0] b;
    
    constraint c_order { solve a before b; }
    constraint c_dist_ab { a dist { [0:3] := 1, [4:7] := 2 }; }
    constraint c_range { b inside { [0:255] }; }
endclass

// Test 11: Inside constraint
class inside_constraint;
    rand bit [7:0] data;
    rand bit [7:0] addr;
    
    constraint c_inside { data inside { [0:10], [20:30], [40:50] }; }
    constraint c_not_inside { addr !inside { [10:20], [30:40] }; }
endclass

// Test 12: Inside with array
class inside_with_array;
    rand bit [7:0] data;
    int valid_vals [] = '{1, 3, 5, 7, 9};
    
    constraint c_inside_array { data inside { valid_vals }; }
endclass

// Test 13: Unique constraint
class unique_constraint;
    rand byte array [4];
    
    constraint c_unique { unique { array }; }
endclass

// Test 14: If-else with implication
class if_else_imply;
    rand bit mode;
    rand bit [7:0] a;
    rand bit [7:0] b;
    
    constraint c_mixed {
        if (mode == 0)
            a -> b > 0;
        else
            b -> a > 0;
    }
endclass

// Test 15: Post-randomize with constraints
class post_rand_with_constraint;
    rand bit [7:0] data;
    
    constraint c_data { data > 0; }
    
    function void post_randomize();
        $display("Post randomize: data=%0d", data);
        data = data + 1;
    endfunction
endclass

// Test 16: Constraint with function call
class constraint_func_call;
    rand bit [7:0] value;
    
    constraint c_func { value > my_func(); }
    
    function bit [7:0] my_func();
        return 10;
    endfunction
endclass

// Test 17: Constraint inheritance with override
class base_constraint;
    rand bit [7:0] data;
    
    constraint c_base { data > 0; }
endclass

class derived_constraint extends base_constraint;
    constraint c_base { data > 10; }  // Override
endclass

// Test 18: Static class with constraints
class static_class_constraint;
    static rand bit [15:0] static_counter;
    
    constraint c_static_count { static_counter < 1000; }
endclass

// Test 19: Abstract class with pure virtual and constraints
virtual class abstract_constraint_class;
    pure virtual function void randomize_data();
    
    rand bit [7:0] common_data;
    constraint c_common { common_data > 0; }
endclass

// Test 20: Deep inheritance chain
class level0_constraint;
    rand bit [7:0] base_val;
    constraint c_l0 { base_val > 0; }
endclass

class level1_constraint extends level0_constraint;
    rand bit [7:0] mid_val;
    constraint c_l1 { mid_val > base_val; }
endclass

class level2_constraint extends level1_constraint;
    rand bit [7:0] top_val;
    constraint c_l2 { top_val > mid_val; }
endclass

// Test 21: Dynamic array constraint
class dyn_array_constraint;
    rand int data[];
    
    constraint c_size { data.size() inside { [1:10] }; }
    constraint c_elem { foreach (data[i]) data[i] inside { [0:255] }; }
    constraint c_sum { data.sum() with (int'(item)) < 1000; }
endclass

// Test 22: Queue constraint
class queue_constraint;
    rand int q [$];
    
    constraint c_queue {
        q.size() inside { [1:5] };
        foreach (q[i]) q[i] > 0;
        q[0] < q[1];
    }
endclass

// Test 23: Associative array constraint
class assoc_constraint;
    rand int assoc_arr [*];
    
    constraint c_assoc { assoc_arr.size() inside { [1:5] }; }
endclass

// Test 24: Constraint mode method
class constraint_mode_method;
    rand bit [7:0] a;
    rand bit [7:0] b;
    
    constraint c_a { a > 10; }
    constraint c_b { b > 20; }
    
    function void disable_all();
        c_a.constraint_mode(0);
        c_b.constraint_mode(0);
    endfunction
    
    function void enable_all();
        c_a.constraint_mode(1);
        c_b.constraint_mode(1);
    endfunction
endclass

// Test 25: Randomize with constraint
class rand_with_constraint;
    rand bit [7:0] x;
    rand bit [7:0] y;
    
    constraint c_xy { x + y < 256; }
    
    function void post_randomize();
        $display("x=%d, y=%d", x, y);
    endfunction
endclass

// Test 26: randc with constraint
class randc_complex;
    randc bit [2:0] val;
    
    constraint c_val { val != 3; }  // Exclude value 3
endclass

// Test 27: Bit selection constraint
class bit_select_constraint;
    rand bit [15:0] data;
    
    constraint c_bits {
        data[0] == 1'b1;
        data[1:0] == 2'b11;
        data[15:8] > 0;
    }
endclass

// Test 28: Constraint with casting
class cast_constraint;
    rand int signed_val;
    rand int unsigned_val;
    
    constraint c_cast {
        signed_val inside { [-100:100] };
        unsigned_val == unsigned'(signed_val);
    }
endclass

// Test 29: Multiple implications
class multi_imply_chain;
    rand bit a;
    rand bit b;
    rand bit c;
    rand bit [7:0] val;
    
    constraint c_chain { a && b && c -> val > 100; }
endclass

// Test 30: Conditional with dist
class conditional_dist;
    rand bit mode;
    rand bit [7:0] data;
    
    constraint c_mode_dist {
        if (mode == 0)
            data dist { [0:127] := 1, [128:255] := 1 };
        else
            data dist { [0:127] := 3, [128:255] := 1 };
    }
endclass
