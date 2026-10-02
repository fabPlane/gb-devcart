// gbcart_mapper.v — GB DEVCART r2 mapper: MBC5 plus a locked "dev mode" for flash writes.
//
// Everything here is on the cart's 3.3 V side, behind the level shifters:
//   a[15:12], d[7:0], nwr, nrd, ncs, nreset come from the Game Boy bus (via 74LVC245s);
//   flash and F-RAM get bus A0-A13 straight from the shifters; this block drives only the high
//   address bits, the memory strobes and the data-bus transceiver (74LVC8T245) DIR/OE.
//
// Memory map (MBC5-compatible):
//   0000-1FFF W  RAM enable: low nibble 0xA enables F-RAM; writing 0xD0 also leaves dev mode
//   2000-2FFF W  ROM bank bits 7:0
//   3000-3FFF W  ROM bank bit 8              (9 bits -> 512 x 16 KB = 8 MB)
//   4000-5FFF W  RAM bank bits 1:0           (4 x 8 KB = 32 KB F-RAM)
//   6000-7FFF W  ignored by MBC5; the 4-byte sequence "GBDV" here enters dev mode
//   0000-3FFF R  ROM bank 0, 4000-7FFF R ROM bank N (bank 0 allowed, as on MBC5)
//   A000-BFFF RW F-RAM bank, only when RAM is enabled
// Dev mode: writes to 4000-7FFF are passed to the flash /WE (so JEDEC command sequences work
// through the switchable window) instead of updating the RAM bank register. A game cannot
// reach this by accident: it needs the exact unlock sequence and then the flash's own unlock.
module gbcart_mapper (
    input  wire       clk,       // free-running sample clock (>= 20 MHz), e.g. on-chip oscillator
    input  wire       nreset,    // cart /RESET from the console, active low
    input  wire [15:12] a,       // high address bits (A0-A11 only go to the memories)
    input  wire [7:0] d,         // data bus, cart side (read only for this block)
    input  wire       nwr,
    input  wire       nrd,
    input  wire       ncs,       // console /CS: asserted for A000-FDFF

    output wire [22:14] rom_a,   // flash A14-A22 (16 KB bank number)
    output wire       rom_ce_n,
    output wire       rom_oe_n,
    output wire       rom_we_n,
    output wire [14:13] ram_a,   // F-RAM A13-A14 (8 KB bank number)
    output wire       ram_ce_n,
    output wire       ram_oe_n,
    output wire       ram_we_n,
    output wire       bus_oe_n,  // 74LVC8T245 /OE: only talk on the console bus when addressed
    output wire       bus_dir,   // 74LVC8T245 DIR: 1 = cart -> console (reads), 0 = console -> cart

    output wire       dev_mode   // exposed for a status LED / test pad
);
  // ---- registers ----------------------------------------------------------------------------
  reg [8:0] rom_bank;
  reg [1:0] ram_bank;
  reg       ram_en;
  reg       dev;
  reg [1:0] unlock_step;

  // Synchronise /WR and keep a short history of address/data samples. The transceiver stops
  // driving the cart-side data bus as soon as the real /WR rises, so the values committed on the
  // (synchronised, ~2 clocks late) rising edge are the ones sampled 4 clocks earlier, while the
  // strobe was still low. At ~42 MHz that needs /WR low >= ~120 ns; consoles give 240 ns+.
  reg [2:0] nwr_s;
  reg [3:0] a_h [0:3];
  reg [7:0] d_h [0:3];
  wire       wr_rise = (nwr_s[2:1] == 2'b01);
  wire [3:0] wa = a_h[3];
  wire [7:0] wd = d_h[3];
  always @(posedge clk) begin
    nwr_s  <= {nwr_s[1:0], nwr};
    a_h[0] <= a;   a_h[1] <= a_h[0]; a_h[2] <= a_h[1]; a_h[3] <= a_h[2];
    d_h[0] <= d;   d_h[1] <= d_h[0]; d_h[2] <= d_h[1]; d_h[3] <= d_h[2];
  end

  localparam [31:0] UNLOCK = "GBDV";
  wire [7:0] unlock_byte = UNLOCK[31 - 8 * unlock_step -: 8];

  always @(posedge clk or negedge nreset) begin
    if (!nreset) begin
      rom_bank    <= 9'd1;
      ram_bank    <= 2'd0;
      ram_en      <= 1'b0;
      dev         <= 1'b0;
      unlock_step <= 2'd0;
    end else if (wr_rise && !wa[3]) begin  // writes to 0000-7FFF are mapper registers
      case (wa[3:1])
        3'b000: begin  // 0000-1FFF
          ram_en <= (wd[3:0] == 4'hA);
          if (wd == 8'hD0) dev <= 1'b0;
        end
        3'b001: begin  // 2000-3FFF
          if (!wa[0]) rom_bank[7:0] <= wd;
          else        rom_bank[8]   <= wd[0];
        end
        3'b010: if (!dev) ram_bank <= wd[1:0];  // 4000-5FFF
        3'b011: if (!dev) begin                 // 6000-7FFF: dev-mode unlock sequence
          if (wd == unlock_byte) begin
            if (unlock_step == 2'd3) begin
              dev         <= 1'b1;
              unlock_step <= 2'd0;
            end else begin
              unlock_step <= unlock_step + 2'd1;
            end
          end else begin
            unlock_step <= (wd == UNLOCK[31:24]) ? 2'd1 : 2'd0;
          end
        end
        default: ;
      endcase
    end
  end
  assign dev_mode = dev;

  // ---- combinational decode (must be fast: the memories see these directly) ---------------
  wire a15 = a[15], a14 = a[14], a13 = a[13];
  wire rom_sel = !a15;                       // 0000-7FFF
  wire ram_sel = !ncs && !a14 && a13;        // A000-BFFF (/CS covers A000-FDFF)

  assign rom_a    = a14 ? rom_bank : 9'd0;
  // /CE and /OE need no logic: on the board they are wired straight to A15 and /RD.
  assign rom_ce_n = a15;
  assign rom_oe_n = nrd;
  assign rom_we_n = !(dev && rom_sel && a14 && !nwr);

  assign ram_a    = ram_bank;
  assign ram_ce_n = !(ram_sel && ram_en);
  assign ram_oe_n = nrd;  // wired straight to /RD on the board
  assign ram_we_n = nwr;  // wired straight to /WR on the board

  // Drive the console data bus only while the console reads from us; open it inward for any
  // write to cart space so register writes and flash/F-RAM writes reach this side.
  wire cart_read  = !nrd && nwr && (rom_sel || (ram_sel && ram_en));
  wire cart_write = !nwr && (rom_sel || ram_sel);
  assign bus_dir  = cart_read;
  assign bus_oe_n = !(cart_read || cart_write);
endmodule
