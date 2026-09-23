/*
 * Copyright (c) 2026 Ayaan Tunio
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module ayaant0_counter8 #(parameter WIDTH = 8) (
    input wire clk,
    input wire rst_n, // async reset (active low)
    input wire load, // sync load (atcive high)
    input wire en, // count en (active high)
    input wire [WIDTH-1:0] d, // load when = 1
    output reg [WIDTH-1:0] q // curr count
);

  localparam [WIDTH-1:0] ONE = 1;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= {WIDTH{1'b0}};
    else if (load) q <= d;
    else if (en) q <= q + ONE;
  end

endmodule