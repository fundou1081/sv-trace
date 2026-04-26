// ============================================================================
// 循环依赖测试
// 测试模块间循环依赖检测
// ============================================================================

// Test 1: 简单循环依赖 A -> B -> A
module module_a (
    input  logic clk,
    input  logic [7:0] data_from_b,
    output logic [7:0] data_to_b
);
    logic [7:0] internal_a;
    
    always_ff @(posedge clk) begin
        internal_a <= data_from_b + 1;
        data_to_b <= internal_a;
    end
endmodule

module module_b (
    input  logic clk,
    input  logic [7:0] data_from_a,
    output logic [7:0] data_to_a
);
    logic [7:0] internal_b;
    
    always_ff @(posedge clk) begin
        internal_b <= data_from_a + 1;
        data_to_a <= internal_b;
    end
endmodule

// top包含A和B，形成 A <-> B 循环
module top_circular_simple (
    input  logic clk,
    input  logic rst_n
);
    logic [7:0] a_to_b, b_to_a;
    
    module_a u_a (.clk(clk), .data_from_b(b_to_a), .data_to_b(a_to_b));
    module_b u_b (.clk(clk), .data_from_a(a_to_b), .data_to_a(b_to_a));
endmodule


// Test 2: 多模块循环 A -> B -> C -> A
module module_c_a (
    input  logic clk,
    input  logic [7:0] from_c,
    output logic [7:0] to_c
);
    logic [7:0] reg_a;
    always_ff @(posedge clk) begin
        reg_a <= from_c + 1;
        to_c <= reg_a;
    end
endmodule

module module_c_b (
    input  logic clk,
    input  logic [7:0] from_a,
    output logic [7:0] to_a
);
    logic [7:0] reg_b;
    always_ff @(posedge clk) begin
        reg_b <= from_a + 1;
        to_a <= reg_b;
    end
endmodule

module module_c_c (
    input  logic clk,
    input  logic [7:0] from_b,
    output logic [7:0] to_b
);
    logic [7:0] reg_c;
    always_ff @(posedge clk) begin
        reg_c <= from_b + 1;
        to_b <= reg_c;
    end
endmodule

// top形成 A -> B -> C -> A 循环
module top_circular_chain (
    input  logic clk,
    input  logic rst_n
);
    logic [7:0] a_to_b, b_to_c, c_to_a;
    
    module_c_a u_a (.clk(clk), .from_c(c_to_a), .to_c(a_to_b));
    module_c_b u_b (.clk(clk), .from_a(a_to_b), .to_a(b_to_c));
    module_c_c u_c (.clk(clk), .from_b(b_to_c), .to_b(c_to_a));
endmodule


// Test 3: 自循环 - 模块输出直接反馈到输入
module self_loop (
    input  logic clk,
    input  logic rst_n,
    input  logic [7:0] data_in,
    output logic [7:0] data_out
);
    logic [7:0] reg_data;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            reg_data <= 8'h00;
        else
            reg_data <= data_in + reg_data;  // 自循环: reg_data = data_in + reg_data
    end
    
    assign data_out = reg_data;
endmodule


// Test 4: 复杂循环 with enable
module enable_feedback_a (
    input  logic clk,
    input  logic enable,
    input  logic [7:0] from_b,
    output logic [7:0] to_b
);
    logic [7:0] reg_a;
    always_ff @(posedge clk) begin
        if (enable)
            reg_a <= from_b + 1;
        to_b <= reg_a;
    end
endmodule

module enable_feedback_b (
    input  logic clk,
    input  logic enable,
    input  logic [7:0] from_a,
    output logic [7:0] to_a
);
    logic [7:0] reg_b;
    always_ff @(posedge clk) begin
        if (enable)
            reg_b <= from_a + 1;
        to_a <= reg_b;
    end
endmodule

module top_enable_circular (
    input  logic clk,
    input  logic enable,
    input  logic rst_n
);
    logic [7:0] a_to_b, b_to_a;
    
    enable_feedback_a u_a (.clk(clk), .enable(enable), .from_b(b_to_a), .to_b(a_to_b));
    enable_feedback_b u_b (.clk(clk), .enable(enable), .from_a(a_to_b), .to_a(b_to_a));
endmodule


// Test 5: 无循环 - 正常的前馈设计
module no_circular_a (
    input  logic clk,
    input  logic [7:0] data_in,
    output logic [7:0] data_out
);
    logic [7:0] reg_a;
    always_ff @(posedge clk) begin
        reg_a <= data_in + 1;
    end
    assign data_out = reg_a;
endmodule

module no_circular_b (
    input  logic clk,
    input  logic [7:0] data_from_a,
    output logic [7:0] data_to_c
);
    logic [7:0] reg_b;
    always_ff @(posedge clk) begin
        reg_b <= data_from_a + 1;
    end
    assign data_to_c = reg_b;
endmodule

module no_circular_c (
    input  logic clk,
    input  logic [7:0] data_from_b,
    output logic [7:0] data_out
);
    logic [7:0] reg_c;
    always_ff @(posedge clk) begin
        reg_c <= data_from_b + 1;
    end
    assign data_out = reg_c;
endmodule

// top: A -> B -> C, 无循环
module top_no_circular (
    input  logic clk,
    input  logic rst_n
);
    logic [7:0] a_to_b, b_to_c;
    
    no_circular_a u_a (.clk(clk), .data_in(8'h00), .data_out(a_to_b));
    no_circular_b u_b (.clk(clk), .data_from_a(a_to_b), .data_to_c(b_to_c));
    no_circular_c u_c (.clk(clk), .data_from_b(b_to_c), .data_out());
endmodule
