// ============================================================================
// ModuleDependencyAnalyzer 测试用例 - 20个依赖组合
// ============================================================================

// 1. 单模块无依赖
module dep_01_single;
endmodule

// 2. 两个模块依赖
module dep_02_two_level;
endmodule
module dep_02_top;
    dep_02_two_level u_sub();
endmodule

// 3. 三个模块依赖
module dep_03_three_level;
endmodule
module dep_03_middle;
    dep_03_three_level u_leaf();
endmodule
module dep_03_top;
    dep_03_middle u_mid();
endmodule

// 4. 参数化模块依赖
module dep_04_param #(
    parameter WIDTH = 8
);
endmodule
module dep_04_top;
    dep_04_param #(.WIDTH(16)) u_param();
endmodule

// 5. 多实例
module dep_05_multi_inst;
endmodule
module dep_05_top;
    dep_05_multi_inst u_inst0();
    dep_05_multi_inst u_inst1();
    dep_05_multi_inst u_inst2();
endmodule

// 6. 参数传递
module dep_06_param_pass #(
    parameter WIDTH = 8,
    parameter DEPTH = 16
);
endmodule
module dep_06_top;
    dep_06_param_pass #(.WIDTH(32), .DEPTH(256)) u();
endmodule

// 7. 数组实例化
module dep_07_array_inst;
endmodule
module dep_07_top;
    dep_07_array_inst u_array [0:3] ();
endmodule

// 8. 嵌套实例化
module dep_08_nested;
endmodule
module dep_08_a;
    dep_08_nested u_n();
endmodule
module dep_08_b;
    dep_08_nested u_n();
endmodule
module dep_08_top;
    dep_08_a u_a();
    dep_08_b u_b();
endmodule

// 9. generate if
module dep_09_gen_if;
endmodule
module dep_09_top #(
    parameter USE_EXT = 0
);
    generate
        if (USE_EXT) begin : gen_ext
            dep_09_gen_if u_ext();
        end else begin : gen_int
            dep_09_gen_if u_int();
        end
    endgenerate
endmodule

// 10. generate for
module dep_10_gen_for;
endmodule
module dep_10_top #(
    parameter N = 4
);
    genvar i;
    generate
        for (i = 0; i < N; i = i + 1) begin : gen_loop
            dep_10_gen_for u();
        end
    endgenerate
endmodule

// 11. 条件实例化
module dep_11_conditional;
endmodule
module dep_11_top;
    dep_11_conditional u_true();
endmodule

// 12. 多个子模块
module dep_12_multi_sub;
endmodule
module dep_12_top;
    dep_12_multi_sub u_cpu();
    dep_12_multi_sub u_mem();
    dep_12_multi_sub u_uart();
    dep_12_multi_sub u_spi();
endmodule

// 13. diamond 依赖
module dep_13_diamond_leaf;
endmodule
module dep_13_a;
    dep_13_diamond_leaf u();
endmodule
module dep_13_b;
    dep_13_diamond_leaf u();
endmodule
module dep_13_top;
    dep_13_a u_a();
    dep_13_b u_b();
endmodule

// 14. 全局/本地信号
module dep_14_signals;
    logic clk, rst_n;
endmodule

// 15. 跨文件引用
// (需要在多个文件中测试)

// 16. 复杂层次
module dep_16_leaf;
endmodule
module dep_16_block_a;
    dep_16_leaf u();
endmodule
module dep_16_block_b;
    dep_16_leaf u();
endmodule
module dep_16_top;
    dep_16_block_a u_a();
    dep_16_block_b u_b();
endmodule

// 17. 递归依赖检测
module dep_17_recursive;
endmodule

// 18. 同层多个实例
module dep_18_same_level;
endmodule
module dep_18_top;
    dep_18_same_level u0();
    dep_18_same_level u1();
    dep_18_same_level u2();
    dep_18_same_level u3();
endmodule

// 19. 带连接的实例
module dep_19_with_conn(
    input clk,
    input [7:0] data_in,
    output [7:0] data_out
);
endmodule
module dep_19_top;
    logic clk;
    logic [7:0] a, b, c;
    dep_19_with_conn u1(.clk(clk), .data_in(a), .data_out(b));
    dep_19_with_conn u2(.clk(clk), .data_in(b), .data_out(c));
endmodule

// 20. 混合层次
module dep_20_leaf_a;
endmodule
module dep_20_leaf_b;
endmodule
module dep_20_middle;
    dep_20_leaf_a u_a();
    dep_20_leaf_b u_b();
endmodule
module dep_20_top;
    dep_20_middle u_mid();
    dep_20_leaf_a u_standalone();
endmodule
