#!/usr/bin/env python3
"""Check KiCad boards against the DMG cartridge shell (mech/dims.py) and write mech/out/fit.json.

    python3 mech/fit_check.py NAME=path/to/board.kicad_pcb [...]

Each board is placed in the shell the way a real cart sits: centred across, bottom edge 1.6 mm above
the shell's connector end, component side facing the label. Exit code 1 if any board fails.
"""
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dims import SHELL as S, PCB_STD as P, PCB_INSET_Y, COMPONENT_MAX_H  # noqa: E402

# max seated height above the PCB (datasheet / JEDEC maximums), matched on the footprint name
HEIGHTS = [
    ("PLCC-32", 3.56), ("USB_C_Receptacle_HRO_TYPE-C-31-M-12", 3.26), ("SOIC-28W", 2.65), ("SOIC-20W", 2.65),
    ("SOIC-14", 1.75), ("TSOP-I-48", 1.2), ("TSSOP", 1.2), ("QFN-88", 0.9), ("QFN-28", 0.8),
    ("SOT-23-5", 1.45), ("SOT-23-6", 1.45), ("SOT-23", 1.12), ("D_SOD-123", 1.35), ("C_1206", 1.6),
    ("C_0603", 0.9), ("R_0603", 0.55), ("Oscillator_SMD", 0.8), ("Crystal_SMD_3225", 0.8),
    ("TestPoint_Pad", 0.05), ("GB_Cart_Edge", 0.0),
]


def sexp_blocks(text, head):
    """Yield (start, end) of every top-level-ish '(head ' block."""
    for m in re.finditer(r"\(" + re.escape(head) + r"[\s\n]", text):
        depth, i = 0, m.start()
        while i < len(text):
            c = text[i]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    yield text[m.start():i + 1]
                    break
            elif c == '"':
                i = text.index('"', i + 1)
            i += 1


def num(s):
    return [float(v) for v in s.split()]


