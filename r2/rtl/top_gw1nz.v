// top_gw1nz.v — GB DEVCART r2 FPGA top level for the Gowin GW1NZ-LV1 (QN48).
// Only the signals that need logic go through the FPGA (31 of its 31 free I/O, JTAG kept free):
// flash /CE = A15, flash /OE = F-RAM /OE = /RD and F-RAM /WE = /WR are wired directly on the PCB.
// The sample clock comes from the on-chip oscillator: 250 MHz / 6 ~ 41.7 MHz.
module top_gw1nz (
    input  wire        GB_NRESET,
    input  wire [15:12] GB_A,
    input  wire [7:0]  GB_D,
    input  wire        GB_NWR,
    input  wire        GB_NRD,
    input  wire        GB_NCS,
    output wire [22:14] ROM_A,
    output wire        ROM_NWE,
    output wire [14:13] RAM_A,
    output wire        RAM_NCE,
    output wire        BUS_NOE,
    output wire        BUS_DIR
);
  wire clk;
  OSCZ #(.FREQ_DIV(6)) osc (.OSCEN(1'b1), .OSCOUT(clk));

  /* verilator lint_off PINCONNECTEMPTY */
  gbcart_mapper mapper (
      .clk(clk), .nreset(GB_NRESET), .a(GB_A), .d(GB_D),
      .nwr(GB_NWR), .nrd(GB_NRD), .ncs(GB_NCS),
      .rom_a(ROM_A), .rom_ce_n(), .rom_oe_n(), .rom_we_n(ROM_NWE),
      .ram_a(RAM_A), .ram_ce_n(RAM_NCE), .ram_oe_n(), .ram_we_n(),
      .bus_oe_n(BUS_NOE), .bus_dir(BUS_DIR), .dev_mode());
endmodule
