#!/usr/bin/env python3
"""r2.1 placement on the DMG cartridge outline (mech/dims.py PCB_STD, gekkio GB-CART256K-A shape).

KiCad board frame: origin at the board's top-left, y down, mm. The fingers run along the bottom
edge (y = 61); the USB-C mouth sticks out of the top edge into the r2 shell's opening.

    python3 r2/hw/layout_dmg.py      # checks courtyards against each other, the shell component
                                     # zone, the notch and the screw/post keep-outs; exits 1 on a clash

Every part sits on F.Cu (the label side), no taller than 3.3 mm, inside the zone between the shell's
side ribs (x 0.55-50.85) and between its cross ribs (y 0.9-51.2); nothing in the connector mouth.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "mech"))
from dims import PCB_STD as P, SHELL as S, PCB_INSET_Y, PCB_X_IN_SHELL  # noqa: E402

W, H = P["width"], P["height"]

# Board outline (KiCad frame), clockwise from the tongue's bottom-left corner.
def outline():
    t0, t1, th = P["tongue_x0"], P["tongue_x1"], P["tongue_h"]
    pts = [(t0, 0), (t1, 0), (t1, th), (W, th), (W, P["notch_y0"]), (P["notch_x0"], P["notch_y0"]),
           (P["notch_x0"], H), (0, H), (0, th), (t0, th)]
    return [(x, round(H - y, 3)) for x, y in pts]

HOLES = [(P["big_hole"][0], round(H - P["big_hole"][1], 3), P["big_hole"][2]),
         (P["small_hole"][0], round(H - P["small_hole"][1], 3), P["small_hole"][2])]

# ref -> (x, y, rotation°). Rotation is KiCad's (counter-clockwise on screen).
LAYOUT = {
    # edge connector: origin = bottom-edge centre
    "J1": (W / 2, H, 0),
    # top band: USB-C (mouth up, 1.2 mm past the board edge), USB bridge, power
    "J2": (W / 2, 2.95, 180),
    "U11": (34.0, 4.5, 0), "U10": (40.5, 5.5, 0), "Y1": (46.0, 6.5, 0),
    "C25": (49.9, 6.0, 90), "C26": (46.5, 9.7, 0),
    "C23": (36.0, 9.7, 0), "C27": (39.5, 9.7, 0), "R16": (43.0, 9.7, 0),
    "R17": (18.5, 2.6, 0), "R18": (18.5, 4.6, 0),
    "D2": (3.2, 2.3, 0), "D1": (3.2, 5.0, 0),
    "U8": (9.0, 2.7, 0), "U9": (9.0, 6.6, 0),
    "C15": (14.0, 1.9, 0), "C12": (14.0, 3.8, 0), "C11": (14.0, 5.7, 0), "C13": (14.0, 7.6, 0),
    "C10": (3.2, 7.6, 0), "C14": (3.2, 9.6, 0),
    # FPGA + decoupling, oscillator, configuration straps
    "U1": (11.5, 27.0, 0),
    # decoupling at the QFN corners and mid-sides, leaving a 2.5 mm fan-out ring around the pins clear
    "C1": (5.2, 20.6, 0), "C5": (5.2, 18.9, 0), "C3": (17.8, 20.6, 0), "C6": (17.8, 18.9, 0),
    "C4": (5.2, 33.4, 0), "C7": (5.2, 35.1, 0), "C2": (17.8, 33.4, 0), "C8": (17.8, 35.1, 0),
    "C9": (11.5, 18.4, 0), "C24": (11.5, 35.6, 0),
    "X1": (2.2, 23.6, 0),
    "R3": (2.2, 26.5, 0), "R4": (2.2, 28.3, 0), "R8": (2.2, 30.1, 0),
    "R5": (2.2, 31.9, 0), "R6": (2.2, 33.7, 0), "R7": (2.2, 35.5, 0),
    # memories on the right, pull-ups between them and the FPGA
    "U2": (39.0, 17.0, 0), "C16": (25.2, 15.5, 0),
    "U3": (39.0, 31.0, 90), "C17": (39.0, 38.6, 0),
    "R10": (25.2, 24.5, 0), "R12": (25.2, 26.3, 0), "R14": (25.2, 28.1, 0), "R15": (25.2, 29.9, 0),
    "R9": (21.3, 24.5, 0), "R11": (21.3, 26.3, 0), "R13": (21.3, 28.1, 0),
    # console-detect divider
    "R1": (2.2, 37.3, 0), "R2": (2.2, 39.1, 0),
    # level shifters in a row above the fingers, console side (A on U4-U6, B on U7) facing down
    "U6": (4.3, 47.2, 90), "U4": (13.2, 47.2, 90), "U5": (34.0, 47.2, 90), "U7": (43.5, 47.2, 270),
    "C20": (4.3, 42.0, 0), "C18": (13.2, 42.0, 0), "C19": (34.0, 42.0, 0),
    "C21": (41.5, 42.0, 0), "C22": (45.5, 42.0, 0),
    # test pads
    "TP5": (8.0, 39.9, 0), "TP6": (10.5, 39.9, 0),
    "TP4": (35.0, 39.9, 0), "TP3": (42.5, 39.9, 0), "TP2": (45.0, 39.9, 0), "TP1": (47.5, 39.9, 0),
}

# Courtyard extents around the footprint origin, unrotated: (x0, x1, y0, y1), from the KiCad footprints.
_C0603 = (-1.48, 1.48, -0.73, 0.73)
CRTYD = {
    "R": _C0603, "C": _C0603,
    "D": (-2.35, 2.35, -1.15, 1.15),
    "J2": (-5.32, 5.32, -5.27, 4.15),
    "U1": (-5.33, 5.33, -5.33, 5.33), "U10": (-2.6, 2.6, -2.6, 2.6), "U11": (-2.05, 2.05, -1.7, 1.7),
    "U2": (-10.73, 10.73, -6.25, 6.25), "U3": (-5.93, 5.93, -9.2, 9.2),
    "U4": (-3.85, 3.85, -3.5, 3.5), "U5": (-3.85, 3.85, -3.5, 3.5), "U6": (-3.85, 3.85, -3.5, 3.5),
    "U7": (-3.85, 3.85, -4.15, 4.15), "U8": (-1.93, 1.93, -1.7, 1.7), "U9": (-2.05, 2.05, -1.7, 1.7),
    "X1": (-1.5, 1.5, -1.45, 1.45), "Y1": (-2.1, 2.1, -1.75, 1.75),
    "TP": (-1.0, 1.0, -1.0, 1.0),
}


def box(ref, layout=None, crtyd=None):
    layout, crtyd = layout or LAYOUT, crtyd or CRTYD
    x, y, rot = layout[ref]
    key = ref if ref in crtyd else ref.rstrip("0123456789")
    x0, x1, y0, y1 = crtyd[key]
    a = math.radians(-rot)
    pts = [(cx * math.cos(a) - cy * math.sin(a), cx * math.sin(a) + cy * math.cos(a))
           for cx in (x0, x1) for cy in (y0, y1)]
    return (x + min(p[0] for p in pts), y + min(p[1] for p in pts), x + max(p[0] for p in pts), y + max(p[1] for p in pts))


def problems(layout=None, crtyd=None):
    layout = layout or LAYOUT
    # component zone in the board frame (shell frame -> board frame)
    zx0 = S["width"] / 2 - S["cavity_width"] / 2 + S["side_rib_w"] - PCB_X_IN_SHELL
    zx1 = S["width"] / 2 + S["cavity_width"] / 2 - S["side_rib_w"] - PCB_X_IN_SHELL
    zy0 = H - (S["cross_rib_high_y"] - PCB_INSET_Y)
    zy1 = H - (S["cross_rib_low_y"] - PCB_INSET_Y)
    out = []
    boxes = {r: box(r, layout, crtyd) for r in layout if r != "J1"}
    for r, (x0, y0, x1, y1) in boxes.items():
        if r == "J2":   # the receptacle's mouth deliberately overhangs the top edge
            y0 = max(y0, zy0)
        if x0 < zx0 or x1 > zx1 or y0 < zy0 or y1 > zy1:
            out.append(f"{r} outside the zone x {zx0:.2f}-{zx1:.2f} y {zy0:.2f}-{zy1:.2f}: {x0:.2f},{y0:.2f},{x1:.2f},{y1:.2f}")
        if x1 > P["notch_x0"] and y0 < H - P["notch_y0"]:
            out.append(f"{r} in the lock notch")
        for hx, hy, d in HOLES:
            keep = d / 2 + 0.5
            nx, ny = min(max(hx, x0), x1), min(max(hy, y0), y1)
            if math.hypot(nx - hx, ny - hy) < keep:
                out.append(f"{r} within {keep:.2f} of the hole at ({hx}, {hy})")
    refs = sorted(boxes)
    for i, a in enumerate(refs):
        for b in refs[i + 1:]:
            A, B = boxes[a], boxes[b]
            if A[0] < B[2] and B[0] < A[2] and A[1] < B[3] and B[1] < A[3]:
                out.append(f"courtyards overlap: {a} {b}")
    return out


if __name__ == "__main__":
    bad = problems()
    print("\n".join(bad) or f"layout ok: {len(LAYOUT)} parts, no courtyard, zone, notch or hole clashes")
    sys.exit(1 if bad else 0)
