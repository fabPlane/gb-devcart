// usb_engine.v — UART command engine for GB DEVCART r2 USB mode (no console present).
// The USB bridge's UART talks to this block, which drives the flash / F-RAM directly.
//
// Protocol (host -> cart, little endian; t = target: 0 flash, 1 F-RAM):
//   'I'                         -> "GBFPGA1\n"
//   'M'                         -> 1 byte: bit0 = USB mode (no console), bit1 = dev mode
//   'R' t a24 n16               -> n bytes read, sequential addresses
//   'W' t a24 n16 data[n]       -> 'K' after n sequential write strobes
//   'P' 0 a24 n16 data[n<=256]  -> 'K' | 'T' (timeout) | 'F' (flash reported failure, DQ5/DQ1):
//                                  programs flash with the AMD write-buffer sequence, 32-byte
//                                  pages, Data# polling done here. Program erased flash only.
// With a console present every R/W/P answers 'C' (R first returns n x 0xFF) and touches nothing.
module uart_rx #(parameter CLKS_PER_BIT = 42) (
    input wire clk, input wire rx, output reg valid = 1'b0, output reg [7:0] data = 8'h00);
  reg [2:0] rx_s = 3'b111;
  reg [15:0] cnt = 0;
  reg [3:0] bitn = 0;
  reg busy = 0;
  always @(posedge clk) begin
    rx_s  <= {rx_s[1:0], rx};
    valid <= 1'b0;
    if (!busy) begin
      if (!rx_s[2]) begin busy <= 1'b1; cnt <= CLKS_PER_BIT / 2; bitn <= 0; end
    end else if (cnt == CLKS_PER_BIT - 1) begin
      cnt <= 0;
      bitn <= bitn + 1'b1;
      if (bitn == 0) begin
        if (rx_s[2]) busy <= 1'b0;                 // false start bit
      end else if (bitn <= 8) begin
        data <= {rx_s[2], data[7:1]};
      end else begin
        busy <= 1'b0;
        valid <= rx_s[2];                         // stop bit must be high
      end
    end else begin
      cnt <= cnt + 1'b1;
    end
  end
endmodule

