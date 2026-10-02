#!/usr/bin/env python3
"""Write the DMG-shell reference board outline and the corrected edge-finger footprint.

  mech/out/dmg_reference.kicad_pcb    OEM-style outline (dimensions from gekkio/gb-hardware
                                      GB-CART256K-A, CC BY 4.0): body 51.4 x 61.0, finger tongue,
                                      top-right notch, Ø7.2 screw-tube hole, Ø2.3 locating hole,
                                      32 fingers. Start r1.1 / r2.1 layouts from this.
  lib/gbdev.pretty/GB_Cart_Edge_32_DMG.kicad_mod
                                      fingers start 1.5 mm above the edge (pins 1/32: 1.0 mm,
                                      longer, so GND/VCC make contact first); origin = bottom-edge
                                      centre like GB_Cart_Edge_32, so it drops in place.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dims import PCB_STD as P  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "out"
W, H = P["width"], P["height"]
CXB = W / 2  # finger footprint origin x (board centre)


def fingers():
    """(number, x from bottom-edge centre, y centre (KiCad, negative = up), w, l)"""
    out = []
    for n in range(1, 33):
        if n in (1, 32):
            x = (P["pin1_x"] - CXB) * (1 if n == 1 else -1)
            w, l, gap = 1.3, 6.0, 1.0
        else:
            x = P["pin2_x"] - CXB + (n - 2) * P["finger_pitch"]
            w, l, gap = P["finger_w"], P["finger_len"], P["finger_gap"]
        out.append((n, round(x, 3), -(gap + l / 2), w, l))
    return out


def footprint_text(name, inline_at=None):
    at = f"\n\t\t(at {inline_at[0]} {inline_at[1]})" if inline_at else ""
    pads = "\n".join(
        f'\t\t(pad "{n}" smd rect (at {x} {y}) (size {w} {l}) (layers "F.Cu" "F.Mask"))'
        for n, x, y, w, l in fingers())
    return f'''	(footprint "{name}"
		(layer "F.Cu"){at}
		(descr "Game Boy cartridge edge fingers for a DMG shell: 32 x 1.5 mm pitch, start 1.5 mm above the board edge (pins 1/32 1.0 mm). Origin = bottom-edge centre. Order ENIG or hard gold.")
		(tags "gameboy cartridge edge connector dmg")
		(property "Reference" "J1" (at 0 -8.5) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
		(property "Value" "GB_Cart_Edge_32_DMG" (at 0 -10) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
		(attr smd)
		(fp_line (start -24.6 0) (end 24.6 0) (stroke (width 0.1) (type solid)) (layer "F.Fab"))
		(fp_line (start -24.6 -7.3) (end 24.6 -7.3) (stroke (width 0.1) (type dash)) (layer "F.SilkS"))
{pads}
	)'''


def outline_kicad():
    """PCB frame (y up) -> KiCad (y down), board top-left at (0, 0)."""
    t0, t1, th = P["tongue_x0"], P["tongue_x1"], P["tongue_h"]
    pts = [(t0, 0), (t1, 0), (t1, th), (W, th), (W, P["notch_y0"]), (P["notch_x0"], P["notch_y0"]),
           (P["notch_x0"], H), (0, H), (0, th), (t0, th)]
    return [(x, round(H - y, 3)) for x, y in pts]


def main():
    OUT.mkdir(exist_ok=True)
    pts = outline_kicad()
    lines = "\n".join(
        f'\t(gr_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (stroke (width 0.05) (type solid)) (layer "Edge.Cuts"))'
        for a, b in zip(pts, pts[1:] + pts[:1]))
    holes = "\n".join(
        f'\t(gr_circle (center {x} {round(H - y, 3)}) (end {round(x + d / 2, 3)} {round(H - y, 3)}) (stroke (width 0.05) (type solid)) (fill none) (layer "Edge.Cuts"))'
        for x, y, d in (P["big_hole"], P["small_hole"]))
    board = f'''(kicad_pcb
	(version 20240108)
	(generator "gb-devcart-mech")
	(general (thickness {P["thickness"]}))
	(paper "A4")
	(layers
		(0 "F.Cu" signal)
		(31 "B.Cu" signal)
		(36 "B.SilkS" user "B.Silkscreen")
		(37 "F.SilkS" user "F.Silkscreen")
		(38 "B.Mask" user)
		(39 "F.Mask" user)
		(44 "Edge.Cuts" user)
		(49 "F.Fab" user)
	)
	(net 0 "")
{lines}
{holes}
{footprint_text("gbdev:GB_Cart_Edge_32_DMG", inline_at=(CXB, H))}
)
'''
    (OUT / "dmg_reference.kicad_pcb").write_text(board)
    mod = footprint_text("GB_Cart_Edge_32_DMG").replace("\t(footprint", "(footprint", 1)
    mod = "\n".join(line[1:] if line.startswith("\t") else line for line in mod.splitlines())
    mod = mod.replace('(footprint "GB_Cart_Edge_32_DMG"', '(footprint "GB_Cart_Edge_32_DMG"\n\t(version 20241229)\n\t(generator "gb-devcart-mech")', 1)
    (ROOT / "lib/gbdev.pretty/GB_Cart_Edge_32_DMG.kicad_mod").write_text(mod + "\n")
    print("wrote mech/out/dmg_reference.kicad_pcb and lib/gbdev.pretty/GB_Cart_Edge_32_DMG.kicad_mod")


if __name__ == "__main__":
    main()
