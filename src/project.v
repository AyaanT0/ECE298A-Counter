/*
 * Copyright (c) 2026 Ayaan Tunio
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_ayaant0_counter (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  wire load = ui_in[0];
  wire oe = ui_in[1];
  wire en = ui_in[2];

  wire [7:0] count;
  wire [7:0] load_data = oe ? count : uio_in;

  ayaant0_counter8 #(.WIDTH(8)) counter (
      .clk(clk),
      .rst_n(rst_n),
      .load(load),
      .en(en),
      .d(load_data),
      .q(count)
  );

  assign uio_out = count;
  assign uio_oe = {8{oe}};
  assign uo_out = count;

  // List all unused inputs to prevent warnings
  wire _unused = &{ena, ui_in[7:3], 1'b0};

endmodule
