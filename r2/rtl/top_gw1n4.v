// top_gw1n4.v — GB DEVCART r2 FPGA top level for the Gowin GW1N-LV4QN88.
// Clock: external 48 MHz oscillator on GCLKT_6 (the on-chip oscillator is only ~±5%, too loose for
// the 1 Mbaud USB UART). Pin assignment: r2/hw/fpga_pins.py -> gw1n4_qn88.cst.
module top_gw1n4 (
    input  wire        CLK48,
    input  wire        CONS_PRESENT,   // edge-connector 5 V through a divider
    input  wire        GB_NRESET,
    input  wire [15:0] GB_A,
    input  wire        GB_NWR,
    input  wire        GB_NRD,
    input  wire        GB_NCS,
    inout  wire [7:0]  CD,             // cart-side data bus (8T245 A side, flash, F-RAM)
    output wire [22:0] MA,             // flash A-1..A21 / F-RAM A0..A14
    output wire        ROM_NCE,
    output wire        ROM_NWE,
    output wire        RAM_NCE,
    output wire        RAM_NWE,
    output wire        MEM_NOE,        // shared /OE: each memory is gated by its own /CE
    output wire        BUS_NOE,
    output wire        BUS_DIR,
    input  wire        UART_RX,        // from the CH347F TXD0
    output wire        UART_TX         // to the CH347F RXD0
);
  wire [7:0] cd_out; wire cd_oe;
  wire rom_oe_n, ram_oe_n;
  assign CD = cd_oe ? cd_out : 8'bz;
  assign MEM_NOE = rom_oe_n & ram_oe_n;

  /* verilator lint_off PINCONNECTEMPTY */
  gbcart_core #(.CLKS_PER_BIT(48), .DEBOUNCE(65535)) core (
      .clk(CLK48), .cons_present(CONS_PRESENT), .gb_nreset(GB_NRESET), .gb_a(GB_A),
      .gb_nwr(GB_NWR), .gb_nrd(GB_NRD), .gb_ncs(GB_NCS),
      .cd_in(CD), .cd_out(cd_out), .cd_oe(cd_oe), .ma(MA),
      .rom_ce_n(ROM_NCE), .rom_oe_n(rom_oe_n), .rom_we_n(ROM_NWE),
      .ram_ce_n(RAM_NCE), .ram_oe_n(ram_oe_n), .ram_we_n(RAM_NWE),
      .bus_oe_n(BUS_NOE), .bus_dir(BUS_DIR),
      .uart_rx(UART_RX), .uart_tx(UART_TX), .usb_mode(), .dev_mode());
endmodule
