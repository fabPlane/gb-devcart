#!/usr/bin/env python3
"""Generate lib/gbdev.kicad_sym, lib/gbdev.pretty/GB_Cart_Edge_32.kicad_mod and circuit.netlist.json."""
import json, os, math

PROJ = "/home/user/fabdesk-projects/gb-devcart"
LIB = f"{PROJ}/lib"
os.makedirs(f"{LIB}/gbdev.pretty", exist_ok=True)

# ---------------------------------------------------------------- symbols
# part -> (refprefix, description, left[(num,name,type)], right[...])
def gate_chip(desc):
    L = [("1", "1A", "input"), ("2", "1B", "input"), ("4", "2A", "input"), ("5", "2B", "input"),
         ("9", "3A", "input"), ("10", "3B", "input"), ("12", "4A", "input"), ("13", "4B", "input")]
    R = [("14", "VCC", "power_in"), ("3", "1Y", "output"), ("6", "2Y", "output"),
         ("8", "3Y", "output"), ("11", "4Y", "output"), ("7", "GND", "power_in")]
    return ("U", desc, L, R)

flash_addr = {"A0": 12, "A1": 11, "A2": 10, "A3": 9, "A4": 8, "A5": 7, "A6": 6, "A7": 5, "A8": 27, "A9": 26,
              "A10": 23, "A11": 25, "A12": 4, "A13": 28, "A14": 29, "A15": 3, "A16": 2, "A17": 30, "A18": 1}
flash_dq = [13, 14, 15, 17, 18, 19, 20, 21]
SST_L = [(str(flash_addr[f"A{i}"]), f"A{i}", "input") for i in range(19)] + \
        [("22", "~{CE}", "input"), ("24", "~{OE}", "input"), ("31", "~{WE}", "input")]
SST_R = [(str(flash_dq[i]), f"DQ{i}", "bidirectional") for i in range(8)] + \
        [("32", "VDD", "power_in"), ("16", "VSS", "power_in")]

fram_addr = {"A0": 10, "A1": 9, "A2": 8, "A3": 7, "A4": 6, "A5": 5, "A6": 4, "A7": 3, "A8": 25, "A9": 24,
             "A10": 21, "A11": 23, "A12": 2, "A13": 26, "A14": 1}
fram_dq = [11, 12, 13, 15, 16, 17, 18, 19]
FRAM_L = [(str(fram_addr[f"A{i}"]), f"A{i}", "input") for i in range(15)] + \
         [("20", "~{CE}", "input"), ("22", "~{OE}", "input"), ("27", "~{WE}", "input")]
FRAM_R = [(str(fram_dq[i]), f"DQ{i}", "bidirectional") for i in range(8)] + \
         [("28", "VDD", "power_in"), ("14", "VSS", "power_in")]

L574 = [("1", "~{OE}", "input")] + [(str(2 + i), f"D{i}", "input") for i in range(8)] + [("11", "CP", "input")]
R574 = [("20", "VCC", "power_in")] + [(str(19 - i), f"Q{i}", "tri_state") for i in range(8)] + [("10", "GND", "power_in")]

CONN_NAMES = ["VCC", "CLK", "~{WR}", "~{RD}", "~{CS}"] + [f"A{i}" for i in range(16)] + \
             [f"D{i}" for i in range(8)] + ["~{RESET}", "AUDIO_IN", "GND"]
assert len(CONN_NAMES) == 32
CONN = []
for i, n in enumerate(CONN_NAMES):
    t = "power_out" if n in ("VCC", "GND") else "bidirectional"
    CONN.append((str(i + 1), n, t))

SYMS = {
    "GB_Cart_Edge_32": ("J", "Game Boy DMG/Chromatic cartridge edge connector, 32 fingers", CONN[:16], CONN[16:]),
    # Tall chips are split evenly across both sides (16/16, 14/14) so each symbol stays inside one
    # 30.48 mm row of the generated-schematic grid; otherwise their pin labels land on the pins of the
    # symbol below and merge different nets.
    "SST39SF040": ("U", "512KB 5V parallel NOR flash, PLCC-32", (SST_L + SST_R)[:16], (SST_L + SST_R)[16:]),
    "FM18W08": ("U", "32KB parallel F-RAM, 2.7-5.5V, SOIC-28", (FRAM_L + FRAM_R)[:14], (FRAM_L + FRAM_R)[14:]),
    "74HC574": ("U", "Octal D flip-flop, tri-state outputs", L574, R574),
    "74HC32": gate_chip("Quad 2-input OR"),
    "74HC00": gate_chip("Quad 2-input NAND"),
    "R": ("R", "Resistor", [("1", "~", "passive")], [("2", "~", "passive")]),
    "C": ("C", "Capacitor", [("1", "~", "passive")], [("2", "~", "passive")]),
    "TestPoint": ("TP", "Test point", [("1", "1", "passive")], []),
}

