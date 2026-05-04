// Test 5: Nested if - Priority encoder
module priority_encoder (
    input  logic [7:0] req,
    output logic [2:0] grant,
    output logic        valid
);
    // 嵌套 if - 优先级编码
    always_comb begin
        valid = 1'b0;
        grant = 3'h0;
        
        if (req[7]) begin
            valid = 1'b1;
            grant = 3'd7;
        end else if (req[6]) begin
            valid = 1'b1;
            grant = 3'd6;
        end else if (req[5]) begin
            valid = 1'b1;
            grant = 3'd5;
        end else if (req[4]) begin
            valid = 1'b1;
            grant = 3'd4;
        end else if (req[3]) begin
            valid = 1'b1;
            grant = 3'd3;
        end else if (req[2]) begin
            valid = 1'b1;
            grant = 3'd2;
        end else if (req[1]) begin
            valid = 1'b1;
            grant = 3'd1;
        end else if (req[0]) begin
            valid = 1'b1;
            grant = 3'd0;
        end
    end
endmodule
