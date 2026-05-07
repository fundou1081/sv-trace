// ============================================================================
// DriverTracer 语法覆盖度金标准测试
// 按项目纪律：每个module测试一种场景，期望明确标注
// ============================================================================

// ============================================================================
// 支持的语法 (完全支持)
// ============================================================================

// 1. always_ff posedge 时钟
// 期望: 时钟提取 clk
module covered_01_posedge;
    logic clk;
    logic [7:0] data;
    always_ff @(posedge clk) begin
        data <= data + 1;
    end
endmodule

// 2. always_ff 异步复位 (or negedge)
// 期望: 时钟 clk, 复位 rst_n
module covered_02_async_reset;
    logic clk, rst_n;
    logic [7:0] data;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            data <= 8'h0;
        else
            data <= data + 1;
    end
endmodule

// 3. always_ff 同步复位 high (if rst)
// 期望: 时钟 clk, 复位 rst
module covered_03_sync_reset_high;
    logic clk, rst;
    logic [7:0] data;
    always_ff @(posedge clk) begin
        if (rst)
            data <= 8'h0;
        else
            data <= data + 1;
    end
endmodule

// 4. always_ff 同步复位 low (if !rst_n)
// 期望: 时钟 clk, 复位 rst_n
module covered_04_sync_reset_low;
    logic clk, rst_n;
    logic [7:0] data;
    always_ff @(posedge clk) begin
        if (!rst_n)
            data <= 8'h0;
        else
            data <= data + 1;
    end
endmodule

// 5. generate for 循环生成
// 期望: 时钟 clk, 复位 rst_n
module covered_05_generate_for;
    logic clk, rst_n;
    logic [7:0] data [0:3];
    genvar i;
    generate
        for (i = 0; i < 4; i = i + 1) begin : gen_block
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    data[i] <= 8'h0;
                else
                    data[i] <= i;
            end
        end
    endgenerate
endmodule

// 6. function 返回值作为驱动源
// 期望: 时钟 clk, 复位 rst
module covered_06_function_return;
    logic clk, rst;
    logic [7:0] data, result;
    
    function logic [7:0] calc(input logic [7:0] a);
        return a + 1;
    endfunction
    
    always_ff @(posedge clk) begin
        if (rst)
            result <= 8'h0;
        else
            result <= calc(data);
    end
endmodule

// ============================================================================
// 部分支持语法 (标注为已知限制)
// ============================================================================

// 7. Class Method - 类方法驱动
// 期望: 可解析，但方法内驱动可能不完全提取
module partial_01_class_method;
    logic clk, rst;
    logic [7:0] data_out;
    
    class DriverClass;
        randc logic [7:0] rand_data;
        function void drive_signal(output logic [7:0] d);
            d <= rand_data;
        endfunction
    endclass
    
    DriverClass drv;
    initial drv = new();
    
    always_ff @(posedge clk) begin
        if (rst)
            data_out <= 8'h0;
        else
            drv.drive_signal(data_out);
    end
endmodule

// 8. Clocking Block - 时钟块
// 期望: 解析但不提取clocking块内的信号定义
module partial_02_clocking_block;
    logic clk;
    logic [7:0] data, valid;
    
    clocking cb @(posedge clk);
        input data;
        output valid;
    endclocking
    
    // 实际驱动在clocking外部
    always_ff @(posedge clk) begin
        valid <= data;
    end
endmodule

// 9. Interface Modport - 接口modport
// 期望: 解析但不提取modport连接
module partial_03_interface_modport;
    logic clk;
    logic [7:0] data;
    
    interface IF_MAC;
        logic [7:0] data;
        modport mp(input data);
        modport mp_out(output data);
    endinterface
    
    IF_MAC intf();
    assign intf.data = data;
    
    always_ff @(posedge clk) begin
        intf.mp_out.data <= 8'h0;
    end
endmodule

// 10. Sequence 定义 - SVA序列
// 期望: 解析但序列本身不产生驱动
module partial_04_sequence;
    logic clk, a, b;
    
    sequence seq_match;
        @(posedge clk) a ##1 b;
    endsequence
    
    // 实际驱动
    always_ff @(posedge clk) begin
        b <= a;
    end
endmodule

// 11. Property 定义 - SVA属性
// 期望: 解析但属性不产生驱动
module partial_05_property;
    logic clk, a, b;
    
    property prop_check;
        @(posedge clk) a |-> ##1 b;
    endproperty
    
    // 实际驱动
    always_ff @(posedge clk) begin
        b <= a;
    end
endmodule

// 12. Randc - 随机循环变量
// 期望: 解析但使用需实例化
module partial_06_randc;
    logic clk;
    logic [7:0] data;
    
    class Stimulus;
        randc logic [7:0] rand_data;
    endclass
    
    Stimulus stim;
    
    always_ff @(posedge clk) begin
        data <= stim.rand_data;
    end
endmodule

// ============================================================================
// 不支持语法 (已确认无法正确提取驱动)
// ============================================================================

// 13. Force Statement - 强制赋值
// 期望: ⚠️ 不支持提取为驱动
module unsupported_01_force;
    logic clk;
    logic [7:0] a, b;
    always_ff @(posedge clk) begin
        force a = b;
    end
endmodule

// 14. Release Statement - 释放赋值
// 期望: ⚠️ 不支持提取为驱动
module unsupported_02_release;
    logic clk;
    logic [7:0] a, b;
    always_ff @(posedge clk) begin
        release a;
    end
endmodule

// 15. Alias Statement - 线网别名
// 期望: ⚠️ 不支持提取为驱动
module unsupported_03_alias;
    logic [7:0] a, b;
    alias a = b;
endmodule

// 16. Deassign - 取消赋值
// 期望: ⚠️ 不支持提取为驱动
module unsupported_04_deassign;
    logic clk;
    logic [7:0] a;
    always_ff @(posedge clk) begin
        deassign a;
    end
endmodule