# pin lookup: PIN[part][name] -> number
PIN = {k: {**{num: num for (num, _n, _t) in (v[2] + v[3])}, **{n: num for (num, n, _t) in (v[2] + v[3]) if n != "~"}} for k, v in SYMS.items()}

FONT = '(effects (font (size 1.27 1.27)))'
def sym_text(name, v):
    prefix, desc, left, right = v
    rows = max(len(left), len(right))
    two_sided = bool(right)
    W = 12.7 if two_sided else 5.08  # pin tip x
    y0 = 1.27 * (rows - 1)
    top = y0 + 2.54
    hw = W - 2.54
    if not two_sided:
        hw = 1.27
    out = [f'  (symbol "{name}" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)',
           f'    (property "Reference" "{prefix}" (at 0 {top + 1.27:.3f} 0) {FONT})',
           f'    (property "Value" "{name}" (at 0 {-top - 1.27:.3f} 0) {FONT})',
           f'    (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
           f'    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
           f'    (property "Description" "{desc}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
           f'    (symbol "{name}_0_1" (rectangle (start {-hw:.3f} {top:.3f}) (end {hw:.3f} {-top:.3f}) '
           f'(stroke (width 0.254) (type default)) (fill (type background))))',
           f'    (symbol "{name}_1_1"']
    for i, (num, pn, t) in enumerate(left):
        y = y0 - 2.54 * i
        out.append(f'      (pin {t} line (at {-W:.3f} {y:.3f} 0) (length 2.54) (name "{pn}" {FONT}) (number "{num}" {FONT}))')
    for i, (num, pn, t) in enumerate(right):
        y = y0 - 2.54 * i
        out.append(f'      (pin {t} line (at {W:.3f} {y:.3f} 180) (length 2.54) (name "{pn}" {FONT}) (number "{num}" {FONT}))')
    out.append('    )')
    out.append('  )')
    return "\n".join(out)

with open(f"{LIB}/gbdev.kicad_sym", "w") as f:
    f.write('(kicad_symbol_lib (version 20241209) (generator "gbdev") (generator_version "1.0")\n')
    for k, v in SYMS.items():
        f.write(sym_text(k, v) + "\n")
    f.write(")\n")

# ---------------------------------------------------------------- edge footprint
FING_W, FING_H, PITCH, EDGE_GAP = 1.0, 6.0, 1.5, 0.5
pads = []
for n in range(1, 33):
    x = (n - 16.5) * PITCH
    pads.append(f'  (pad "{n}" smd rect (at {x:.3f} {-(EDGE_GAP + FING_H / 2):.3f}) (size {FING_W} {FING_H}) (layers "F.Cu" "F.Mask"))')
mod = f'''(footprint "GB_Cart_Edge_32"
  (version 20241229)
  (generator "gbdev")
  (generator_version "1.0")
  (layer "F.Cu")
  (descr "Game Boy cartridge edge fingers, 32 x 1.5 mm pitch, component side. Origin = bottom edge centre. Specify ENIG / hard gold.")
  (tags "gameboy cartridge edge connector")
  (property "Reference" "REF**" (at 0 -8.5 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
  (property "Value" "GB_Cart_Edge_32" (at 0 -10 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
  (property "Footprint" "" (at 0 0 0) (layer "F.Fab") (hide yes) (effects (font (size 1.27 1.27))))
  (property "Datasheet" "" (at 0 0 0) (layer "F.Fab") (hide yes) (effects (font (size 1.27 1.27))))
  (property "Description" "" (at 0 0 0) (layer "F.Fab") (hide yes) (effects (font (size 1.27 1.27))))
  (attr smd)
  (fp_line (start -24.5 0) (end 24.5 0) (stroke (width 0.1) (type solid)) (layer "F.Fab"))
  (fp_line (start -24.5 -7) (end 24.5 -7) (stroke (width 0.1) (type dash)) (layer "F.SilkS"))
{chr(10).join(pads)}
)
'''
with open(f"{LIB}/gbdev.pretty/GB_Cart_Edge_32.kicad_mod", "w") as f:
    f.write(mod)

# ---------------------------------------------------------------- netlist
FP = {
    "J1": "gbdev:GB_Cart_Edge_32",
    "U1": "Package_LCC:PLCC-32_11.4x14.0mm_P1.27mm",
    "U2": "Package_SO:SOIC-28W_7.5x17.9mm_P1.27mm",
    "U3": "Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm",
    "U4": "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
    "U5": "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
    "U6": "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
}
comps = []
def add(ref, value, fp, part, **fields):
    comps.append({"ref": ref, "value": value, "footprint": fp,
                  "fields": {k: v for k, v in fields.items()},
                  "libSource": {"lib": "gbdev", "part": part}})
    PARTOF[ref] = part
