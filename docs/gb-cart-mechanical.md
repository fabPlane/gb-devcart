# Game Boy (DMG/GBC) cartridge: mechanical reference

Research date 2026-10-02. All values are in mm. Confidence key:
**CAD** means measured by me from open CAD files (KiCad Edge.Cuts/pads parsed, or STL ray-cast with trimesh).
**doc** means a published spec. **forum** means a secondary or unverified source.
No Nintendo drawing of the shell or PCB was found in public. Every shell number comes from community replicas, so check them against a real cart before tooling.

## Sources

| Key | Source | Licence |
| --- | --- | --- |
| GK | gekkio/gb-hardware: GB-CART32K-A, GB-CART256K-A, GB-MBCTEST and GB-LIVE32 `.kicad_pcb` files, plus the README spec lines. https://github.com/Gekkio/gb-hardware | CC BY 4.0 |
| MBL | MouseBiteLabs/Game-Boy-Cartridges, `MBC5 (Type A, SRAM)/mbc5_SRAM_typeA_1-2.kicad_pcb` (footprint `GBC_CART_TABBED`; the README says the shape "mimic[s] original Game Boy circuit boards"). https://github.com/MouseBiteLabs/Game-Boy-Cartridges | CC BY-SA 4.0 |
| RGR | RetroGameRevival, "Nintendo GameBoy (classic/DMG-01) cartridge shell". Both STLs are in assembled position. https://www.printables.com/model/804399 | CC BY-NC |
| FUN | FuniverseMN, "Gameboy DMG Cartridge Shell". The maker test-fit it in a real DMG with a Link's Awakening board. https://www.printables.com/model/281341 | CC BY-SA |
| WOOD | Staacks/wooden-game-boy-cartridge: CNC G-code (1.5 mm end mill; outline = toolpath extent − 1.5). https://github.com/Staacks/wooden-game-boy-cartridge | CC BY 4.0 |
| WP | Wikipedia, "Game Boy Game Pak". https://en.wikipedia.org/wiki/Game_Boy_Game_Pak | doc |
| LEM | Lemmy "Game Cartridge Dimensions" table (a repost). https://lemmy.world/post/241714 | forum |

## 1. Outer shell (grey DMG Game Pak)

| Item | Value | Source | Confidence |
| --- | --- | --- | --- |
| Width | 57.0 (FUN 56.95, WOOD 56.8) | WP 57; RGR; FUN; WOOD | doc + CAD, consistent |
| Height | 65.0 (RGR); 65.05 (FUN); 65.5 (WP); 64.5 (WOOD) | as listed | sources disagree by up to 1.0. Use 65.0 to 65.5 |
| Thickness | 7.8 (RGR assembled); 7.5 (WP; LEM "GB"); 9 (LEM "GBC", probably measured over the label bump) | RGR, WP, LEM | sources disagree. Design to ≤ 7.8 |
| Half thicknesses | back 5.75, front 5.3, overlapping at the lip (RGR); back 5.8, front 5.2 (FUN); back "about 5.5" (WOOD) | RGR, FUN, WOOD | CAD |
| Outline corner radii | ≈1.0 on all four corners (RGR silhouette); top corners ≈1.0 (FUN) | RGR, FUN | CAD |
| Lock notch (top-right seen from the label side; the DMG power-switch tab slides into it) | 4.8 wide × 3.3 deep (RGR); 5.0 wide × 3.0 deep (FUN) | RGR, FUN | CAD. Sources disagree by about 0.3 |
| Label recess (front) | ≈44.0 wide × ≈35.5 tall × 0.35 deep (RGR); the side rails beside it are at full height | RGR | CAD. Confirm on a real cart |
| Top front finger scoop | concave, ≈12 tall, up to 0.94 deep, ending about 15 below the top edge | RGR | CAD |
| Side grip grooves | 5 grooves at 2.0 pitch, 0.47 deep, on both sides, about 4 to 14 below the top | RGR | CAD |
| Front edge chamfer | ≈1.6 × 0.3 along the long sides | RGR | CAD (rough) |

## 2. PCB (fingers at the bottom, origin at the PCB bottom-left, component/finger side facing you)

