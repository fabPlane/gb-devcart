# JLCPCB pricing: GB dev cart (56.0 x 49.5 mm, 2-layer)

Snapshot taken **2026-10-01**. Prices are USD and exclude tax, shipping and coupons unless a row says otherwise.
Each figure is tagged with its source and date:

- **[Q]** = live JLCPCB quote engine (`cart.jlcpcb.com` price calc, the same endpoint the quote page uses), queried 2026-10-01.
- **[P]** = JLCPCB/LCSC parts library API (`jlcpcb.com/api/.../selectSmtComponentList`), queried 2026-10-01.
- **[F]** = JLCPCB help page "PCB Assembly Cost" (last updated 2026-09-09).
- **[E]** = an estimate. Check it in the real cart before ordering.

## 1. Bare PCB (2L FR-4, 1 oz, 0.25 mm track / 0.3 mm via = standard, no surcharge) [Q]

Order total in USD. Green and black soldermask cost the same, and 1.0 mm and 1.6 mm cost the same.

| Finish | 5 pcs | 10 pcs | 30 pcs | 100 pcs |
|---|---|---|---|---|
| HASL (leaded) / OSP | 2.00 | 5.00 | 10.70 / 11.00 | 40.70 / 42.00 |
| **HASL lead-free** (cheapest RoHS baseline) | 3.10 | 6.10 | 12.10 | 47.00 |
| **ENIG 1u"** (recommended) | **18.60** | **21.60** | **28.90** | **62.70** |
| ENIG 2u" gold | 35.48 | 38.83 | 47.50 | 86.12 |
| ENIG + "Gold fingers" 30°/45° bevel | ~25-35 [E] | ~30-40 [E] | ~40 [E] | ~75-80 [E] |

- The ENIG upcharge is a flat **$16.60** per order at these sizes. At 5 and 10 pcs the base price is the $2 or $5 promo price. From 30 pcs up the order is priced normally: base plus an engineering fee of $8.30 at 30 pcs and $18.40 at 100 pcs [Q].
- Since **2026-07-30** the free prototype finish is **OSP**. ENIG is no longer free (JLCPCB news, "Free OSP Surface Finish").
- Gold-finger bevel: the quote engine did not change the price for the `goldFingerBevel` field. Third-party guides put the add-on at about $10-20 per prototype order [E].
- **Size problem:** JLC's gold-finger rules (help article, updated 2026-09-18) say a board or panel with gold fingers must be **at least 50 mm on both sides**, and the bevel angle is 30° or 45° (30° recommended). At **49.5 mm** this board is under the limit. Either widen the board to 50 mm or order a panel, otherwise the bevel or gold-finger option may be refused. Plain ENIG with no bevel still gives the fingers gold.
- Board weight [Q]: 0.04 kg for 5 pcs and 0.63 kg for 100 pcs at 1.0 mm (0.93 kg at 1.6 mm). Build time is 72 h for 5-30 pcs, or 24 h for +$7.60. At 100 pcs it is about 5 days.

## 2. BOM: LCSC / JLC parts library [P] (stock and unit price on 2026-10-01)