PARTOF = {}

add("J1", "GB_Cart_Edge_32", FP["J1"], "GB_Cart_Edge_32", Description="DMG cartridge edge fingers (PCB feature, ENIG)")
add("U1", "SST39SF040", FP["U1"], "SST39SF040", MPN="SST39SF040-55-4I-NHE-T", Manufacturer="Microchip", LCSC="C632847")
add("U2", "FM18W08", FP["U2"], "FM18W08", MPN="FM18W08-SGTR", Manufacturer="Infineon (Cypress/Ramtron)", LCSC="C55945")
add("U3", "74HC574", FP["U3"], "74HC574", MPN="SN74HC574DWR", Manufacturer="Texas Instruments", LCSC="C10097")
add("U4", "74HC32", FP["U4"], "74HC32", MPN="SN74HC32DR", Manufacturer="Texas Instruments", LCSC="C6838")
add("U5", "74HC32", FP["U5"], "74HC32", MPN="SN74HC32DR", Manufacturer="Texas Instruments", LCSC="C6838")
add("U6", "74HC00", FP["U6"], "74HC00", MPN="SN74HC00DR", Manufacturer="Texas Instruments", LCSC="C10090")
for i in range(1, 7):
    add(f"C{i}", "100nF", "Capacitor_SMD:C_0603_1608Metric", "C", Description="X7R 50V decoupling", MPN="CC0603KRX7R9BB104", Manufacturer="Yageo", LCSC="C14663")
add("C7", "10uF", "Capacitor_SMD:C_1206_3216Metric", "C", Description="X5R 50V bulk", MPN="CL31A106KBHNNNE", Manufacturer="Samsung", LCSC="C13585")
add("R1", "10k", "Resistor_SMD:R_0603_1608Metric", "R", Description="/RESET pull-up", MPN="0603WAF1002T5E", Manufacturer="UNI-ROYAL", LCSC="C25804")
for i in range(2, 7):
    add(f"R{i}", "2.2k", "Resistor_SMD:R_0603_1608Metric", "R", Description="bank latch pull-down", MPN="0603WAF2201T5E", Manufacturer="UNI-ROYAL", LCSC="C4190")
for i, n in enumerate(["VCC", "GND", "CLK", "WR", "RD", "AUDIO_IN"], 1):
    add(f"TP{i}", f"TP_{n}", "TestPoint:TestPoint_Pad_D1.5mm", "TestPoint")

nets = {}
def conn(net, *pins):
    nets.setdefault(net, [])
    for ref, pn in pins:
        part = PARTOF[ref]
        num = PIN[part][pn]
        nets[net].append({"ref": ref, "pin": str(num), "pinFunction": pn.replace("~{", "/").replace("}", "")})

# power
conn("VCC", ("J1", "VCC"), ("U1", "VDD"), ("U2", "VDD"), ("U3", "VCC"), ("U4", "VCC"), ("U5", "VCC"), ("U6", "VCC"),
     *[(f"C{i}", "1") for i in range(1, 8)], ("R1", "1"), ("TP1", "1"))
conn("GND", ("J1", "GND"), ("U1", "VSS"), ("U2", "VSS"), ("U3", "GND"), ("U4", "GND"), ("U5", "GND"), ("U6", "GND"),
     *[(f"C{i}", "2") for i in range(1, 8)], *[(f"R{i}", "2") for i in range(2, 7)], ("TP2", "1"),
     ("U2", "A13"), ("U2", "A14"),
     ("U5", "4A"), ("U5", "4B"), ("U6", "3A"), ("U6", "3B"), ("U6", "4A"), ("U6", "4B"))
# control
conn("CLK", ("J1", "CLK"), ("TP3", "1"))
conn("WR_N", ("J1", "~{WR}"), ("U4", "1A"), ("U2", "~{WE}"), ("TP4", "1"))
conn("RD_N", ("J1", "~{RD}"), ("U1", "~{OE}"), ("U2", "~{OE}"), ("TP5", "1"))
conn("CS_N", ("J1", "~{CS}"), ("U5", "2A"))
conn("RESET_N", ("J1", "~{RESET}"), ("R1", "2"))
conn("AUDIO_IN", ("J1", "AUDIO_IN"), ("TP6", "1"))
# address
for i in range(16):
    p = [("J1", f"A{i}")]
    if i <= 13: p.append(("U1", f"A{i}"))
    if i <= 12: p.append(("U2", f"A{i}"))
    if i == 12: p.append(("U4", "2B"))
    if i == 13: p += [("U6", "1A"), ("U6", "1B")]
    if i == 14: p += [("U4", "2A"), ("U5", "2B"), ("U6", "2A"), ("U6", "2B")]
    if i == 15: p += [("U4", "1B"), ("U1", "~{CE}")]
    conn(f"A{i}", *p)
