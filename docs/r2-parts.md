# GB DEVCART r2: parts research (FPGA mapper, 4-layer, 56 x 50 mm)

Snapshot taken **2026-10-02**. Prices are USD unit prices from the JLCPCB/LCSC parts API (`selectSmtComponentList`) unless marked otherwise.
Tags: **[P]** parts API, queried 2026-10-02. **[Q]** live JLC quote engine (`cart.jlcpcb.com` `calculationGoodsCosts`), queried 2026-10-02.
**[D]** vendor datasheet (version and date given). **[E]** estimate or unverified, so check it before ordering.
"Ext" means a JLC Extended part. Under Economic PCBA each one costs a $3.07 loading fee per order.

## Recommended parts per role [P]

| Role | MPN | LCSC | Lib | Stock | $ @10 | $ @100 | KiCad footprint | Datasheet |
|---|---|---|---|---|---|---|---|---|
| FPGA | **GW1NZ-LV1QN48C6/I5** | **C5799569** | Ext | 912 | 5.59 | 4.44 | `Package_DFN_QFN:QFN-48-1EP_6x6mm_P0.4mm_EP4.4x4.4mm` [E] | cdn.gowinsemi.com.cn/DS841E.pdf, pinout cdn.gowinsemi.com.cn/UG842E.pdf |
| ROM 8 MB | **S29GL064N90TFI040** | **C117907** | Ext | 108 | 2.86 | 2.25 | `Package_SO:TSOP-I-48_18.4x12mm_P0.5mm` | lcsc.com/datasheet/lcsc_datasheet_2304140030_Infineon-Cypress-Semicon-S29GL064N90TFI040_C117907.pdf |
| Save RAM 32 KB | **FM28V020-SGTR** | **C54935** | Ext | 1,000 | 9.16 | 6.97 | `Package_SO:SOIC-28W_7.5x17.9mm_P1.27mm` (same as r1 U2) | lcsc.com/datasheet/lcsc_datasheet_1912111437_Infineon-Cypress-Semicon-FM28V020-SGTR_C54935.pdf |
| 5 V to 3.3 V, x3 | **74LVC245APW,118** (Nexperia) | **C6082** | Ext | 270,429 | 0.21 | 0.17 | `Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm` | lcsc.com/datasheet/lcsc_datasheet_2407241045_Nexperia-74LVC245APW-118_C6082.pdf |
| Data bus, x1 | **SN74LVC8T245PWR** | **C27643** | Ext | 57,632 | 0.27 | 0.19 | `Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm` | lcsc.com/datasheet/lcsc_datasheet_1810312312_Texas-Instruments-SN74LVC8T245PWR_C27643.pdf |
| 3.3 V LDO | **XC6206P332MR-G** | **C5446** | **Basic** | 474,338 | 0.14 | 0.12 | `Package_TO_SOT_SMD:SOT-23` | lcsc.com/datasheet/lcsc_datasheet_2304140030_Torex-Semicon-XC6206P332MR-G_C5446.pdf |
| 1.2 V LDO | **ME6211C12M5G-N** | **C236672** | Ext | 10,931 | 0.06 | 0.05 | `Package_TO_SOT_SMD:SOT-23-5` | lcsc.com/datasheet/lcsc_datasheet_2304140030_MICRONE-Nanjing-Micro-One-Elec-ME6211C12M5G-N_C236672.pdf |

## Alternates [P]