| Ref | Part (LCSC #) | Lib | Stock | $/u @10 | $/u @100 | Notes |
|---|---|---|---|---|---|---|
| U1 | SST39SF040-70-4C-NHE **C645936** | Ext | **0** | 3.95 | 2.93 | Exact part, PLCC-32, out of stock |
| U1 alt | SST39SF040-55-4I-NHE-T **C632847** | Ext | **17** | 5.33 | 5.16 | Same die, faster/industrial, drop-in. Enough for 5 or 10 boards |
| U1 alt | SST39SF040-55-4C-NHE-T C632846 | Ext | 3 | 5.23 | 5.06 | Drop-in, too few in stock |
| U1 (no) | SST39SF040-70-4C-TU C43083883 | Ext | 55 | 4.85 | 4.00 | TSOP-32: needs a new footprint |
| U2 | FM18W08-SG C466863 / C1348737 | Ext | **0** | 18.04 | 18.04 | Exact part, out of stock |
| U2 alt | **FM18W08-SGTR C55945** | Ext | **45** | 9.58 | 9.58 | Same part on tape-and-reel. Covers 5/10/30 boards |
| U3 | **SN74HC574DWR C10097** | Ext | 9,077 | 0.44 | 0.35 | (Nexperia 74HC574D,653 C16501: 48k stock, 0.32/0.25) |
| U4,U5 | **SN74HC32DR C6838** (x2) | Ext | 23,625 | 0.25 | 0.21 | |
| U6 | **SN74HC00DR C10090** | Ext | 91,193 | 0.12 | 0.10 | |
| C1-C6 | 100nF 0603 X7R 50V **C14663** | **Basic** | 54M | 0.012 | 0.012 | |
| C7 | 10uF 1206 X5R 50V **C13585** | **Basic** | 2.4M | 0.27 | 0.20 | |
| R1 | 10k 0603 1% **C25804** | **Basic** | 23M | 0.002 | 0.002 | |
| R2-R6 | 2.2k 0603 1% **C4190** | **Basic** | 7.6M | 0.002 | 0.002 | |

- **PLCC-32 can be assembled:** the JLC part page for C632847 lists "SMT Assembly", Economic and Standard, MSL3. No hand soldering is needed.
- At **30 or 100 boards** U1 has to come through JLC Global Sourcing or a parts pre-order (the C645936 list price is used below), or you consign the parts yourself. U2 at 100 also needs about 55 more units from Global Sourcing. Global Sourcing price and lead time are [E]. DigiKey/Mouser pricing for FM18W08-SG may be higher than $9.58.
- **No FM18W08 F-RAM alternative is stocked.** FM16W08 (8 KB, same pinout) is out of stock in every listing. The usual 62256 SRAM fallback (IS62C256AL-45ULI-TR **C14323**, 2,850 stock, $4.23/$3.38) has the same pinout but a **330 mil SOP body, not 300 mil**, and needs a battery and CE-gating circuit. It is not a drop-in.
- No other 5 V 512 KB PLCC-32 NOR flash is stocked: MX29F040, AM29F040B and M29F040B all show 0. SST39SF010A (128 KB, C632838, 22 stock) is pin-compatible but smaller.
- **Unique Extended parts: 5** (U1, U2, U3, U4/5, U6). **Unique Basic parts: 4.** **Joints per board: 148.**

## 3. Assembly fees [F] (single side, top)

| Fee | Economic | Standard |
|---|---|---|
| Setup / engineering | $8.18 | $25.56 |
| Stencil | $1.53 | $8.21 |
| Part loading | $3.07 x 5 Extended = **$15.35** (Basic free) | $1.53 x 9 unique = **$13.77** |
| **Fixed per order** | **$25.06** | **$47.54** |
| SMT joints | 148 x $0.0016 = $0.24/board, minimum **$0.48/board** surcharge | same |

## 4. Summary: cost per board, USD, before shipping

The assembly rows include the ENIG 1.0 mm PCB plus parts (list prices from section 2) plus the fees from section 3. They do not include the bevel.

| Option | 5 | 10 | 30 | 100 |
|---|---|---|---|---|
| (a) Bare PCB, HASL lead-free [Q] | 0.62 | 0.61 | 0.40 | 0.47 |
| **(a) Bare PCB, ENIG** [Q] | **3.72** | **2.16** | **0.96** | **0.63** |
| Parts only (BOM, section 2) [P] | 16.53 | 16.32 | 14.27* | 13.61* |
| **(b) PCB + Economic PCBA** | **25.75** | **21.46** | **16.55*** | **14.97*** |
| (b) PCB + Standard PCBA | 30.24 | 23.71 | 17.30* | 15.20* |
| Order total, Economic | $129 | $215 | $496* | $1,497* |

\* This figure assumes U1 (and U2 at 100) can be bought through Global Sourcing at about list price [E]. Add **$0.6-1.6/board** if you stay on the stocked SST39SF040-55 at $5.2. U2 (the $9.58 F-RAM) is about 60-65% of the cost of an assembled board.

## 5. Shipping (all [E] unless noted)

| Destination | Global Standard Direct (economy, DDP) | DHL Express |
|---|---|---|
| USA, bare PCBs 5-30 pcs | ~$12-13 incl. prepaid tariff (forum report, 2026-03-19: "$10 boards + ~$2 tax + ~$12 shipping") | ~$35-45 (forum report, 2026-03-06: "$5 of PCBs for $45" by DHL) |
| USA, PCBA or 100 pcs (~0.7-1 kg) | ~$18-30 [E] | ~$40-60 [E] |
| Thailand, bare PCBs | ~$6-12 [E] | ~$20-30 [E] |
| Thailand, PCBA or 100 pcs | ~$12-20 [E] | ~$30-45 [E] |

- For US orders, choose the DDP or "Global Standard Direct Line" option so the tariff is prepaid. Express (DAP) can bring a broker or duty bill on delivery.
- Thailand charges 7% VAT on low-value imports (since 2024), which may be collected at checkout or on delivery [E].

## 6. Cartridge shell (separate line)

| Item | Price | Source / date |
|---|---|---|
| Generic DMG-style cart shell (AliExpress bulk, 10-50 pack) | ~$0.30-2.00 each [E] | gbstudiocentral.com cart-shell guide: "10 cents to 3 bucks"; date not shown |
| Quality shell (Retro Modding) | $3.99 each; 12-colour pack $44.99 | same guide |
| Gamebit 3.8 mm screw / driver | ~$0.10 per screw, ~$3 driver [E] | AliExpress listings |

Before ordering shells, check that the 56 x 49.5 mm outline and the screw-boss cutout fit the shell you choose.

## Sources
- JLCPCB quote engine (cart.jlcpcb.com) and parts API (jlcpcb.com), queried 2026-10-01.
- JLCPCB help: "PCB Assembly Cost" (2026-09-09); "In what cases will there be charged extra?" (2026-09-09, ENIG >30% area surcharge); "JLCPCB gold fingers" (2026-09-18).
- JLCPCB news: "Free OSP Surface Finish" (2026-07-30).
- JLC part page C632847 (assembly type, MSL3).
- allaboutcircuits.com thread "JLCPCB Global Standard Direct Line Shipping" (2026-03-06 to 2026-03-19).
- gbstudiocentral.com "GB Game Cartridge Shells".
