// ============================================================================
// 跨模块追踪测试
// 测试跨模块实例化信号追踪
// ============================================================================

// 子模块1: 计数器
module counter_sub (
    input  logic clk,
    input  logic rst_n,
    input  logic enable,
    input  logic [7:0] load_val,
    output logic [7:0] count,
    output logic overflow
);
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 8'h00;
            overflow <= 1'b0;
        end else if (enable) begin
            if (count == 8'hFF) begin
                count <= load_val;
                overflow <= 1'b1;
            end else begin
                count <= count + 1;
                overflow <= 1'b0;
            end
        end
    end
endmodule

// 子模块2: FIFO
module fifo_sub (
    input  logic clk,
    input  logic rst_n,
    input  logic wr_en,
    input  logic rd_en,
    input  logic [7:0] data_in,
    output logic [7:0] data_out,
    output logic full,
    output logic empty
);
    logic [7:0] mem [0:15];
    logic [3:0] wr_ptr, rd_ptr;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr <= 4'h0;
            rd_ptr <= 4'h0;
            full <= 1'b0;
            empty <= 1'b1;
        end else begin
            if (wr_en && !full) begin
                mem[wr_ptr] <= data_in;
                wr_ptr <= wr_ptr + 1;
            end
            if (rd_en && !empty) begin
                data_out <= mem[rd_ptr];
                rd_ptr <= rd_ptr + 1;
            end
            full <= (wr_ptr == rd_ptr) && (wr_en || rd_en);
            empty <= (wr_ptr == rd_ptr) && !wr_en;
        end
    end
endmodule

// 子模块3: 寄存器文件
module regfile_sub (
    input  logic clk,
    input  logic rst_n,
    input  logic [2:0] read_addr1,
    input  logic [2:0] read_addr2,
    input  logic [2:0] write_addr,
    input  logic write_en,
    input  logic [7:0] write_data,
    output logic [7:0] read_data1,
    output logic [7:0] read_data2
);
    logic [7:0] regs [0:7];
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i < 8; i++)
                regs[i] <= 8'h00;
        end else if (write_en) begin
            regs[write_addr] <= write_data;
        end
    end
    
    always_comb begin
        read_data1 = regs[read_addr1];
        read_data2 = regs[read_addr2];
    end
endmodule

// 顶层模块 - 实例化多个子模块
module top_cross_module (
    input  logic clk,
    input  logic rst_n,
    input  logic enable,
    input  logic [7:0] load_val,
    output logic [7:0] counter_out,
    output logic counter_overflow,
    output logic [7:0] fifo_data_out,
    output logic fifo_full,
    output logic [7:0] regfile_data1,
    output logic [7:0] regfile_data2
);
    
    // 内部连接信号
    logic counter_enable;
    logic [7:0] counter_load;
    logic fifo_wr, fifo_rd;
    logic [7:0] fifo_din, fifo_dout;
    logic [2:0] rf_read_addr1, rf_read_addr2, rf_write_addr;
    logic rf_write_en;
    logic [7:0] rf_write_data;
    
    // 实例化计数器
    counter_sub u_counter (
        .clk(clk),
        .rst_n(rst_n),
        .enable(counter_enable),
        .load_val(counter_load),
        .count(counter_out),
        .overflow(counter_overflow)
    );
    
    // 实例化FIFO
    fifo_sub u_fifo (
        .clk(clk),
        .rst_n(rst_n),
        .wr_en(fifo_wr),
        .rd_en(fifo_rd),
        .data_in(fifo_din),
        .data_out(fifo_dout),
        .full(fifo_full),
        .empty()
    );
    
    // 实例化寄存器文件
    regfile_sub u_regfile (
        .clk(clk),
        .rst_n(rst_n),
        .read_addr1(rf_read_addr1),
        .read_addr2(rf_read_addr2),
        .write_addr(rf_write_addr),
        .write_en(rf_write_en),
        .write_data(rf_write_data),
        .read_data1(regfile_data1),
        .read_data2(regfile_data2)
    );
    
    // 连接逻辑
    assign counter_enable = enable;
    assign counter_load = load_val;
    assign fifo_wr = enable && !fifo_full;
    assign fifo_rd = !fifo_full;
    assign fifo_din = counter_out;
    assign fifo_data_out = fifo_dout;
    
    // 寄存器文件控制
    assign rf_read_addr1 = 3'b001;
    assign rf_read_addr2 = 3'b010;
    assign rf_write_addr = 3'b001;
    assign rf_write_en = counter_overflow;
    assign rf_write_data = counter_out;
endmodule


// 测试: 多层嵌套实例化
module nested_inst_test;
    // 层级1
    module level1 (
        input logic a,
        output logic b
    );
        logic internal_sig;
        assign b = a;
    endmodule
    
    // 层级2
    module level2 (
        input logic x,
        output logic y
    );
        logic level2_sig;
        level1 u_l1 (.a(x), .b(level2_sig));
        assign y = level2_sig;
    endmodule
    
    // 层级3
    module level3 (
        input logic p,
        output logic q
    );
        logic level3_sig;
        level2 u_l2 (.x(p), .y(level3_sig));
        assign q = level3_sig;
    endmodule
    
    // 顶层
    module top_nested (
        input logic top_in,
        output logic top_out
    );
        logic nested_sig;
        level3 u_l3 (.p(top_in), .q(nested_sig));
        assign top_out = nested_sig;
    endmodule
endmodule
