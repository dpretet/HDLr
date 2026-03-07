// distributed under the mit license
// https://opensource.org/licenses/mit-license.php

`timescale 1 ns / 1 ps
`default_nettype none


module alu(input a, input b, output y);

submodule #(
    .WIDTH(8)
) u_sub (
    .clk(clk),
    .data(data)
);

endmodule

`resetall
