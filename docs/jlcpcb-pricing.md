# JLCPCB pricing: GB DEVCART r1.1 and r2.1

Snapshot taken **2026-10-02**. USD, before shipping, tax and coupons. Tags:
**[Q]** live JLCPCB quote engine (`cart.jlcpcb.com`, the endpoint the quote page uses);
**[P]** live JLCPCB parts library API; **[F]** JLCPCB's published assembly fee table (help page
"PCB Assembly Cost", 2026-09-09); **[E]** estimate. Prices change, so the real cart decides.

Regenerate: `python3 scripts/jlc_check.py [BOARD_DIR]` (stock, library, prices: writes
`exports/jlcpcb/parts_check.json`), then `python3 scripts/jlc_cost.py …` (writes `cost_estimate.json`).

## Summary

| | r1.1 (parallel flash, 2 layers) | r2.1 (FPGA + USB-C, 4 layers) |
|---|---|---|
| Board | 51.4 × 61 mm, 1.0 mm, ENIG | 51.4 × 61 mm, 1.0 mm, ENIG, 4 layers |
| Parts in JLC's library | 9 / 9 lines, all in stock | 21 / 21 lines, all in stock |
| Unique parts (Extended) | 9 (5) | 21 (11) |
| Solder joints per board | 148 SMT | 423 SMT + 4 THT (USB-C shell legs) |
| **5 boards, assembled** | **≈ $130** ($25.99/board) | **≈ $284** ($56.73/board, Standard) |
| **10 boards, assembled** | **≈ $216** ($21.59/board) | **≈ $443** ($44.28/board, Standard) |
| Most expensive part | FM18W08 F-RAM $9.58 | GW1N-LV4 FPGA $15.79, FM28V020 F-RAM $10.39 |

All part numbers in both BOMs match the design's MPNs, and every line has enough stock for 10 boards.

## r1.1

Bare PCB, 2 layers, 51.4 × 61 mm, 1.0 mm [Q]:

| Finish | 5 | 10 | 30 | 100 |
|---|---|---|---|---|
| HASL (leaded) | $2.00 | $5.00 | $11.50 | $42.80 |
| **ENIG** (recommended for the fingers) | $18.60 | $21.60 | $30.00 | $65.50 |

Parts [P]:

| LCSC | Refs | Package | Library | Stock (2026-10-02) | $/unit at 5 boards |
|---|---|---|---|---|---|
| C14663 | C1, C2, C3, C4, C5, C6 | 0603 | Basic | 54,190,290 | 0.0123 |
| C13585 | C7 | 1206 | Basic | 2,393,834 | 0.2655 |
| C25804 | R1 | 0603 | Basic | 23,046,124 | 0.0018 |
| C4190 | R2, R3, R4, R5, R6 | 0603 | Basic | 7,595,099 | 0.0018 |
| C632847 | U1 | PLCC-32(11.4x14) | Extended | 17 | 5.4574 |
| C55945 | U2 | SOIC-28-300mil | Extended | 45 | 9.5768 |
| C10097 | U3 | SOIC-20-300mil | Extended | 9,077 | 0.5251 |
| C6838 | U4, U5 | SOIC-14 | Extended | 23,625 | 0.2499 |
| C10090 | U6 | SOIC-14 | Extended | 90,183 | 0.1244 |

Order estimate (PCB + parts + assembly fees [F]):

| Boards | Bare PCB (ENIG) [Q] | Parts [P] | **Total, Economic PCBA** | Total, Standard PCBA |
|---|---|---|---|---|
| 5 | $18.60 | $83.90 | **$129.96** ($25.99/board) | $152.44 ($30.49/board) |
| 10 | $21.60 | $164.39 | **$215.85** ($21.59/board) | $238.33 ($23.83/board) |
| 30 | $30.00 | $484.75 | **$554.21** ($18.47/board) | $576.69 ($19.22/board) |
| 100 | $65.50 | $1585.09 | **$1723.65** ($17.24/board) | $1746.13 ($17.46/board) |

