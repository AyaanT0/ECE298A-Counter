`default_nettype none
`timescale 1ns / 1ps

/* This testbench instantiates the module, models uio pads as a tristate bus,
  makes wires that can be used by cocotb
*/
module tb ();

  // Dump the signals to a FST file. You can view it with gtkwave or surfer.
  initial begin
    $dumpfile("tb.fst");
    $dumpvars(0, tb);
    #1;
  end

  // Wire up the inputs and outputs:
  reg clk;
  reg rst_n;
  reg ena;
  reg [7:0] ui_in;
  wire [7:0] uio_in;
  wire [7:0] uo_out;
  wire [7:0] uio_out;
  wire [7:0] uio_oe;
`ifdef GL_TEST
  wire VPWR = 1'b1;
  wire VGND = 1'b0;
`endif

  // model of the uio pads
  reg ext_oe;
  reg [7:0] ext_data;
  wire [7:0] uio_bus;

  genvar i;
  generate
    for (i = 0; i < 8; i = i + 1) begin : g_uio_pad
      assign uio_bus[i] = uio_oe[i] ? uio_out[i] : 1'bz;
    end
  endgenerate

  assign uio_bus = ext_oe ? ext_data : 8'bz;
  assign uio_in  = uio_bus;

  tt_um_ayaant0_counter user_project (

      // Include power ports for the Gate Level test:
`ifdef GL_TEST
      .VPWR(VPWR),
      .VGND(VGND),
`endif

      .ui_in  (ui_in),    // Dedicated inputs
      .uo_out (uo_out),   // Dedicated outputs
      .uio_in (uio_in),   // IOs: Input path
      .uio_out(uio_out),  // IOs: Output path
      .uio_oe (uio_oe),   // IOs: Enable path (active high: 0=input, 1=output)
      .ena    (ena),      // enable - goes high when design is selected
      .clk    (clk),      // clock
      .rst_n  (rst_n)     // not reset
  );

endmodule
