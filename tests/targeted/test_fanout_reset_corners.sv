// ============================================================================
// Fanout & Reset Corner Cases - 扇出和复位边界测试
// ============================================================================

// ============================================================================
// Fanout Corner Cases
// ============================================================================

module fanout_corners;
    // Test 1: 时钟信号高扇出
    // 假设一个时钟驱动100个寄存器
    logic clk;
    logic rst_n;
    
    // 100个寄存器全部由同一个时钟驱动
    genvar i;
    generate
        for (i = 0; i < 100; i = i + 1) begin : clk_fanout_test
            logic [7:0] reg_data;
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    reg_data <= 8'b0;
                else
                    reg_data <= reg_data + 1;
            end
        end
    endgenerate

    // Test 2: 复位信号高扇出
    // 100个寄存器全部由同一个复位复位
    generate
        for (i = 0; i < 100; i = i + 1) begin : rst_fanout_test
            logic [7:0] reset_reg;
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    reset_reg <= 8'hAA;  // 复位到特定值
                else
                    reset_reg <= reset_reg + 1;
            end
        end
    endgenerate

    // Test 3: 使能信号不均衡分布
    logic enable;
    logic [7:0] en_counter;
    
    // enable驱动4个不同的功能块，每个功能块内部扇出不同
    generate
        for (i = 0; i < 4; i = i + 1) begin : uneven_fanout
            logic [7:0] block_en_reg;
            always_ff @(posedge clk) begin
                if (enable)
                    block_en_reg <= i;
            end
        end
    endgenerate

    // Test 4: 扇出为0(孤立信号)
    logic isolated_signal;
    logic [7:0] unused_reg;
    
    // isolated_signal定义了但没有被任何always块使用
    assign isolated_signal = clk;  // 被驱动但没有被使用
    
    // unused_reg被always块赋值但值没有被使用
    always_ff @(posedge clk) begin
        unused_reg <= unused_reg + 1;
    end

    // Test 5: 多源驱动同一信号
    logic shared_signal;
    
    // 同一信号被多个always块驱动 - 危险!
    always_ff @(posedge clk) begin
        shared_signal <= a;  // 驱动1
    end
    
    always_ff @(posedge clk) begin
        shared_signal <= b;  // 驱动2 - 多驱动!
    end
    
    logic a, b;
endmodule


// ============================================================================
// Reset Corner Cases
// ============================================================================