def parse(path):
    t = Path(path).read_text()
    thickness = float(re.search(r"\(thickness ([\d.]+)\)", t).group(1))
    layers = len(re.findall(r'\(\d+ "(?:F|B|In\d+)\.Cu"', t))
    edges, circles = [], []
    for kind in ("gr_line", "gr_arc", "gr_rect", "gr_circle"):
        for b in sexp_blocks(t, kind):
            if '"Edge.Cuts"' not in b:
                continue
            pts = [num(m) for m in re.findall(r"\((?:start|end|mid|center) ([-\d.]+ [-\d.]+)\)", b)]
            if kind == "gr_circle":
                c, e = pts[0], pts[1]
                circles.append((c[0], c[1], 2 * math.dist(c, e)))
            elif kind == "gr_rect":
                (x0, y0), (x1, y1) = pts
                edges += [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
            else:
                edges += pts
    xs, ys = [p[0] for p in edges], [p[1] for p in edges]
    bb = (min(xs), min(ys), max(xs), max(ys))
    fps = []
    for b in sexp_blocks(t, "footprint"):
        name = re.match(r'\(footprint "([^"]+)"', b).group(1)
        ref = re.search(r'\(property "Reference" "([^"]+)"', b).group(1)
        tr = re.search(r"\(transform\s*\(translate ([-\d.]+ [-\d.]+)\)\s*\(rotate ([-\d.]+)\)", b)
        if tr:  # FabPlane KiCad fork: (transform (translate x y) (rotate r) ...)
            at, rot = num(tr.group(1)), float(tr.group(2))
        else:   # stock KiCad: the footprint's own (at x y [r]) comes before any property
            m_at = re.search(r'\(footprint "[^"]+"[\s\S]*?\(at ([-\d.]+ [-\d.]+)(?: ([-\d.]+))?\)', b)
            at, rot = num(m_at.group(1)), float(m_at.group(2) or 0)
        side = "B" if '(layer "B.Cu")' in b[:300] else "F"
        cy = []
        for kind in ("fp_line", "fp_rect", "fp_poly", "fp_circle"):
            for g in sexp_blocks(b, kind):
                if '.CrtYd"' in g:
                    cy += [num(m) for m in re.findall(r"\((?:start|end|xy|center) ([-\d.]+ [-\d.]+)\)", g)]
        pads = []
        for p in sexp_blocks(b, "pad"):
            pm = re.match(r'\(pad "([^"]*)" (\w+) (\w+)', p)
            pa = num(re.search(r"\(at ([-\d.]+ [-\d.]+)", p).group(1))
            sz = num(re.search(r"\(size ([-\d.]+ [-\d.]+)\)", p).group(1))
            dr = re.search(r"\(drill ([-\d.]+)", p)
            pads.append(dict(num=pm.group(1), kind=pm.group(2), at=pa, size=sz, drill=float(dr.group(1)) if dr else 0))
        fps.append(dict(name=name, ref=ref, at=at, rot=rot, side=side, crtyd=cy, pads=pads))
    return dict(thickness=thickness, layers=layers, bbox=bb, edges=edges, circles=circles, fps=fps)


def rotate(p, deg):
    a = math.radians(-deg)  # KiCad rotation is counter-clockwise on screen (y down)
    return (p[0] * math.cos(a) - p[1] * math.sin(a), p[0] * math.sin(a) + p[1] * math.cos(a))


def check(name, path):
    b = parse(path)
    x0, y0, x1, y1 = b["bbox"]
    w, h = x1 - x0, y1 - y0
    ox = (S["width"] - w) / 2            # board left edge in the shell frame
    to_shell = lambda x, y: (ox + (x - x0), PCB_INSET_Y + (y1 - y))   # noqa: E731
    res, items = [], []

    def add(id_, label, ok, measured, required, severity="fail"):
        res.append(dict(id=id_, label=label, status="pass" if ok else severity, measured=measured, required=required))

    add("width", "Board width fits the shell cavity", w <= S["cavity_width"] - 0.3,
        f"{w:.2f} mm", f"≤ {S['cavity_width'] - 0.3:.1f} mm (cavity {S['cavity_width']} minus 0.15 clearance per side)")
    top_room = S["height"] - 1.6 - PCB_INSET_Y
    add("height", "Board height fits under the top wall", h <= top_room, f"{h:.2f} mm", f"≤ {top_room:.1f} mm")
    # outline points in the shell frame
    outline = [to_shell(px, py) for px, py in b["edges"]]
    nx0, ny0 = S["width"] - S["notch_w"] - 1.0, S["height"] - S["notch_d"] - 1.0
    in_notch = [p for p in outline if p[0] > nx0 + 1e-6 and p[1] > ny0 + 1e-6]
    corner = (ox + w, PCB_INSET_Y + h)
    blocked = bool(in_notch) or (corner[0] > nx0 and corner[1] > ny0 and not _has_notch(outline, nx0, ny0))
    add("notch", "Clears the DMG power-lock notch (top right)", not blocked,
        "board corner reaches the notch" if blocked else "clear", f"nothing at x > {nx0:.1f}, y > {ny0:.1f} (shell frame)")
    # holes for the screw tube and the locating post
    holes = [to_shell(c[0], c[1]) + (c[2],) for c in b["circles"]]
    for fp in b["fps"]:
        for p in fp["pads"]:
            if p["kind"] == "np_thru_hole" and p["drill"] > 1.5:
                q = rotate(p["at"], fp["rot"])
                holes.append(to_shell(fp["at"][0] + q[0], fp["at"][1] + q[1]) + (p["drill"],))
    def hole_near(x, y, dmin):
        best = min(holes, key=lambda hh: math.dist(hh[:2], (x, y)), default=None)
        return best, best is not None and math.dist(best[:2], (x, y)) <= 0.3 and best[2] >= dmin
    hb, ok = hole_near(S["width"] / 2, S["screw_y"], S["screw_tube_od"] + 0.2)
    add("screw", "Hole for the shell's screw tube", ok,
        f"Ø{hb[2]:.1f} at ({hb[0]:.1f}, {hb[1]:.1f})" if hb else "no hole",
        f"Ø ≥ {S['screw_tube_od'] + 0.2:.1f} at ({S['width'] / 2:.1f}, {S['screw_y']:.2f})")
    hp, ok = hole_near(S["width"] / 2, S["post_y"], S["post_d"] + 0.3)
    add("post", "Hole for the locating post", ok,
        f"Ø{hp[2]:.1f} at ({hp[0]:.1f}, {hp[1]:.1f})" if hp else "no hole",
        f"Ø ≥ {S['post_d'] + 0.3:.1f} at ({S['width'] / 2:.1f}, {S['post_y']:.2f}); or print the shell without the post", "warn")
    # edge fingers
    j = next((f for f in b["fps"] if "Cart_Edge" in f["name"] or f["ref"] == "J1"), None)
    fingers = []
    if j:
        for p in j["pads"]:
            q = rotate(p["at"], j["rot"])
            cx, cy = to_shell(j["at"][0] + q[0], j["at"][1] + q[1])
            fingers.append(dict(n=p["num"], x=cx, y=cy, w=p["size"][0], l=p["size"][1]))
    fingers.sort(key=lambda f: f["x"])
    if len(fingers) == 32:
        pitch = (fingers[-2]["x"] - fingers[1]["x"]) / 29
        p1_want = (S["width"] - P["width"]) / 2 + P["pin1_x"]
        p2_want = (S["width"] - P["width"]) / 2 + P["pin2_x"]
        add("pitch", "32 fingers at 1.5 mm pitch", abs(pitch - 1.5) < 0.01, f"{pitch:.3f} mm", "1.500 mm")
        add("finger_x", "Fingers line up with the console connector",
            abs(fingers[1]["x"] - p2_want) <= 0.25, f"pin 2 at x {fingers[1]['x']:.2f}", f"pin 2 at x {p2_want:.2f} ± 0.25")
        gap = min(f["y"] - f["l"] / 2 for f in fingers[1:-1]) - PCB_INSET_Y
        add("finger_gap", "Finger start above the board edge (pins 2-31)", 1.3 <= gap <= 1.8, f"{gap:.2f} mm", "1.5 mm (1.3-1.8)")
    else:
        add("pitch", "32 fingers at 1.5 mm pitch", False, f"{len(fingers)} fingers found", "32")
    # components: side, keep-out zones, height
    zone = (S["width"] / 2 - S["cavity_width"] / 2 + S["side_rib_w"], S["cross_rib_low_y"],
            S["width"] / 2 + S["cavity_width"] / 2 - S["side_rib_w"], S["cross_rib_high_y"])
    worst_h, outside, back = 0.0, [], []
    for fp in b["fps"]:
        if fp is j:
            continue
        hgt = next((v for k, v in HEIGHTS if k in fp["name"]), 1.0)
        if fp["crtyd"]:
            pts = [rotate(c, fp["rot"]) for c in fp["crtyd"]]
            pts = [to_shell(fp["at"][0] + c[0], fp["at"][1] + c[1]) for c in pts]
        else:
            pts = [to_shell(*fp["at"])]
        xs_, ys_ = [p[0] for p in pts], [p[1] for p in pts]
        box = (min(xs_), min(ys_), max(xs_), max(ys_))
        items.append(dict(ref=fp["ref"], box=box, h=hgt, side=fp["side"], pkg=fp["name"].split(":")[-1]))
        if fp["side"] == "B":
            back.append(fp["ref"])
        # a USB-C receptacle may cross the top cross rib: the r2 shell cuts the rib and wall over it
        # (checked separately by "usb")
        top = S["height"] if "USB_C" in fp["name"] else zone[3]
        if hgt > 0.1 and (box[0] < zone[0] or box[2] > zone[2] or box[1] < zone[1] or box[3] > top):
            outside.append(fp["ref"])
        worst_h = max(worst_h, hgt)
    tallest = max(items, key=lambda i: i["h"]) if items else None
    add("height_parts", "Tallest part fits under the label side", worst_h <= COMPONENT_MAX_H,
        f"{tallest['ref']} {tallest['pkg']} {worst_h:.2f} mm" if tallest else "-",
        f"≤ {COMPONENT_MAX_H:.1f} mm (printed shell; an OEM shell has about 3.6)",
        "warn" if worst_h <= 3.6 else "fail")
    add("zone", "Parts stay between the shell ribs and above the connector mouth", not outside,
        ", ".join(outside[:12]) + (" …" if len(outside) > 12 else "") if outside else "all inside",
        f"x {zone[0]:.2f}-{zone[2]:.2f}, y {zone[1]:.1f}-{zone[3]:.1f} (shell frame)")
    add("back", "Nothing on the back side (0.35-0.55 mm behind the board)", not back,
        ", ".join(back) if back else "none", "no B-side parts")
    add("thickness", "Board thickness in the file", 0.75 <= b["thickness"] <= 1.05, f"{b['thickness']:.2f} mm",
        "0.8 or 1.0 mm (set it in the fab order if the file differs)", "warn")
    usb = next((i for i in items if "USB_C" in i["pkg"]), None)
    if usb:
        add("usb", "USB-C mouth reaches the shell's top edge", usb["box"][3] >= S["height"] - 1.2,
            f"connector front at y {usb['box'][3]:.1f}", f"≥ {S['height'] - 1.2:.1f} (custom shell has the opening)")
    verdict = "fail" if any(r["status"] == "fail" for r in res) else ("warn" if any(r["status"] == "warn" for r in res) else "pass")
    return dict(name=name, file=str(path), verdict=verdict, size=[round(w, 2), round(h, 2)], layers=b["layers"],
                thickness=b["thickness"], offset=[round(ox, 3), PCB_INSET_Y],
                outline=[[round(x, 3), round(y, 3)] for x, y in outline], holes=[[round(v, 3) for v in hh] for hh in holes],
                fingers=[[round(f["x"], 3), round(f["y"], 3), f["w"], f["l"]] for f in fingers],
                parts=[dict(ref=i["ref"], box=[round(v, 2) for v in i["box"]], h=i["h"], side=i["side"], pkg=i["pkg"]) for i in items],
                checks=res)


def _has_notch(outline, nx0, ny0):
    return any(p[0] < nx0 + 6 and p[1] > ny0 for p in outline) and not any(p[0] > nx0 and p[1] > ny0 for p in outline)


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "out"
    out.mkdir(exist_ok=True)
    boards = [check(*a.split("=", 1)) for a in sys.argv[1:]]
    doc = dict(shell=S, pcb_std=P, inset=PCB_INSET_Y, component_max_h=COMPONENT_MAX_H, boards=boards)
    json.dump(doc, open(out / "fit.json", "w"), indent=1)
    for bd in boards:
        print(f"{bd['name']:10s} {bd['verdict'].upper():5s} {bd['size'][0]} x {bd['size'][1]} mm, {bd['layers']} layers")
        for r in bd["checks"]:
            print(f"   [{r['status']:4s}] {r['label']}: {r['measured']}  (need {r['required']})")
    sys.exit(1 if any(bd["verdict"] == "fail" for bd in boards) else 0)
