// distributed under the mit license
// https://opensource.org/licenses/mit-license.php

`timescale 1 ns / 1 ps
`default_nettype none

module param_localparam

    #(
    parameter NAME = 0
    )(
    );

    parameter WIDTH = 8;
    parameter DEPTH = 16;

endmodule

`resetall

