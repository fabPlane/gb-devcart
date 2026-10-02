// tb_mapper.v — testbench: Game Boy bus cycles and USB-UART commands -> gbcart_core ->
// flash + F-RAM models.
//   iverilog -g2012 -o tb r2/rtl/*.v r2/tb/tb_mapper.v && vvp tb
`timescale 1ns/1ps
module tb_mapper;
  // ---- console side ----
  reg  [15:0] A = 16'h0000;
  reg  [7:0]  dout = 8'h00;   // value the console drives during writes
  reg         nwr = 1, nrd = 1, nreset = 0, cons = 1;
  wire        ncs = !(A >= 16'hA000 && A < 16'hFE00) || nrd && nwr;
  reg         clk = 0;
  always #12 clk = !clk;      // ~41.7 MHz, like the on-chip oscillator

  // ---- DUT ----
  localparam CPB = 42;        // 1 Mbaud
  wire [22:0] ma;
  wire rom_ce_n, rom_oe_n, rom_we_n, ram_ce_n, ram_oe_n, ram_we_n, bus_oe_n, bus_dir, dev, usb;
  wire [7:0] cd, cd_out; wire cd_oe;
  reg  urx = 1'b1; wire utx;
  gbcart_core #(.CLKS_PER_BIT(CPB), .DEBOUNCE(200)) dut (
      .clk(clk), .cons_present(cons), .gb_nreset(nreset), .gb_a(A), .gb_nwr(nwr), .gb_nrd(nrd), .gb_ncs(ncs),
      .cd_in(cd), .cd_out(cd_out), .cd_oe(cd_oe), .ma(ma),
      .rom_ce_n(rom_ce_n), .rom_oe_n(rom_oe_n), .rom_we_n(rom_we_n),
      .ram_ce_n(ram_ce_n), .ram_oe_n(ram_oe_n), .ram_we_n(ram_we_n),
      .bus_oe_n(bus_oe_n), .bus_dir(bus_dir), .uart_rx(urx), .uart_tx(utx), .usb_mode(usb), .dev_mode(dev));
  assign cd = cd_oe ? cd_out : 8'bz;

  // ---- 74LVC8T245 model: console bus <-> cart bus ----
  wire [7:0] gd;  // console data bus
  // 4 ns propagation / turn-off, like the real part: the memories latch data on the rising /WE
  // with 0 ns hold, which the transceiver's turn-off delay covers.
  assign #4 cd = (!bus_oe_n && !bus_dir) ? gd : 8'bz;   // console -> cart (writes)
  assign #4 gd = (!bus_oe_n &&  bus_dir) ? cd : 8'bz;   // cart -> console (reads)
  assign gd = !nwr ? dout : 8'bz;                     // the console drives writes
  pullup pu[7:0] (gd);

  // ---- flash model: 8 MB x8, AMD/JEDEC byte-mode commands incl. write-buffer programming ----
  reg [7:0] flash [0:(1<<23)-1];
  wire [22:0] fa = ma;
  integer fstate = 0, writes_seen = 0, wb_left = 0, busy_polls = 0;
  reg flash_busy = 1'b0; event go_busy;
  always @(go_busy) begin flash_busy = 1'b1; #2000; flash_busy = 1'b0; end  // program takes 2 us
  reg [22:0] wb_addr [0:31]; reg [7:0] wb_data [0:31]; integer wb_n = 0, j;
  reg [7:0] busy_val = 8'h00, toggle = 8'h00;
  wire [7:0] flash_q = flash_busy ? ((~busy_val & 8'h80) | toggle) : flash[fa];
  assign cd = (!rom_ce_n && !rom_oe_n) ? flash_q : 8'bz;
  always @(posedge rom_oe_n) if (flash_busy) begin busy_polls = busy_polls + 1; toggle = toggle ^ 8'h40; end
  always @(posedge rom_we_n) if (!rom_ce_n) begin : flash_cmd
    reg [7:0] v; v = cd; writes_seen = writes_seen + 1;
    case (fstate)
      0: fstate = (fa[11:0] == 12'hAAA && v == 8'hAA) ? 1 : 0;
      1: fstate = (fa[11:0] == 12'h555 && v == 8'h55) ? 2 : 0;
      2: if (fa[11:0] == 12'hAAA && v == 8'hA0) fstate = 3;
         else if (v == 8'h25) fstate = 4;                    // write-buffer load at sector address
         else fstate = 0;
      3: begin flash[fa] = flash[fa] & v; busy_val = v; -> go_busy; fstate = 0; end
      4: begin wb_left = v + 1; wb_n = 0; fstate = 5; end    // word count - 1
      5: begin wb_addr[wb_n] = fa; wb_data[wb_n] = v; wb_n = wb_n + 1; wb_left = wb_left - 1;
               if (wb_left == 0) fstate = 6; end
      6: begin
           if (v == 8'h29) begin
             for (j = 0; j < wb_n; j = j + 1) flash[wb_addr[j]] = flash[wb_addr[j]] & wb_data[j];
             busy_val = wb_data[wb_n - 1]; -> go_busy;
           end
           fstate = 0;
         end
    endcase
    if (v == 8'hF0 && fstate != 5) fstate = 0;
  end

  // ---- F-RAM model: 32 KB ----
  reg [7:0] fram [0:32767];
  wire [14:0] ra = ma[14:0];
  assign cd = (!ram_ce_n && !ram_oe_n) ? fram[ra] : 8'bz;
  always @(posedge ram_we_n) if (!ram_ce_n) fram[ra] = cd;

  // ---- UART host side (1 Mbaud) ----
  task automatic u_send(input [7:0] b);
    integer k;
    begin
      urx = 0; #(CPB * 24);
      for (k = 0; k < 8; k = k + 1) begin urx = b[k]; #(CPB * 24); end
      urx = 1; #(CPB * 24);
    end
  endtask
  task automatic u_recv(output [7:0] b);
    integer k;
    begin
      @(negedge utx); #(CPB * 12);           // middle of the start bit
      for (k = 0; k < 8; k = k + 1) begin #(CPB * 24); b[k] = utx; end
      #(CPB * 24);
    end
  endtask
  task automatic u_cmd(input [7:0] op, input t, input [23:0] addr, input [15:0] n);
    begin
      u_send(op); u_send({7'd0, t}); u_send(addr[7:0]); u_send(addr[15:8]); u_send(addr[23:16]);
      u_send(n[7:0]); u_send(n[15:8]);
    end
  endtask

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
    wait (!usb); #200;  // the cart powers up in USB mode until the console-present debounce expires

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
    #3000;  // the flash is busy ~2 us; a real flasher polls Data# here
    check_read(16'h4321, 8'h42, "flash program in dev mode");
    if (flash[23'h180 * 16384 + 23'h0321] !== 8'h42) begin errors = errors + 1; $display("FAIL flash array"); end
    gb_write(16'h4000, 8'h01);  // in dev mode this goes to flash, not the RAM bank register
    if (dut.mapper.ram_bank !== 2'd3) begin errors = errors + 1; $display("FAIL RAM bank changed in dev mode"); end
    gb_write(16'h0000, 8'hD0);
    if (dev) begin errors = errors + 1; $display("FAIL dev mode not left on 0xD0"); end
    // reset clears everything
    nreset = 0; #100; nreset = 1; #100;
    check_read(16'h4000, 8'h01, "bank 1 after reset");

    // ===================== USB mode =====================
    begin : usb_tests
      reg [7:0] b; reg [8*8-1:0] id; integer k; reg [7:0] ack;
      fork
        begin for (k = 0; k < 8; k = k + 1) begin u_recv(b); id = {id[55:0], b}; end end
        u_send("I");
      join
      if (id !== "GBFPGA1\n") begin errors = errors + 1; $display("FAIL USB id in console mode: %s", id); end
      // console present: writes must be refused
      fork u_recv(ack); begin u_cmd("W", 0, 24'h000123, 1); u_send(8'h00); end join
      if (ack !== "C") begin errors = errors + 1; $display("FAIL USB write accepted with console present (%h)", ack); end
      cons = 0; #20000;  // pull the cart out
      if (!usb) begin errors = errors + 1; $display("FAIL usb_mode not entered"); end
      if (bus_oe_n !== 1'b1) begin errors = errors + 1; $display("FAIL transceiver on in USB mode"); end
      fork u_recv(b); u_send("M"); join
      if (b !== 8'h01) begin errors = errors + 1; $display("FAIL mode byte %h", b); end
      // AMD byte program of 0x5A at 0x123456 built from single-byte W commands
      fork u_recv(ack); begin u_cmd("W", 0, 24'h000AAA, 1); u_send(8'hAA); end join
      fork u_recv(ack); begin u_cmd("W", 0, 24'h000555, 1); u_send(8'h55); end join
      fork u_recv(ack); begin u_cmd("W", 0, 24'h000AAA, 1); u_send(8'hA0); end join
      fork u_recv(ack); begin u_cmd("W", 0, 24'h123456, 1); u_send(8'h5A); end join
      if (ack !== "K" || flash[23'h123456] !== 8'h5A) begin errors = errors + 1; $display("FAIL USB flash program (%h, %h)", ack, flash[23'h123456]); end
      // burst read 3 bytes of flash (bank N markers) and 4-byte F-RAM write + read
      fork
        begin u_recv(b); if (b !== 8'hFF) begin errors = errors + 1; $display("FAIL USB R0 %h", b); end
              u_recv(b); if (b !== 8'h5A) begin errors = errors + 1; $display("FAIL USB R1 %h", b); end
              u_recv(b); if (b !== 8'hFF) begin errors = errors + 1; $display("FAIL USB R2 %h", b); end end
        u_cmd("R", 0, 24'h123455, 3);
      join
      fork u_recv(ack); begin u_cmd("W", 1, 24'h007FFC, 4); u_send(8'h11); u_send(8'h22); u_send(8'h33); u_send(8'h44); end join
      if (fram[15'h7FFC] !== 8'h11 || fram[15'h7FFF] !== 8'h44) begin errors = errors + 1; $display("FAIL USB F-RAM write"); end
      fork
        begin u_recv(b); if (b !== 8'h33) begin errors = errors + 1; $display("FAIL USB F-RAM read %h", b); end end
        u_cmd("R", 1, 24'h007FFE, 1);
      join
      // 'P': 40 bytes from 0x0201F crossing a 32-byte page boundary -> 3 write-buffer pages
      begin : ptest
        reg [7:0] pd [0:39]; integer q;
        for (q = 0; q < 40; q = q + 1) pd[q] = 8'h80 ^ q[7:0] * 8'd7;
        fork
          u_recv(ack);
          begin u_cmd("P", 0, 24'h02001F, 40); for (q = 0; q < 40; q = q + 1) u_send(pd[q]); end
        join
        if (ack !== "K") begin errors = errors + 1; $display("FAIL USB P ack %h", ack); end
        if (busy_polls < 3) begin errors = errors + 1; $display("FAIL USB P never saw the flash busy (%0d polls)", busy_polls); end
        for (q = 0; q < 40; q = q + 1)
          if (flash[23'h02001F + q] !== pd[q]) begin errors = errors + 1; $display("FAIL USB P byte %0d: %h want %h", q, flash[23'h02001F + q], pd[q]); end
        if (flash[23'h02001E] !== 8'hFF || flash[23'h020047] !== 8'hFF) begin errors = errors + 1; $display("FAIL USB P wrote outside range"); end
      end
      cons = 1; #20000;
      if (usb) begin errors = errors + 1; $display("FAIL console mode not restored"); end
      check_read(16'h0000, 8'h00, "console mode after USB");
    end

    if (errors == 0) $display("PASS: all mapper checks");
    else $display("%0d FAILURES", errors);
    $finish;
  end
endmodule