| Role | MPN | LCSC | Lib | Stock | $ @10 | $ @100 | Note |
|---|---|---|---|---|---|---|---|
| FPGA | ICE40UP5K-SG48I | C2678152 | Ext | 261 | 9.61 | 8.10 | QFN-48 7x7 (`QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm` [E]). 1.2 V core. Needs an external SPI flash: W25Q32JVSSIQ **C179173** (17,363 stock, $1.30/$1.04, `Package_SO:SOIC-8_5.23x5.23mm_P1.27mm`). Best-supported open-source flow (IceStorm). |
| FPGA | ICE40HX1K-VQ100 | C1519043 | Ext | **35** | 11.63 | 8.94 | TQFP-100 is too large for a 56 x 50 mm board alongside a TSOP-48. Needs SPI flash. |
| FPGA | GW1N-LV1QN48C6/I5 | C5799563 | Ext | **0** | 24.38 | - | Pin-compatible sibling. Out of stock. LV1FN32 (C5453972) and LV1CS16 also show 0. |
| ROM 8 MB | S29GL064S70TFI040 | C914938 | Ext | 87 | 4.55 | 3.63 | Newer "S" die, 70 ns, same pinout. Drop-in. |
| ROM 8 MB | MX29LV640EBTI-70G | C30076 | Ext | **13** | 5.58 | 4.71 | TSOP-48 x8/x16 bottom boot. Low stock. |
| ROM 4 MB | S29GL032N90TFI040 | C117908 | Ext | 119 | 3.73 | 2.92 | Same family and pinout, half the size. Costs more than the 064 today. |
| ROM (no) | SST39VF6401B / 3201B (C36836, C46322) | | Ext | 62/96 | 6.06/6.18 | | **x16 only, no BYTE# pin.** Not suitable. |
| Save RAM | FM18W08-SGTR | C55945 | Ext | **45** | 9.58 | 9.58 | 2.7-5.5 V, same JEDEC 32Kx8 pinout and footprint. Works at 3.3 V but has less stock. |
| Save RAM (no) | FM28V020-TG | C2947417 | Ext | 10 | 24.94 | | TSOP-32, expensive. |
| Translator | SN74LVC4245APWR | C7859 | Ext (Preferred) | 122,578 | 0.39 | 0.28 | Classic octal 5 V/3.3 V transceiver with DIR. Alternative to the 8T245. |
| Translator | SN74LVC16T245DGGR | C148170 | Ext | 2,618 | 1.49 | 1.16 | 16-bit dual-supply, TSSOP-48. Two of them would cover all 29 GB lines in 2 parts but cost about 3x more. |
| 3.3 V LDO | ME6211C33M5G-N / AP2112K-3.3TRG1 | C82942 / C51118 | Ext | 165k / 38.8k | 0.06 / 0.17 | 0.05 / 0.14 | 500 / 600 mA, SOT-23-5 with EN pin. Use one if the 3.3 V rail needs more than 200 mA. |
| 1.2 V LDO | XC6206P122MR-G (Torex) / AP2112K-1.2TRG1 | C424699 / C460310 | Ext | 2,383 / 200 | 0.16 / 0.36 | 0.13 / 0.28 | SOT-23 / SOT-23-5. |

## Notes per role

**1. FPGA: GW1NZ-LV1 (GW1NZ-1) in QN48.** Specs are from [D] DS841 v2.8E (2026-04-03) and UG842 v1.6.8E (2026-03-09).
- 1,152 LUT4s, 864 FFs, 72 Kbit BSRAM, 1 PLL, 64 Kbit user flash, internal config flash (instant-on, no SPI chip). **QN48 has 41 user I/O, maximum.**
- Core VCC (LV part) is **1.2 V nominal**, range 1.07-1.26 V. VCCIO0/VCCIO1 range 1.14-3.6 V, so 3.3 V is fine. VCCX (auxiliary) range 1.71-3.6 V and must be at least VCCIO, so tie it to 3.3 V. The absolute maximum on any I/O is 3.75 V, so the pins are **not 5 V tolerant**.
- VCC ramp rate must be between 0.6 and 6 mV/us, i.e. the 1.2 V rail must take at least 200 us to come up. Check the LDO soft-start, or add an RC on EN or a larger output capacitor [E].
- QN48 power pins: VCC 12 and 37, VCCIO0 1, VCCIO1 25, VCCX 36, VSS 2 and 26 plus the EPAD (GND recommended).
- JTAG pins: **TCK 3, TMS 4, TDI 5, TDO 7**. Config pins: JTAGSEL_N 44, RECONFIG_N 48, DONE 46, READY 45, MODE0 43, MODE1 42 (MODE2 is internally grounded).
- JTAG pins become GPIO unless JTAGSEL_N is held low. Keep JTAG dedicated (pull JTAGSEL_N low, or leave the pins unused as GPIO) so the part cannot lock you out. That leaves about **35 usable I/O**.
- Open-source flow: the Apicula README (checked 2026-10-02) lists the *Sipeed Tang Nano 1K: GW1NZ-LV1QN48C6/I5* as a supported board, using yosys `synth_gowin`, nextpnr-himbaechel (gowin) and gowin_pack. openFPGALoader's FPGAs.yml lists GW1NZ-1 with "Memory: OK, Flash: IF", meaning SRAM load and internal-flash programming both work. This is the same chip as the Tang Nano 1K, which makes it a good dev board for bring-up.
- I/O budget, assuming the memories take buffered GB A0-A13 directly and the FPGA only decodes.
  - Inputs, 17: A12-A15, D0-D7, /RD, /WR, /CS, CLK, /RST.
  - Outputs, 16: ROM A13-A21 (9 bank bits), ROM /CE, ROM /WE gate, RAM /CE, RAM A13-A14, xcvr DIR, xcvr /OE.
  - Total: 33, plus 4 JTAG, is **37 of 41**. That leaves room for an LED or 2 I2C pins for an RTC, and nothing more. Full 16-bit address decode in the FPGA does **not** fit.

