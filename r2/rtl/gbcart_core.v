// gbcart_core.v — GB DEVCART r2 logic, vendor independent: MBC5 mapper (console mode) + USB
// engine (no console). The console-present input is the cart's 5 V edge pin through a divider; when
// it has been low for DEBOUNCE clocks the cart switches to USB mode and the UART owns the memories.
module gbcart_core #(
    parameter CLKS_PER_BIT = 42,     // UART: 41.7 MHz / 1 Mbaud
    parameter DEBOUNCE     = 65535   // ~1.6 ms at 41.7 MHz
) (
    input  wire        clk,
    input  wire        cons_present,   // high while the console powers the edge connector
    input  wire        gb_nreset,
    input  wire [15:0] gb_a,
    input  wire        gb_nwr,
    input  wire        gb_nrd,
    input  wire        gb_ncs,
    input  wire [7:0]  cd_in,
    output wire [7:0]  cd_out,
    output wire        cd_oe,          // FPGA drives the cart data bus (USB-mode writes only)
    output wire [22:0] ma,
    output wire        rom_ce_n, rom_oe_n, rom_we_n,
    output wire        ram_ce_n, ram_oe_n, ram_we_n,
    output wire        bus_oe_n, bus_dir,
    input  wire        uart_rx,
    output wire        uart_tx,
    output wire        usb_mode,
    output wire        dev_mode
);
  // console-present: synchronise, then require it to be stable for DEBOUNCE clocks
  reg [1:0]  cp_s = 2'b00;
  reg [16:0] cp_cnt = 0;
  reg        usb = 1'b1;
  always @(posedge clk) begin
    cp_s <= {cp_s[0], cons_present};
    if (cp_s[1] == usb) begin              // input disagrees with the current mode
      if (cp_cnt == DEBOUNCE) begin usb <= !cp_s[1]; cp_cnt <= 0; end
      else cp_cnt <= cp_cnt + 1'b1;
    end else cp_cnt <= 0;
  end
  assign usb_mode = usb;

  wire [22:0] u_ma;
  wire u_rce, u_roe, u_rwe, u_ace, u_aoe, u_awe;
  usb_engine #(.CLKS_PER_BIT(CLKS_PER_BIT)) engine (
      .clk(clk), .usb_mode(usb), .dev_mode(dev_mode), .rx(uart_rx), .tx(uart_tx),
      .cd_in(cd_in), .cd_out(cd_out), .cd_oe(cd_oe), .ma(u_ma),
      .rom_ce_n(u_rce), .rom_oe_n(u_roe), .rom_we_n(u_rwe),
      .ram_ce_n(u_ace), .ram_oe_n(u_aoe), .ram_we_n(u_awe));

  // The mapper is held in reset while in USB mode, so returning to a console starts from a
  // fresh MBC5 state.
  gbcart_mapper mapper (
      .clk(clk), .nreset(gb_nreset && !usb), .ga(gb_a), .cd_in(cd_in),
      .nwr(gb_nwr), .nrd(gb_nrd), .ncs(gb_ncs),
      .ma(ma), .rom_ce_n(rom_ce_n), .rom_oe_n(rom_oe_n), .rom_we_n(rom_we_n),
      .ram_ce_n(ram_ce_n), .ram_oe_n(ram_oe_n), .ram_we_n(ram_we_n),
      .bus_oe_n(bus_oe_n), .bus_dir(bus_dir), .dev_mode(dev_mode),
      .usb_mode(usb), .usb_ma(u_ma),
      .usb_rom_ce_n(u_rce), .usb_rom_oe_n(u_roe), .usb_rom_we_n(u_rwe),
      .usb_ram_ce_n(u_ace), .usb_ram_oe_n(u_aoe), .usb_ram_we_n(u_awe));
endmodule