- **Stock limit:** only 17 SST39SF040-55 flash chips (C632847) and 45 FM18W08 F-RAMs (C55945) are in
  stock. That covers 10 boards; 30+ boards need JLC Global Sourcing or a pre-order (the 30/100 rows assume list price) [E].
- The board is now ≥ 50 mm on both sides, so JLC's bevelled gold-finger option is allowed.

## r2.1

Bare PCB, 4 layers, 51.4 × 61 mm, 1.0 mm [Q] (JLC's default 4-layer stack-up):

| Finish | 5 | 10 | 30 | 100 |
|---|---|---|---|---|
| HASL (leaded) | $8.00 | $14.00 | $35.10 | $51.70 |
| **ENIG** (recommended for the fingers) | $24.60 | $30.60 | $53.20 | $73.50 |

Parts [P]:

| LCSC | Refs | Package | Library | Stock (2026-10-02) | $/unit at 5 boards |
|---|---|---|---|---|---|
| C19702 | C10, C11, C15 | 0603 | Basic | 10,368,144 | 0.0319 |
| C15849 | C12, C13, C14 | 0603 | Basic | 6,260,435 | 0.0168 |
| C14663 | C1, C2, C3, C4, C5, C6, C7, C8, C9, C16, C17, C18, C19, C20, C21, C22, C23, C24, C27 | 0603 | Basic | 54,190,290 | 0.0123 |
| C1653 | C25, C26 | 0603 | Basic | 2,751,038 | 0.0058 |
| C8598 | D1, D2 | SOD-123 | Basic | 509,945 | 0.0280 |
| C165948 | J2 | SMD | Extended | 436,456 | 0.1857 |
| C25804 | R1, R2, R7, R9, R10, R11, R12, R13, R14, R15, R16 | 0603 | Basic | 23,046,124 | 0.0018 |
| C23186 | R17, R18 | 0603 | Basic | 25,270,096 | 0.0015 |
| C21190 | R3, R4 | 0603 | Basic | 21,643,642 | 0.0026 |
| C23162 | R5, R6, R8 | 0603 | Basic | 22,449,325 | 0.0028 |
| C31900351 | U1 | QFN-88 | Extended | 112 | 15.7949 |
| C18221627 | U10 | QFN-28(4X4) | Extended | 5,472 | 3.2400 |
| C7519 | U11 | SOT-23-6L | Extended | 34,765 | 0.1767 |
| C117907 | U2 | TSOP-48-18.4mm | Extended | 108 | 3.3749 |
| C54935 | U3 | SOIC-28-300mil | Extended | 1,000 | 10.3945 |
| C352976 | U4, U5, U6 | TSSOP-20 | Extended | 4,375 | 0.5593 |
| C27643 | U7 | TSSOP-24 | Extended | 57,632 | 0.3479 |
| C5446 | U8 | SOT-23-3L | Basic | 472,796 | 0.1426 |
| C236672 | U9 | SOT-23-5 | Extended | 10,931 | 0.0620 |
| C7434936 | X1 | SMD2520-4P | Extended | 6,005 | 0.5788 |
| C367183 | Y1 | SMD3225-4P | Extended | 10,992 | 0.3363 |

Order estimate:

| Boards | Bare PCB (ENIG) [Q] | Parts [P] | **Total, Economic PCBA** | Total, Standard PCBA |
|---|---|---|---|---|
| 5 | $24.60 | $185.90 | **$257.37** ($51.47/board) | $283.63 ($56.73/board) |
| 10 | $30.60 | $335.30 | **$416.14** ($41.61/board) | $442.76 ($44.28/board) |
| 30 | $53.20 | $890.15 | **$1007.13** ($33.57/board) | $1035.13 ($34.50/board) |
| 100 | $73.50 | $2663.20 | **$2847.86** ($28.48/board) | $2880.70 ($28.81/board) |

- **Use Standard PCBA.** The USB-C receptacle has 4 through-hole shell legs, which need hand
  soldering, and the FPGA is a 0.4 mm-pitch QFN-88. The Economic rows are shown for comparison; JLC may
  route the order to Standard anyway. The THT fee is an estimate [E].
- **0.1 mm clearance:** the QFN-88 pads are 0.1 mm apart, so the board uses 0.1 mm clearance and
  0.1 mm neck-downs. JLC's 4-layer process allows 0.09 mm; check the price after uploading the gerbers,
  in case the quote page adds a fine-trace charge [E].
- The FPGA (C31900351, 112 in stock) and flash (C117907, 108 in stock) limit a single order to about 100 boards.
- The FPGA needs its bitstream after assembly: load it over USB with `openFPGALoader -c ch347_jtag`
  (see `programmer/README.md`).

## How to order

1. Bare PCB: upload `exports/jlcpcb/gerbers.zip` (r1.1) or `r2/board/exports/jlcpcb/gerbers.zip` (r2.1)
   at jlcpcb.com. Set **thickness 1.0 mm** and **ENIG** (or gold fingers with a 30° bevel); r2.1 is
   detected as 4 layers.
2. Assembly: turn on PCB Assembly, top side. Upload `bom.csv` and `cpl.csv` from the same folder. Pick
   Standard for r2.1.
3. Check the rotation preview: SOIC, PLCC, TSOP and QFN reels sometimes need ±90°/180°, and check pin 1.
   Leave J1 (edge fingers) and TP1–TP6 (test pads) unplaced; they are not in the BOM.

## Shipping (all [E] unless noted)

| Destination | Global Standard Direct (economy, DDP) | DHL Express |
|---|---|---|
| USA, bare PCBs 5-30 pcs | ~$12-13 incl. prepaid tariff (forum report, 2026-03-19: "$10 boards + ~$2 tax + ~$12 shipping") | ~$35-45 (forum report, 2026-03-06: "$5 of PCBs for $45" by DHL) |
| USA, PCBA or 100 pcs (~0.7-1 kg) | ~$18-30 [E] | ~$40-60 [E] |
| Thailand, bare PCBs | ~$6-12 [E] | ~$20-30 [E] |
| Thailand, PCBA or 100 pcs | ~$12-20 [E] | ~$30-45 [E] |

- For US orders, choose the DDP or "Global Standard Direct Line" option so the tariff is prepaid. Express (DAP) can bring a broker or duty bill on delivery.
- Thailand charges 7% VAT on low-value imports (since 2024), which may be collected at checkout or on delivery [E].

## Cartridge shell (separate line)

| Item | Price | Source / date |
|---|---|---|
| Generic DMG-style cart shell (AliExpress bulk, 10-50 pack) | ~$0.30-2.00 each [E] | gbstudiocentral.com cart-shell guide: "10 cents to 3 bucks"; date not shown |
| Quality shell (Retro Modding) | $3.99 each; 12-colour pack $44.99 | same guide |
| Gamebit 3.8 mm screw / driver | ~$0.10 per screw, ~$3 driver [E] | AliExpress listings |

r1.1 and r2.1 use the standard DMG board outline, so any DMG-style shell fits (`mech/fit.html`). r2.1 needs the printed USB-C shell from `mech/`, or a shell cut open over the connector.

## Sources
- JLCPCB quote engine (cart.jlcpcb.com) and parts API (jlcpcb.com), queried 2026-10-01.
- JLCPCB help: "PCB Assembly Cost" (2026-09-09); "In what cases will there be charged extra?" (2026-09-09, ENIG >30% area surcharge); "JLCPCB gold fingers" (2026-09-18).
- JLCPCB news: "Free OSP Surface Finish" (2026-07-30).
- JLC part page C632847 (assembly type, MSL3).
- allaboutcircuits.com thread "JLCPCB Global Standard Direct Line Shipping" (2026-03-06 to 2026-03-19).
- gbstudiocentral.com "GB Game Cartridge Shells".
