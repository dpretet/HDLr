// distributed under the mit license
// https://opensource.org/licenses/mit-license.php

`timescale 1 ns / 1 ps
`default_nettype none

module ModuleName

    #(
    parameter NAME = 0
    )(
    input  wire aclk,
    input  wire aresetn,
    output logic encoded,
    output logic [3:0] encoded1,
    output logic [4-1:0] encoded2
    );

    parameter ACLKK = 5;

    reg register0;
    reg [31:0] register1;
    logic [31:0] register2;

endmodule

`resetall