module reset_corners;
    logic clk;
    logic rst_n;
    logic async_rst_n;
    logic sync_rst_n;
    logic [7:0] data_in;
    logic [7:0] data_out1, data_out2, data_out3, data_out4;

    // Test 1: 异步复位，同步释放
    always_ff @(posedge clk or negedge async_rst_n) begin
        if (!async_rst_n)
            data_out1 <= 8'b0;
        else
            data_out1 <= data_in;
    end

    // Test 2: 同步复位
    always_ff @(posedge clk) begin
        if (!sync_rst_n)
            data_out2 <= 8'b0;
        else
            data_out2 <= data_in;
    end

    // Test 3: 内部生成的复位
    logic internal_rst;
    logic [3:0] rst_counter;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rst_counter <= 4'b0;
            internal_rst <= 1'b0;
        end else begin
            if (rst_counter < 4'b1111)
                rst_counter <= rst_counter + 1;
            else
                internal_rst <= 1'b1;  // 内部生成复位脉冲
        end
    end
    
    logic [7:0] internal_rst_reg;
    always_ff @(posedge clk or negedge internal_rst) begin
        if (!internal_rst)
            internal_rst_reg <= 8'h55;
        else
            internal_rst_reg <= data_in;
    end

    // Test 4: 多级复位链
    logic [2:0] rst_chain;
    logic [7:0] chain_reg1, chain_reg2, chain_reg3;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            rst_chain <= 3'b000;
        else
            rst_chain <= {rst_chain[1:0], 1'b1};
    end
    
    always_ff @(posedge clk or negedge rst_chain[0]) begin
        if (!rst_chain[0])
            chain_reg1 <= 8'b0;
        else
            chain_reg1 <= data_in;
    end
    
    always_ff @(posedge clk or negedge rst_chain[1]) begin
        if (!rst_chain[1])
            chain_reg2 <= 8'b0;
        else
            chain_reg2 <= data_in;
    end
    
    always_ff @(posedge clk or negedge rst_chain[2]) begin
        if (!rst_chain[2])
            chain_reg3 <= 8'b0;
        else
            chain_reg3 <= data_in;
    end

    // Test 5: 复位时序问题 - 复位释放顺序
    logic rst_a, rst_b;
    logic rst_a_sync, rst_b_sync;
    logic [1:0] rst_a_meta, rst_b_meta;
    
    // 两级同步器
    always_ff @(posedge clk) begin
        rst_a_meta <= {rst_a_meta[0], rst_a};
        rst_b_meta <= {rst_b_meta[0], rst_b};
    end
    
    assign rst_a_sync = rst_a_meta[1];
    assign rst_b_sync = rst_b_meta[1];
    
    logic [7:0] reg_a, reg_b;
    
    // 寄存器A
    always_ff @(posedge clk or negedge rst_a_sync) begin
        if (!rst_a_sync)
            reg_a <= 8'hAA;
        else
            reg_a <= data_in;
    end
    
    // 寄存器B - 依赖寄存器A的复位释放时序
    always_ff @(posedge clk or negedge rst_b_sync) begin
        if (!rst_b_sync)
            reg_b <= 8'hBB;
        else
            reg_b <= reg_a;  // 使用reg_a的值
    end

    // Test 6: 上电复位序列
    logic [7:0] power_up_counter;
    logic power_up_done;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            power_up_counter <= 8'b0;
            power_up_done <= 1'b0;
        end else begin
            if (power_up_counter < 8'd100)
                power_up_counter <= power_up_counter + 1;
            else
                power_up_done <= 1'b1;
        end
    end
    
    // 仅在power_up_done后才正常工作
    logic [7:0] normal_reg;
    always_ff @(posedge clk) begin
        if (power_up_done)
            normal_reg <= data_in;
    end

    // Test 7: 条件复位
    logic cond_rst;
    logic [7:0] cond_rst_reg;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            cond_rst_reg <= 8'b0;
        else if (cond_rst)  // 条件复位
            cond_rst_reg <= 8'b0;
        else
            cond_rst_reg <= data_in;
    end

    // Test 8: 读写复位(读时清零)
    logic read_en;
    logic [7:0] read_clear_reg;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            read_clear_reg <= 8'b0;
        else if (read_en)
            read_clear_reg <= 8'b0;  // 读操作清零
        else
            read_clear_reg <= data_in;
    end
endmodule


// ============================================================================
// Combined: Fanout + Reset Corner Cases
// ============================================================================

module fanout_reset_combined;
    logic clk;
    logic rst_n;
    logic global_enable;
    
    // 全局使能信号，扇出到多个模块
    // 模块1
    logic [7:0] mod1_counter;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            mod1_counter <= 0;
        else if (global_enable)
            mod1_counter <= mod1_counter + 1;
    end
    
    // 模块2
    logic [7:0] mod2_counter;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            mod2_counter <= 0;
        else if (global_enable)
            mod2_counter <= mod2_counter + 1;
    end
    
    // 模块3 - 多个使能条件
    logic mod3_enable;
    logic [7:0] mod3_counter;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            mod3_counter <= 0;
        else if (mod3_enable && global_enable)
            mod3_counter <= mod3_counter + 1;
    end
    
    // 模块4 - 使能反相
    logic mod4_enable;
    logic [7:0] mod4_counter;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            mod4_counter <= 0;
        else if (!mod4_enable && global_enable)
            mod4_counter <= mod4_counter + 1;
    end
    
    // 复位也可能有不同的组合
    logic global_rst;
    logic [7:0] global_rst_counter;
    
    always_ff @(posedge clk or negedge global_rst) begin
        if (!global_rst)
            global_rst_counter <= 0;
        else
            global_rst_counter <= global_rst_counter + 1;
    end
endmodule
