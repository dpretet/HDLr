// distributed under the mit license
// https://opensource.org/licenses/mit-license.php

`timescale 1 ns / 1 ps
`default_nettype none

module param_localparam_non_ansi

    #(
    parameter NAME = 0
    )(
    );

    localparam WIDE = 4;
    parameter WIDTH = 8;
    parameter DEPTH = 16;

endmodule

`resetall