**2. ROM: S29GL064N, model 04.** Model 04 is the TSOP-48, x8/x16, bottom-boot version. Models 06/07 are x16-only [E: from memory of the S29GL-N ordering table, so check this in the datasheet before ordering].
- 2.7-3.6 V supply, 90 ns access, AMD/JEDEC command set. Tie **BYTE# low** for x8 mode. DQ15 then becomes A-1 (the byte LSB): wire GB A0 to A-1, GB A1-A13 to A0-A12, and the FPGA bank bits to A13-A21.
- In byte mode, unlock and program use **0xAAA/0xAA, 0x555/0x55, 0xAAA/0xA0**. Word mode uses 0x555/0x2AA. Autoselect and erase follow the same pattern (0x80, 0x10/0x30).
- WP#/ACC needs a pull-up and RESET# a pull-up or an FPGA pin.
- With the shifters' few ns of delay, 90 ns fits easily in the GB access window, including CGB double speed.

**3. Save RAM: FM28V020-SGTR.** This is the pick: 1,000 in stock, cheaper than the FM18W08-SGTR (45 in stock), and specified for 2.0-3.6 V. It sits on the 3.3 V side, so its 3 V-only rating does not matter.
- Same JEDEC 32Kx8 SOIC-28 (300 mil) pinout as r1's FM18W08, so the r1 footprint carries over.
- F-RAM needs no battery. /CE must toggle on every access (the RAM is address-latched on the /CE falling edge). Drive /CE from the FPGA, qualified by the GB /CS (A000-BFFF) and RAM enable, so the r1 CE-gating logic moves into the FPGA.

