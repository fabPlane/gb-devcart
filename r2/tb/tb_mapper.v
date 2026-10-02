// tb_mapper.v — testbench: Game Boy bus cycles -> gbcart_mapper -> flash + F-RAM models.
//   iverilog -g2012 -o tb r2/rtl/gbcart_mapper.v r2/tb/tb_mapper.v && vvp tb
`timescale 1ns/1ps
module tb_mapper;
  // ---- console side ----
  reg  [15:0] A = 16'h0000;
  reg  [7:0]  dout = 8'h00;   // value the console drives during writes
  reg         nwr = 1, nrd = 1, nreset = 0;
  wire        ncs = !(A >= 16'hA000 && A < 16'hFE00) || nrd && nwr;
  reg         clk = 0;
  always #12 clk = !clk;      // ~41.7 MHz, like the on-chip oscillator

  // ---- mapper ----
  wire [22:14] rom_a; wire [14:13] ram_a;
  wire rom_ce_n, rom_oe_n, rom_we_n, ram_ce_n, ram_oe_n, ram_we_n, bus_oe_n, bus_dir, dev;
  wire [7:0] cd;  // cart-side data bus
  gbcart_mapper dut (.clk(clk), .nreset(nreset), .a(A[15:12]), .d(cd), .nwr(nwr), .nrd(nrd), .ncs(ncs),
      .rom_a(rom_a), .rom_ce_n(rom_ce_n), .rom_oe_n(rom_oe_n), .rom_we_n(rom_we_n),
      .ram_a(ram_a), .ram_ce_n(ram_ce_n), .ram_oe_n(ram_oe_n), .ram_we_n(ram_we_n),
      .bus_oe_n(bus_oe_n), .bus_dir(bus_dir), .dev_mode(dev));

  // ---- 74LVC8T245 model: console bus <-> cart bus ----
  wire [7:0] gd;  // console data bus
  assign cd = (!bus_oe_n && !bus_dir) ? gd : 8'bz;   // console -> cart (writes)
  assign gd = (!bus_oe_n &&  bus_dir) ? cd : 8'bz;   // cart -> console (reads)
  assign gd = !nwr ? dout : 8'bz;                     // the console drives writes
  pullup pu[7:0] (gd);

  // ---- flash model: 8 MB x8, AMD/JEDEC byte-mode commands ----
  reg [7:0] flash [0:(1<<23)-1];
  wire [22:0] fa = {rom_a, A[13:0]};
  integer fstate = 0, writes_seen = 0;
  assign cd = (!rom_ce_n && !rom_oe_n) ? flash[fa] : 8'bz;
  always @(posedge rom_we_n) if (!rom_ce_n || 1) begin : flash_cmd
    reg [7:0] v; v = cd; writes_seen = writes_seen + 1;
    if (v == 8'hF0) fstate = 0;
    else case (fstate)
      0: fstate = (fa[11:0] == 12'hAAA && v == 8'hAA) ? 1 : 0;
      1: fstate = (fa[11:0] == 12'h555 && v == 8'h55) ? 2 : 0;
      2: fstate = (fa[11:0] == 12'hAAA && v == 8'hA0) ? 3 : 0;
      3: begin flash[fa] = flash[fa] & v; fstate = 0; end
    endcase
  end

  // ---- F-RAM model: 32 KB ----
  reg [7:0] fram [0:32767];
  wire [14:0] ra = {ram_a, A[12:0]};
  assign cd = (!ram_ce_n && !ram_oe_n) ? fram[ra] : 8'bz;
  always @(posedge ram_we_n) if (!ram_ce_n) fram[ra] = cd;

  // ---- console bus cycles (DMG-like: ~1 us cycle, /WR low ~500 ns) ----
  integer wr_ns = 480;  // /WR low time; +wr_ns=150 for a GBC double-speed-like strobe
  initial if ($value$plusargs("wr_ns=%d", wr_ns)) $display("/WR low = %0d ns", wr_ns);
  task automatic gb_write(input [15:0] addr, input [7:0] val);
    begin
      A = addr; dout = val; #60; nwr = 0; #(wr_ns); nwr = 1; #120;
    end
  endtask
  task automatic gb_read(input [15:0] addr, output [7:0] val);
    begin
      A = addr; #20; nrd = 0; #300; val = gd; nrd = 1; #100;
    end
  endtask

  integer errors = 0, i;
  reg [7:0] r;
  task automatic check_read(input [15:0] addr, input [7:0] want, input [255:0] what);
    begin
      gb_read(addr, r);
      if (r !== want) begin
        errors = errors + 1;
        $display("FAIL %0s: read %04h = %02h, want %02h", what, addr, r, want);
      end
    end
  endtask

  initial begin
    for (i = 0; i < (1 << 23); i = i + 1) flash[i] = 8'hFF;
    for (i = 0; i < 512; i = i + 1) begin flash[i * 16384] = i[7:0]; flash[i * 16384 + 1] = {7'd0, i[8]}; end
    for (i = 0; i < 32768; i = i + 1) fram[i] = 8'h00;
    #200 nreset = 1; #200;

    // power-on state: bank 0 fixed, bank 1 in the window
    check_read(16'h0000, 8'h00, "bank 0 at 0000");
    check_read(16'h4000, 8'h01, "reset bank 1 at 4000");
    // MBC5 9-bit banking
    gb_write(16'h2000, 8'hFF); gb_write(16'h3000, 8'h01);
    check_read(16'h4000, 8'hFF, "bank 0x1FF low"); check_read(16'h4001, 8'h01, "bank 0x1FF bit 8");
    gb_write(16'h3000, 8'h00); check_read(16'h4000, 8'hFF, "bank 0x0FF");
    gb_write(16'h2000, 8'h00); check_read(16'h4000, 8'h00, "bank 0 selectable in window (MBC5)");
    gb_write(16'h2000, 8'h5A); check_read(16'h0000, 8'h00, "0000 stays bank 0");
    // writes to 4000-7FFF must not reach flash outside dev mode
    writes_seen = 0;
    gb_write(16'h4AAA, 8'hAA); gb_write(16'h7555, 8'h55);
    if (writes_seen != 0) begin errors = errors + 1; $display("FAIL flash /WE pulsed outside dev mode"); end
    // RAM: disabled -> console bus not driven (reads float to FF), enable -> 4 banks
    check_read(16'hA000, 8'hFF, "RAM disabled reads open bus");
    gb_write(16'h0000, 8'h0A);
    for (i = 0; i < 4; i = i + 1) begin gb_write(16'h4000, i[7:0]); gb_write(16'hA123, 8'h30 + i[7:0]); end
    for (i = 0; i < 4; i = i + 1) begin gb_write(16'h4000, i[7:0]); check_read(16'hA123, 8'h30 + i[7:0], "RAM bank"); end
    check_read(16'hBFFF, 8'h00, "RAM top");
    gb_write(16'h0000, 8'h00); check_read(16'hA123, 8'hFF, "RAM disabled again");
    // console-internal regions never see us on the bus
    A = 16'hC000; #20; nrd = 0; #200;
    if (bus_oe_n !== 1'b1) begin errors = errors + 1; $display("FAIL transceiver enabled for WRAM read"); end
    nrd = 1; #100;
    A = 16'hFF80; #20; nwr = 0; #200;
    if (bus_oe_n !== 1'b1) begin errors = errors + 1; $display("FAIL transceiver enabled for HRAM write"); end
    nwr = 1; #100;
    // dev mode: wrong sequence does nothing, right one unlocks, then flash programs via the window
    gb_write(16'h6000, "G"); gb_write(16'h6000, "B"); gb_write(16'h6000, "X"); gb_write(16'h6000, "V");
    if (dev) begin errors = errors + 1; $display("FAIL dev mode entered on wrong sequence"); end
    gb_write(16'h6000, "G"); gb_write(16'h6000, "B"); gb_write(16'h7FFF, "D"); gb_write(16'h6000, "V");
    if (!dev) begin errors = errors + 1; $display("FAIL dev mode not entered"); end
    gb_write(16'h2000, 8'h00);                       // bank 0 -> window = flash 0x0000-0x3FFF
    gb_write(16'h4AAA, 8'hAA); gb_write(16'h4555, 8'h55); gb_write(16'h4AAA, 8'hA0);
    gb_write(16'h2000, 8'h80); gb_write(16'h3000, 8'h01);  // target bank 0x180
    gb_write(16'h4321, 8'h42);
    check_read(16'h4321, 8'h42, "flash program in dev mode");
    if (flash[23'h180 * 16384 + 23'h0321] !== 8'h42) begin errors = errors + 1; $display("FAIL flash array"); end
    gb_write(16'h4000, 8'h01);  // in dev mode this goes to flash, not the RAM bank register
    if (dut.ram_bank !== 2'd3) begin errors = errors + 1; $display("FAIL RAM bank changed in dev mode"); end
    gb_write(16'h0000, 8'hD0);
    if (dev) begin errors = errors + 1; $display("FAIL dev mode not left on 0xD0"); end
    // reset clears everything
    nreset = 0; #100; nreset = 1; #100;
    check_read(16'h4000, 8'h01, "bank 1 after reset");

    if (errors == 0) $display("PASS: all mapper checks");
    else $display("%0d FAILURES", errors);
    $finish;
  end
endmodule