module uart_tx #(parameter CLKS_PER_BIT = 42) (
    input wire clk, input wire start, input wire [7:0] data, output reg tx = 1'b1, output wire busy);
  // start bit is driven on the start cycle; then 8 data bits, stop, and one extra stop-length
  // bit time so busy covers the whole stop bit before the next byte may start
  reg [9:0] sh = 10'h3FF;
  reg [15:0] cnt = 0;
  reg [3:0] left = 0;
  assign busy = (left != 0);
  always @(posedge clk) begin
    if (!busy) begin
      if (start) begin sh <= {2'b11, data}; tx <= 1'b0; left <= 4'd10; cnt <= 0; end
    end else if (cnt == CLKS_PER_BIT - 1) begin
      cnt <= 0; tx <= sh[0]; sh <= {1'b1, sh[9:1]}; left <= left - 1'b1;
    end else begin
      cnt <= cnt + 1'b1;
    end
  end
endmodule

module usb_engine #(
    parameter CLKS_PER_BIT = 42,
    parameter STROBE_CLKS  = 5,        // 5 x 24 ns = 120 ns strobes (flash tACC 90 ns, tWP 35 ns)
    parameter POLL_TIMEOUT = 100000    // polls per 32-byte page before giving up (~0.3 s)
) (
    input  wire        clk,
    input  wire        usb_mode,
    input  wire        dev_mode,
    input  wire        rx,
    output wire        tx,
    input  wire [7:0]  cd_in,
    output reg  [7:0]  cd_out = 8'h00,
    output reg         cd_oe = 1'b0,
    output reg  [22:0] ma = 23'd0,
    output reg         rom_ce_n = 1'b1, output reg rom_oe_n = 1'b1, output reg rom_we_n = 1'b1,
    output reg         ram_ce_n = 1'b1, output reg ram_oe_n = 1'b1, output reg ram_we_n = 1'b1
);
  wire rx_valid; wire [7:0] rx_data;
  uart_rx #(CLKS_PER_BIT) urx (.clk(clk), .rx(rx), .valid(rx_valid), .data(rx_data));
  reg tx_start = 1'b0; reg [7:0] tx_data = 8'h00; wire tx_busy;
  uart_tx #(CLKS_PER_BIT) utx (.clk(clk), .start(tx_start), .data(tx_data), .tx(tx), .busy(tx_busy));

  // ---- bus-cycle sequencer: one read or write strobe on the memory side ---------------------
  reg        bop_go = 1'b0, bop_wr = 1'b0, bop_t = 1'b0;
  reg [22:0] bop_a = 23'd0;
  reg [7:0]  bop_d = 8'h00, bop_q = 8'h00;
  reg        bop_busy = 1'b0, bop_done = 1'b0;
  reg [4:0]  bph = 5'd0;
  always @(posedge clk) begin
    bop_done <= 1'b0;
    if (!bop_busy) begin
      if (bop_go) begin bop_busy <= 1'b1; bph <= 5'd0; ma <= bop_a; cd_out <= bop_d; end
    end else if (!usb_mode) begin           // console came back mid-cycle: release everything
      cd_oe <= 1'b0; rom_ce_n <= 1'b1; rom_oe_n <= 1'b1; rom_we_n <= 1'b1;
      ram_ce_n <= 1'b1; ram_oe_n <= 1'b1; ram_we_n <= 1'b1;
      bop_q <= 8'hFF; bop_busy <= 1'b0; bop_done <= 1'b1;
    end else begin
      bph <= bph + 1'b1;
      if (bop_wr) begin
        if (bph == 0) cd_oe <= 1'b1;                                  // address + data setup
        if (bph == 1) begin
          if (bop_t) begin ram_ce_n <= 1'b0; ram_we_n <= 1'b0; end
          else       begin rom_ce_n <= 1'b0; rom_we_n <= 1'b0; end
        end
        if (bph == STROBE_CLKS + 1) begin rom_we_n <= 1'b1; ram_we_n <= 1'b1; end   // data latched here
        if (bph == STROBE_CLKS + 2) begin rom_ce_n <= 1'b1; ram_ce_n <= 1'b1; end   // /CE after /WE
        if (bph == STROBE_CLKS + 3) begin cd_oe <= 1'b0; bop_busy <= 1'b0; bop_done <= 1'b1; end
      end else begin
        if (bph == 0) begin
          if (bop_t) begin ram_ce_n <= 1'b0; ram_oe_n <= 1'b0; end
          else       begin rom_ce_n <= 1'b0; rom_oe_n <= 1'b0; end
        end
        if (bph == STROBE_CLKS + 1) begin
          bop_q <= cd_in;
          rom_ce_n <= 1'b1; rom_oe_n <= 1'b1; ram_ce_n <= 1'b1; ram_oe_n <= 1'b1;
        end
        if (bph == STROBE_CLKS + 2) begin bop_busy <= 1'b0; bop_done <= 1'b1; end
      end
    end
  end

  // ---- command FSM ---------------------------------------------------------------------------
  localparam S_OP = 0, S_ARGS = 1, S_R_GO = 2, S_R_WAIT = 3, S_R_TX = 4, S_W_RX = 5, S_W_WAIT = 6,
             S_P_RX = 7, S_P_PAGE = 8, S_P_GO = 9, S_P_WAIT = 10, S_P_POLL = 11, S_P_PWAIT = 12,
             S_ACK = 13, S_MSG = 14, S_P_FETCH = 15;
  reg [3:0]  st = S_OP;
  reg [7:0]  op = 8'h00;
  reg [2:0]  argn = 3'd0;
  reg        tgt = 1'b0;
  reg [22:0] addr = 23'd0;
  reg [15:0] n = 16'd0;
  reg [7:0]  ack = 8'h00;
  reg [63:0] msg = 64'd0;
  reg [3:0]  msg_len = 4'd0, msg_i = 4'd0;

  // write-buffer programming state
  (* ram_style = "block" *) reg [7:0] pbuf [0:255];  // BSRAM (sync read via pdata)
  reg [8:0]  fill = 9'd0;       // bytes received into pbuf
  reg [8:0]  bi = 9'd0;         // first buffer index of the current page
  reg [5:0]  cnt = 6'd0;        // bytes in the current page (1..32)
  reg [6:0]  k = 7'd0;          // step within the page sequence
  reg [16:0] polls = 17'd0;
  reg [7:0]  last = 8'h00;      // last byte of the page, for Data# polling
  reg [7:0]  pdata = 8'h00;     // registered pbuf read (keeps pbuf in block RAM)
  wire       console = !usb_mode;
  wire [8:0] page_room = 9'd32 - {4'd0, addr[4:0]};
  wire [8:0] remaining = fill - bi;

  // one step of the page sequence: unlock, 0x25 + count, the data, 0x29 confirm
  reg [22:0] seq_a; reg [7:0] seq_d;
  always @(*) begin
    seq_a = addr; seq_d = 8'h00;
    if (k == 0)                   begin seq_a = 23'h000AAA; seq_d = 8'hAA; end
    else if (k == 1)              begin seq_a = 23'h000555; seq_d = 8'h55; end
    else if (k == 2)              begin seq_a = addr;       seq_d = 8'h25; end
    else if (k == 3)              begin seq_a = addr;       seq_d = {2'b00, cnt} - 8'd1; end
    else if (k < {1'b0, cnt} + 4) begin seq_a = addr + (k - 7'd4); seq_d = pdata; end
    else                          begin seq_a = addr;       seq_d = 8'h29; end
  end

  always @(posedge clk) begin
    tx_start <= 1'b0;
    bop_go   <= 1'b0;
    case (st)
      S_OP: if (rx_valid) begin
        op <= rx_data; argn <= 3'd0;
        case (rx_data)
          "I": begin msg <= "GBFPGA1\n"; msg_len <= 4'd8; msg_i <= 4'd0; st <= S_MSG; end
          "M": begin ack <= {6'd0, dev_mode, usb_mode}; st <= S_ACK; end
          "R", "W", "P": st <= S_ARGS;
          default: ;
        endcase
      end
      S_ARGS: if (rx_valid) begin
        case (argn)
          3'd0: tgt <= rx_data[0];
          3'd1: addr[7:0] <= rx_data;
          3'd2: addr[15:8] <= rx_data;
          3'd3: addr[22:16] <= rx_data[6:0];
          3'd4: n[7:0] <= rx_data;
          default: n[15:8] <= rx_data;
        endcase
        argn <= argn + 1'b1;
        if (argn == 3'd5) begin
          fill <= 9'd0; bi <= 9'd0;
          if ({rx_data, n[7:0]} == 16'd0) begin
            ack <= console ? "C" : "K";
            st <= (op == "R") ? S_OP : S_ACK;
          end else case (op)
            "R": st <= S_R_GO;
            "W": st <= S_W_RX;
            default: st <= S_P_RX;
          endcase
        end
      end
      // ---- R: read n bytes ----
      S_R_GO: if (!bop_busy) begin
        bop_a <= addr; bop_wr <= 1'b0; bop_t <= tgt; bop_go <= !console; st <= S_R_WAIT;
      end
      S_R_WAIT: if (bop_done || console) st <= S_R_TX;
      S_R_TX: if (!tx_busy && !tx_start) begin
        tx_data <= console ? 8'hFF : bop_q; tx_start <= 1'b1;
        addr <= addr + 1'b1; n <= n - 1'b1;
        st <= (n == 16'd1) ? S_OP : S_R_GO;
      end
      // ---- W: n raw write strobes ----
      S_W_RX: if (rx_valid) begin
        bop_a <= addr; bop_d <= rx_data; bop_wr <= 1'b1; bop_t <= tgt; bop_go <= !console;
        st <= S_W_WAIT;
      end
      S_W_WAIT: if (bop_done || console) begin
        addr <= addr + 1'b1; n <= n - 1'b1;
        if (n == 16'd1) begin ack <= console ? "C" : "K"; st <= S_ACK; end
        else st <= S_W_RX;
      end
      // ---- P: buffer n bytes, then program them page by page ----
      S_P_RX: if (rx_valid) begin
        pbuf[fill[7:0]] <= rx_data;
        fill <= fill + 1'b1;
        if (fill + 1'b1 == n[8:0] || fill == 9'd255) begin
          if (console) begin ack <= "C"; st <= S_ACK; end
          else st <= S_P_PAGE;
        end
      end
      S_P_PAGE: begin  // page = up to the next 32-byte boundary
        if (bi == fill) begin ack <= "K"; st <= S_ACK; end
        else begin
          cnt <= (page_room < remaining) ? page_room[5:0] : remaining[5:0];
          k <= 7'd0; polls <= 17'd0;
          st <= S_P_FETCH;
        end
      end
      S_P_FETCH: begin  // synchronous buffer read for the data steps (k = 4 .. cnt+3)
        pdata <= pbuf[bi[7:0] + (k - 7'd4)];
        st <= S_P_GO;
      end
      S_P_GO: if (!bop_busy) begin
        bop_a <= seq_a; bop_d <= seq_d; bop_wr <= 1'b1; bop_t <= 1'b0; bop_go <= 1'b1;
        if (k == {1'b0, cnt} + 3) last <= seq_d;
        st <= S_P_WAIT;
      end
      S_P_WAIT: if (bop_done) begin
        if (console) begin ack <= "C"; st <= S_ACK; end
        else if (k == {1'b0, cnt} + 4) st <= S_P_POLL;    // 0x29 written: poll
        else begin k <= k + 1'b1; st <= S_P_FETCH; end
      end
      S_P_POLL: if (!bop_busy) begin
        bop_a <= addr + cnt - 1'b1; bop_wr <= 1'b0; bop_t <= 1'b0; bop_go <= 1'b1;
        polls <= polls + 1'b1;
        st <= S_P_PWAIT;
      end
      S_P_PWAIT: if (bop_done) begin
        if (bop_q[7] == last[7]) begin                    // Data# polling: done
          addr <= addr + cnt; bi <= bi + cnt; st <= S_P_PAGE;
        end else if (bop_q[5] || bop_q[1]) begin          // exceeded timing / write-buffer abort
          ack <= "F"; st <= S_ACK;
        end else if (console || polls == POLL_TIMEOUT[16:0]) begin
          ack <= console ? "C" : "T"; st <= S_ACK;
        end else st <= S_P_POLL;
      end
      // ---- replies ----
      S_ACK: if (!tx_busy && !tx_start) begin tx_data <= ack; tx_start <= 1'b1; st <= S_OP; end
      S_MSG: if (!tx_busy && !tx_start) begin
        if (msg_i == msg_len) st <= S_OP;
        else begin tx_data <= msg[63 - 8 * msg_i -: 8]; tx_start <= 1'b1; msg_i <= msg_i + 1'b1; end
      end
      default: st <= S_OP;
    endcase
  end
endmodule