**4. Level shifting.** The GB cart edge is 5 V. Every GW1NZ pin has an absolute maximum of 3.75 V.
- (a) Address and control, 5 V to 3.3 V: **3x 74LVC245APW** with VCC = 3.3 V, DIR tied to B to A, /OE to GND. That gives 24 channels for A0-A15, /RD, /WR, /CS, CLK, /RST, with 3 spare. The datasheet allows inputs up to 5.5 V at VCC = 3.3 V.
- (b) Data bus: **SN74LVC8T245** with VCCA = 3.3 V and VCCB = 5 V (the cart's VCC). The FPGA drives DIR and /OE: B to A by default, A to B only while /RD is low and the cart is selected.
- Driving the data bus with a 74LVC245 at 3.3 V, so VOH is about 3.0-3.3 V, does work electrically: its I/O tolerates 5 V while it is receiving. But Nintendo publishes no V_IH for the DMG or CGB CPU. Forum reports put the input threshold at TTL-like levels (about 2.0-2.4 V), which would make 3.3 V work but with a thin margin [E].
- Against a CMOS 0.7 x VCC threshold (3.5 V), 3.3 V is out of spec. The 8T245 costs $0.06 more than a 245, so do not take the risk.
- ModRetro Chromatic: I found **no public schematic or teardown data (as of 2026-10-02)** on its cart-port voltages or buffers. Assume 5 V cart signalling like DMG/CGB. The dual-supply 8T245 is also safe if the port turns out to run at 3.3 V, because both sides accept 1.65-5.5 V.

**5. Regulators.**
- 3.3 V: **XC6206P332MR-G** (Basic, so no loading fee). 200 mA maximum, about 250 mV dropout at 100 mA. Estimated load is 40-80 mA (flash read about 30 mA, program about 50 mA, FPGA plus F-RAM plus logic about 20 mA) [E].
- 1.2 V: **ME6211C12M5G-N**, fed from the 3.3 V rail. That costs less dissipation than feeding it from 5 V, and EN is available for sequencing and ramp control.
- Power-up order: VCCX/VCCIO (3.3 V) first, then 1.2 V, which suits the GW1NZ.

**6. RTC (MBC3), optional.** It is feasible, but the clock must keep running while the cart is unpowered, so the FPGA cannot do it.
- Parts: **PCF8563T/5** (C7440, Ext *Preferred*, 21,338 stock, $0.51/$0.38, `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm`), a 32.768 kHz crystal **Q13FC13500004** (C32346, **Basic**, $0.17, `Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm`) and a CR1220 holder (e.g. C70381, $0.24).
- That adds about **$0.95 per board plus $3.07 loading per order**. The FPGA emulates MBC3 latch registers over I2C, using 2 of the remaining spare pins.

## PCB: 4-layer, 56 x 50 mm, 1.0 mm, ENIG 1u", green, FR-4 Tg140, 1 oz outer / 0.5 oz inner [Q] (2026-10-02)

| Finish | 5 pcs | 10 pcs | 30 pcs | 100 pcs |
|---|---|---|---|---|
| **ENIG 4L** | **$24.60** | **$30.60** | $52.00 | $70.20 |
| HASL (leaded) 4L | $8.00 | $14.00 | $34.00 | $48.90 |
| (r1 reference) ENIG 2L, same query | $18.60 | $21.60 | - | - |

- The ENIG upcharge is the same flat $16.60 per order as on 2L. 4L adds $6.00 at 5 pcs and $9.00 at 10 pcs over 2L.
- r1 noted that JLC wants gold-finger boards at least 50 mm per side. **50 mm meets that.**
- Check in the cart that Economic PCBA accepts 4-layer boards and 0.4 mm-pitch QFN; otherwise use Standard PCBA [E].

## BOM per board at 10 boards (parts only, list price @10) [P]

| Item | $ |
|---|---|
| FPGA 5.59 + ROM 2.86 + F-RAM 9.16 | 17.61 |
| 3x 74LVC245 (0.64) + 8T245 (0.27) + two LDOs (0.20) | 1.11 |
| Passives: ~16x 100 nF, ~4x 1-10 uF, ~8 resistors (Basic) [E] | ~0.60 |
| **r2 parts total** | **~$19.3** (RTC option adds ~$0.95) |
| r1 parts total (docs/jlcpcb-pricing.md, 2026-10-01) | $16.32 |

- **Assembled at 10 pcs, Economic [E]:**
  - PCB: $3.06 per board.
  - Parts: $19.3 per board.
  - Fees: $8.18 setup + $1.53 stencil + 6 Extended x $3.07 = $28.12 per order, about $2.81 per board.
  - Joints: about 280 at $0.0016, about $0.48 per board.
  - Total: **about $25.7 per board, about $257 per order**, versus about $21.46 per board for r1.
- F-RAM is still the largest line, about 47% of r2 parts. At 100 boards r2 parts fall to about $15.0 (FPGA $4.44, F-RAM $6.97) [P].
- Stock today (2026-10-02) covers 100 boards for every recommended line.

## Sources (all accessed 2026-10-02)
- JLCPCB parts API `jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList`. JLC quote engine `cart.jlcpcb.com/api/overseas-shop-cart/v1/shoppingCart/calculationGoodsCosts`.
- Gowin DS841 *GW1NZ series Datasheet* v2.8E (2026-04-03). Gowin UG842 *GW1NZ-1 Pinout* v1.6.8E (2026-03-09). Both from cdn.gowinsemi.com.cn.
- github.com/YosysHQ/apicula readme.md. github.com/trabucayre/openFPGALoader doc/FPGAs.yml.
- KiCad footprint names checked against the local standard library at /home/user/tools/footprints.