for i in range(8):
    conn(f"D{i}", ("J1", f"D{i}"), ("U1", f"DQ{i}"), ("U2", f"DQ{i}"), ("U3", f"D{i}"))
# derived
conn("nA13", ("U6", "1Y"), ("U4", "4B"), ("U5", "3B"))
conn("nA14", ("U6", "2Y"), ("U5", "1B"), ("U3", "~{OE}"))
conn("WR_A15", ("U4", "1Y"), ("U4", "3A"), ("U5", "1A"))
conn("A14_A12", ("U4", "2Y"), ("U4", "3B"))
conn("SEL_PART", ("U4", "3Y"), ("U4", "4A"))
conn("LATCH_CLK", ("U4", "4Y"), ("U3", "CP"))
conn("FLASH_WE_N", ("U5", "1Y"), ("U1", "~{WE}"))
conn("CS_A14", ("U5", "2Y"), ("U5", "3A"))
conn("FRAM_CE_N", ("U5", "3Y"), ("U2", "~{CE}"))
for i in range(5):
    conn(f"ROM_A{14 + i}", ("U3", f"Q{i}"), ("U1", f"A{14 + i}"), (f"R{2 + i}", "1"))

noconn = [{"ref": "U3", "pin": str(PIN["74HC574"][f"Q{i}"])} for i in (5, 6, 7)] + \
         [{"ref": "U5", "pin": "11"}, {"ref": "U6", "pin": "8"}, {"ref": "U6", "pin": "11"}]

# every pin used exactly once
seen = {}
for n, lst in nets.items():
    for nd in lst:
        k = (nd["ref"], nd["pin"])
        assert k not in seen, (k, n, seen[k])
        seen[k] = n

# check no stray connectivity gaps for ICs
for ref, part in PARTOF.items():
    if part in ("R", "C", "TestPoint"): continue
    for num in {n for (n, _x, _t) in SYMS[part][2] + SYMS[part][3]}:
        k = (ref, num)
        if k not in seen and not any(c["ref"] == ref and c["pin"] == num for c in noconn):
            print("UNCONNECTED", ref, num)

PLACE = {
    "J1": (28, 49.5), "U1": (14, 14), "U2": (48.5, 15), "U3": (32.5, 11),
    "U4": (24, 29), "U5": (33, 29), "U6": (13, 31),
    "C1": (18.5, 3.2), "C2": (53, 3.4), "C3": (36.8, 2.4), "C4": (24, 22.5), "C5": (33, 22.5), "C6": (18.5, 27.4),
    "C7": (6, 38.5), "R1": (46, 33),
    "R2": (40.2, 4.8), "R3": (40.2, 7.8), "R4": (40.2, 10.8), "R5": (40.2, 13.8), "R6": (40.2, 16.8),
    "TP1": (40, 39.5), "TP2": (43, 39.5), "TP3": (46, 39.5), "TP4": (49, 39.5), "TP5": (52, 39.5), "TP6": (52, 35.5),
}
doc = {
    "netlist": {
        "components": comps,
        "nets": [{"name": n, "nodes": v} for n, v in nets.items()],
        "noConnects": noconn,
        "design": {"source": "gb-devcart", "tool": "gen.py"},
    },
    "board": {
        "widthMm": 56, "heightMm": 49.5, "copperLayers": 2,
        "rules": {"clearanceMm": 0.15, "trackWidthMm": 0.2, "viaDiameterMm": 0.5, "viaDrillMm": 0.3},
        "holes": [{"x": 28, "y": 39, "diameterMm": 3.5}],
        "placements": [{"ref": r, "position": {"x": x, "y": y}} for r, (x, y) in PLACE.items()],
    },
    "libraries": [
        {"kind": "symbol", "nickname": "gbdev", "uri": f"{LIB}/gbdev.kicad_sym", "description": "GB devcart symbols"},
        {"kind": "footprint", "nickname": "gbdev", "uri": f"{LIB}/gbdev.pretty", "description": "GB devcart footprints"},
    ],
}
assert set(PLACE) == {c["ref"] for c in comps}, set(PLACE) ^ {c["ref"] for c in comps}
with open(f"{PROJ}/circuit.netlist.json", "w") as f:
    json.dump(doc, f, indent=1)
print("ok", len(comps), "components", len(nets), "nets")
