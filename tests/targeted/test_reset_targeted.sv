// ============================================================================
// Reset Integrity Targeted Test Cases - 复位完整性专项测试
// ============================================================================

// Test 1: 异步复位 (async reset)
module reset_async (
    input  logic clk,
    input  logic rst_n,  // 异步低有效复位
    input  logic [7:0] data_in,
    output logic [7:0] data_out
);
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            data_out <= 0;
        else
            data_out <= data_in;
    end
endmodule


// Test 2: 同步复位 (sync reset)
module reset_sync (
    input  logic clk,
    input  logic rst_n,
    input  logic [7:0] data_in,
    output logic [7:0] data_out
);
    always_ff @(posedge clk) begin
        if (!rst_n)
            data_out <= 0;
        else
            data_out <= data_in;
    end
endmodule


// Test 3: 异步置位同步释放
module reset_async_set_sync_release (
    input  logic clk,
    input  logic rst_n,
    input  logic set_n,
    output logic q
);
    always_ff @(posedge clk or negedge set_n) begin
        if (!set_n)
            q <= 1;
        else if (!rst_n)
            q <= 0;
        else
            q <= 1'b0;
    end
endmodule


// Test 4: 多复位源
module reset_multi_source (
    input  logic clk,
    input  logic rst_n,    // 主复位
    input  logic rst_peripheral_n,  // 外设复位
    input  logic [7:0] data_in,
    output logic [7:0] data_reg,
    output logic [7:0] counter
);
    // 数据寄存器使用外设复位
    always_ff @(posedge clk or negedge rst_peripheral_n) begin
        if (!rst_peripheral_n)
            data_reg <= 0;
        else
            data_reg <= data_in;
    end
    
    // 计数器使用主复位
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            counter <= 0;
        else
            counter <= counter + 1;
    end
endmodule


// Test 5: 无复位设计
module reset_none (
    input  logic clk,
    input  logic [7:0] data_in,
    output logic [7:0] data_out
);
    always_ff @(posedge clk) begin
        data_out <= data_in;
    end
endmodule


// Test 6: 复位与时钟门控
module reset_clock_gate (
    input  logic clk,
    input  logic rst_n,
    input  logic clk_en,
    input  logic [7:0] data_in,
    output logic [7:0] data_out
);
    logic gated_clk;
    
    // 时钟门控
    assign gated_clk = clk && clk_en;
    
    always_ff @(posedge gated_clk or negedge rst_n) begin
        if (!rst_n)
            data_out <= 0;
        else
            data_out <= data_in;
    end
endmodule


// Test 7: 高扇出复位树
module reset_tree_high_fanout (
    input  logic clk,
    input  logic rst_n,
    output logic [31:0] registers
);
    // 32个寄存器，全部使用同一个复位
    genvar i;
    generate
        for (i = 0; i < 32; i = i + 1) begin : reg_array
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    registers[i] <= 0;
                else
                    registers[i] <= data_in[i];
            end
        end
    endgenerate
    
    logic [31:0] data_in;
endmodule