| Item | GK (GB-CART*) | MBL (MBC5 Type A) | Confidence |
| --- | --- | --- | --- |
| Thickness | 1.0 (README "PCB thickness: 1.0mm"; board stack-up 1.0) | 0.8 ("Thickness: 0.8mm", "Be sure to get them in 0.8mm") | doc. Sources disagree. Other repro boards (OSH Park listings) also say 0.8 |
| Body width × height | 51.4 × 61.0 | 51.0 × 61.0, or 53.0 × 62.0 over the anti-rotation tabs | CAD |
| Finger tongue | X 1.1–50.3 (49.2 wide), 8.6 tall, bottom corners R0.9 | X 0.75–50.25 (49.5 wide), 9.0 tall, bottom corners R1.5 | CAD |
| Shoulder (tongue to body) | 1.1 step on each side at Y = 8.6, R0.5 corners | 0.75 step at Y = 9.0 | CAD |
| Top-right notch | X 47.4–51.4 (4.0 wide), Y 58.4–61.0 (2.6 deep), R0.5 | X 46.0–51.0 (5.0 wide), Y 58.0–61.0 (3.0 deep) | CAD. Sources disagree |
| Big hole (the shell's screw tube passes through it) | Ø7.2 NPTH at (25.7, 15.35) | Ø7.25 at (25.5, 15.80) | CAD |
| Small locating hole | Ø2.3 at (25.7, 40.35) | Ø2.25 at (25.5, 40.80) | CAD |
| Hole spacing | 25.0 | 25.0 | CAD, consistent |
| Side tabs | none | +1.0 per side, 3.0 tall, at Y 19.2–22.2 and Y 43.2–46.2. MBL added them so the board cannot rotate in loose aftermarket shells. Top tabs are +1.0 at X 13–16 and X 34.8–37.8 | CAD + README |

Holes are on the PCB centreline in both designs (X = half the body width).

## 3. Internal clearance (RGR assembled shell)

The front (label) half carries a perimeter frame of ribs whose underside sits 2.5 above the back outer face. That frame clamps the PCB's **front** face, and the PCB rests on the back half's screw tube and post. Components and fingers face the **label** side. This matches GK/MBL, where parts and fingers share F.Cu.

| Item | Value | Confidence |
| --- | --- | --- |
| Back wall | 1.15 thick (FUN 1.3) | CAD |
| Front wall | 1.65 under the label recess, 2.0 at the rails | CAD |
| PCB front-face plane | 2.5 above the back outer face | CAD |
| Space behind the PCB (back side) | 2.5 − t − 1.15, which is **0.55** for a 0.8 board and **0.35** for a 1.0 board. Treat the back as flat: no parts | CAD |
| Space in front of the PCB (label side), main area | **3.3** (inner face at 5.8) | CAD |
| Space in front, inside the connector mouth (lowest ≈10 of the cart) | 3.95 (inner face at 6.45). The console connector occupies this, so no parts there | CAD |
| Component zone on the front | ≈50.3 wide between the side ribs (1.45 wide each), and lengthwise between the cross ribs, about 11.4 and 61.7 up from the shell's bottom end | CAD |
| Cavity at PCB level | 53.2 wide (± 26.6) × ≈64 long | CAD |
| Tall parts | GK fits a PLCC-32 (JEDEC A ≤ 3.56) on a 1.0 board in a DMG shell. That is more than RGR's 3.3, so an OEM shell probably has about 3.6 of room. Keep parts ≤ 3.3 for printed shells | conflict (CAD vs. working design) |

## 4. Edge connector and slot

| Item | Value | Source | Confidence |
| --- | --- | --- | --- |
| Contacts / pitch | 32 / 1.5, on one side only (the label/component side) | GK, MBL footprints; Pan Docs https://gbdev.io/pandocs/External_Connectors.html | CAD + doc |
| Finger size, pins 2–31 | 1.0 × 5.5 (GK) or 1.0 × 5.4 (MBL) | GK, MBL | CAD |
| Finger size, pins 1 and 32 (GND/VCC) | 1.3 × 6.0 (GK) or 1.5 × 5.6 (MBL) | GK, MBL | CAD |
| Finger gap from the PCB bottom edge | 1.5 (GK) or 1.6 (MBL) for pins 2–31. Pins 1/32 run 0.5 (GK) or 0.2 (MBL) closer to the edge, so they make contact first. The top end of every finger is 7.0 above the edge in both designs | GK, MBL | CAD |
| Pin X positions | pin 1 at X 2.3 (GK) or 2.0 (MBL); pin 2 at 3.95 or 3.75; then 1.5 steps to pin 31; pin 32 is mirrored | GK, MBL | CAD |
| PCB bottom edge to shell bottom opening | 1.15 to 1.6 inset (RGR boss at 16.95 above the shell end, minus the hole height of 15.35 to 15.8); 0.7 to 1.15 (FUN boss at 16.5) | RGR, FUN with GK, MBL | CAD (derived) |
| Shell opening at the connector end | 53.2 wide; 3.95 from the PCB face to the front inner wall; up to ≈10 deep before the first cross rib. On the back side, a 0.75-long lip (49 wide) rises to 2.0 under the PCB edge | RGR | CAD |
| DMG slot connector body | ≈64.3 long × 21.2 deep, or 76.9 including the mounting ears (GB-BRK-SLOT-A footprint `GameBoy_Cartridge_DMG_1x32_P1.50mm_Socket_Horizontal`, F.Fab) | GK | CAD |
| How deep the cart goes into the DMG/GBC, and the slot's opening size | **Not found** in any primary source. The connector itself engages only the bottom ≈10 of the cart (the shell mouth). Measure a console before relying on this | – | gap |

## 5. Console compatibility

| Console | Accepts DMG-size carts? | Notes | Source / confidence |
| --- | --- | --- | --- |
| DMG / MGB / Light | yes | The DMG's power-switch tab enters the top notch. Clear GBC-only carts omit the notch "to prevent them from being used in the original Game Boy". Black dual-mode carts keep it. **Keep the notch** so a DMG can power on. | WP (doc) |
| Game Boy Color | yes | Same outline; the notch is not needed. | WP (doc) |
| GBA / GBA SP | yes (the cart sticks out) | The GBA's shape switch reads a notch on the bottom-rear corner that only GBA carts have. DMG carts have none, so the GBA starts in GB mode at 5 V. | WP (doc) |
| Analogue Pocket | yes | Native GB/GBC slot. No mechanical tolerance is published. EverDrive carts reportedly fail on newer Pocket revisions (androidauthority.com/everdrive-carts-malfunction-with-analogue-pocket-3677246). | forum |
| ModRetro Chromatic | yes | Plays GB and GBC carts; not GBA (ifixit.com/News/106916). ModRetro's own carts "are real Game Boy cartridges … run in an original Game Boy, Game Boy Color and an Analogue Pocket" (retrododo.com/?p=62610), so they use a standard DMG-size shell. They save to FRAM instead of a battery. The console's own screws are tri-point Y1 (ifixit.com/Device/ModRetro_Chromatic). No published slot-depth spec. | doc/forum |

## 6. Shell screw and bosses (RGR CAD unless noted)

| Item | Value | Confidence |
| --- | --- | --- |
| Screw head | 3.8 mm "gamebit" security head (https://handheldlegend.com/products/3-8mm-security-screwdriver-nes-snes-n64-and-game-boy). Not tri-wing, not Phillips | doc (vendor) |
| Screw position | on the centreline, 16.95 above the shell's bottom end (FUN: 16.5) | CAD |
| Back-half screw tube | OD 7.0 (chamfered to 6.0 at the top); top 2.9 above the back outer face; passes through the PCB's Ø7.2 hole | CAD |
| Head counterbore / shank hole | Ø5.0–5.15 from the back face to a depth of 2.25; then Ø2.25 through | CAD |
| Front-half boss | OD 4.0; pilot hole Ø1.5 (Ø2.0 at the mouth, for a self-tapping screw of about 2 mm); hangs from the front inner face (5.8) down to 2.9, about 2.9 tall | CAD |
| Back-half locating post | Ø1.9 tapering to Ø1.3; top 3.15 above the back face; 24.95 above the screw (FUN: 25.3); goes through the PCB's Ø2.3 hole | CAD |
| Screw length / thread | not found. About 2 mm self-tapping, an estimate from the 1.5 pilot | gap |

## 7. Fit check: this repo's `board.kicad_pcb`

These come from parsing `board.kicad_pcb` against the tables above:

- **Width 56.0 does not fit.** The cavity is 53.2 wide, and the OEM-style PCB is 51.4 (51.0 plus tabs to 53.0).
- There is no finger tongue or shoulder step and no top-right notch. A plain 56 × 49.5 rectangle hits the shell's mouth and lock-notch corner.
- Fingers start 0.5 above the board edge; GK/MBL start at 1.5 to 1.6. They are 1.0 × 6.0 at X 28 ± 23.25, so pins 1/32 sit at 4.75/51.25 from the left edge, not GK's 2.3/49.1 on a 51.4 body.
- There is one Ø3.5 hole at (28, 10.5). A DMG shell needs Ø≥7.2 at (W/2, 15.35–15.8) and Ø≥2.3 at (W/2, 40.35–40.8).
- Board thickness is still 1.6 in the file. Order 0.8 (MBL) or 1.0 (GK).
- Height: the PLCC-32 and SOIC-28W parts must stay ≤ 3.3 on the label side. The back side must stay empty (≤ 0.35 to 0.55).
- The simplest fix is to copy GK's GB-CART256K-A Edge.Cuts outline, holes and connector footprint (CC BY 4.0, attribution required).
