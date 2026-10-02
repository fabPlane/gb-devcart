#!/usr/bin/env python3
"""Drop a via next to every GND / 3V3 SMD pad (and a via grid in the QFN exposed pads) so they reach
the In1.Cu GND and In2.Cu 3V3 planes, then add both planes. Applied through fabdesk's
native_edit_transaction, so it is one atomic, revision-checked edit of the board.

    python3 r2/hw/power_vias.py [--apply]     # preview by default

Vias are 0.5/0.3 mm (JLC standard). Each candidate keeps 0.15 mm copper clearance to every
other-net pad and via, stays 0.5 mm from the board edge and holes, and out of the finger area.
"""
import json
import math
import sys

import fab_api as A
import layout_dmg as L

PLANES = {"GND": "In1.Cu", "3V3": "In2.Cu"}
VIA_D, VIA_DRILL, CLR = 0.5, 0.3, 0.15
FINGER_TOP = L.H - 7.3          # copper keeps above the fingers' top end (7.0) plus margin
EP = {("U1", "89"): 3, ("U10", "29"): 1}   # exposed pads: n x n via grid
QFN = {"U1": "89", "U10": "29"}            # GND pins join their exposed pad with a short inward stub
# fine-pitch ICs: vias only straight out from the pin (or under the body for gull-wing packages),
# never beside the pin where they would block the neighbours' fan-out
FINE = {"U1", "U2", "U3", "U4", "U5", "U6", "U7", "U8", "U9", "U10", "U11"}


def rect(p):
    """Pad as an axis-aligned rectangle on the board (sizes come in the footprint frame)."""
    rot = L.LAYOUT[p["component"]][2] % 180
    w, h = (p["height"], p["width"]) if rot == 90 else (p["width"], p["height"])
    return (p["x"] - w / 2, p["y"] - h / 2, p["x"] + w / 2, p["y"] + h / 2)


def d_rect(x, y, r):
    dx = max(r[0] - x, 0, x - r[2])
    dy = max(r[1] - y, 0, y - r[3])
    return math.hypot(dx, dy)


def seg_rect_dist(a, b, r, n=12):
    return min(d_rect(a[0] + (b[0] - a[0]) * t / n, a[1] + (b[1] - a[1]) * t / n, r) for t in range(n + 1))


def inside_board(x, y, m):
    pts = L.outline()
    inside = False
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            inside = not inside
        # distance to edge
        t = max(0, min(1, ((x - x0) * (x1 - x0) + (y - y0) * (y1 - y0)) / ((x1 - x0) ** 2 + (y1 - y0) ** 2 or 1)))
        if math.hypot(x - (x0 + t * (x1 - x0)), y - (y0 + t * (y1 - y0))) < m:
            return False
    if not inside:
        return False
    return all(math.hypot(x - hx, y - hy) >= d / 2 + m for hx, hy, d in L.HOLES)


def main(apply):
    pads, rev = A.pads(sorted(L.LAYOUT))
    smd = [p for p in pads if p["layerNames"] == ["F.Cu"]]
    others = [(rect(p), p["net"]) for p in pads]
    vias, tracks, skipped = [], [], []

    def ok(x, y, net, track_from=None, width=0.25):
        if y > FINGER_TOP or not inside_board(x, y, 0.5 + VIA_D / 2):
            return False
        for r, n in others:
            if n != net and d_rect(x, y, r) < VIA_D / 2 + CLR:
                return False
            if track_from and n != net and seg_rect_dist(track_from, (x, y), r) < width / 2 + CLR:
                return False
        for vx, vy, n in vias:
            if math.hypot(vx - x, vy - y) < VIA_D + (CLR if n != net else 0.1):
                return False
        return True

    for p in smd:
        net = p["net"]
        if net not in PLANES:
            continue
        key = (p["component"], p["number"])
        if key in EP:
            n = EP[key]
            pitch = min(p["width"], p["height"]) / (n + 0.5)
            for i in range(n):
                for j in range(n):
                    vias.append((p["x"] + (i - (n - 1) / 2) * pitch, p["y"] + (j - (n - 1) / 2) * pitch, net))
            continue
        if p["component"] == "J1":
            continue   # the GND finger joins the plane through its own via below
        cx, cy = L.LAYOUT[p["component"]][:2]
        r = rect(p)
        w, h = r[2] - r[0], r[3] - r[1]
        # outward direction: along the pad's long axis, away from the footprint centre
        if w >= h:
            dirs = [(math.copysign(1, p["x"] - cx) if p["x"] != cx else 1, 0)]
        else:
            dirs = [(0, math.copysign(1, p["y"] - cy) if p["y"] != cy else 1)]
        width = 0.15 if p["component"] in QFN else round(min(0.25, min(w, h)), 3)
        if p["component"] in QFN and net == "GND":
            ep = next(q for q in pads if q["component"] == p["component"] and q["number"] == QFN[p["component"]])
            dx, dy = dirs[0]
            end = (p["x"] if dx == 0 else ep["x"] + dx * (ep["width"] / 2 - 0.2),
                   p["y"] if dy == 0 else ep["y"] + dy * (ep["height"] / 2 - 0.2))
            tracks.append(dict(start={"reference": p["component"], "pad": p["number"]},
                               end={"x": round(end[0], 3), "y": round(end[1], 3)}, width=width, layer="F.Cu", net=net))
            continue
        if p["component"] in FINE:
            dirs += [] if p["component"] in QFN else [(-dirs[0][0], -dirs[0][1])]
        else:
            dirs += [(-dirs[0][0], -dirs[0][1]), (dirs[0][1], dirs[0][0]), (-dirs[0][1], -dirs[0][0])]
        done = False
        for dist in (0.45, 0.6, 0.8, 1.0, 1.3, 1.6, 2.0, 2.5, 3.0):
            for dx, dy in dirs:
                half = (w if dx else h) / 2
                x = round(p["x"] + dx * (half + dist), 3)
                y = round(p["y"] + dy * (half + dist), 3)
                edge = (p["x"] + dx * half, p["y"] + dy * half)
                if ok(x, y, net, edge, width):
                    vias.append((x, y, net))
                    tracks.append(dict(start={"reference": p["component"], "pad": p["number"]}, end={"x": x, "y": y},
                                       width=width, layer="F.Cu", net=net))
                    done = True
                    break
            if done:
                break
        if not done:
            skipped.append(f"{p['component']}.{p['number']} ({net})")
    # GND finger (pin 32) and the console VCC finger stay on F.Cu; give the GND finger plane vias
    for p in pads:
        if p["component"] == "J1" and p["net"] == "GND":
            for x in (p["x"] - 0.0,):
                y = round(FINGER_TOP - 0.6, 3)
                vias.append((round(x, 3), y, "GND"))
                tracks.append(dict(start={"reference": "J1", "pad": p["number"]}, end={"x": round(x, 3), "y": y},
                                   width=0.5, layer="F.Cu", net="GND"))

    inset = 0.3
    def poly(m):
        x0, x1 = m, L.W - m
        t0, t1, th = L.P["tongue_x0"] + m, L.P["tongue_x1"] - m, L.H - L.P["tongue_h"] - m
        return [(x0, m), (L.P["notch_x0"] - m, m), (L.P["notch_x0"] - m, L.H - L.P["notch_y0"] + m),
                (x1, L.H - L.P["notch_y0"] + m), (x1, th), (t1, th), (t1, L.H - m), (t0, L.H - m), (t0, th), (x0, th)]
    zones = [dict(points=[{"x": round(x, 3), "y": round(y, 3)} for x, y in poly(inset)], layers=[layer], net=net,
                  name=f"{net}_{layer.split('.')[0]}", clearance=0.2, minThickness=0.2, priority=0)
             for net, layer in PLANES.items()]
    req = {"mode": "apply" if apply else "preview", "expectedPcbRevision": rev,
           "geometry": {"vias": [dict(position={"x": round(x, 3), "y": round(y, 3)}, diameter=VIA_D, drill=VIA_DRILL,
                                      layers=["F.Cu", "B.Cu"], net=n) for x, y, n in vias],
                        "tracks": tracks, "zones": zones}}
    (A.SCRATCH / "power_vias.json").write_text(json.dumps(req, indent=1))
    print(f"{len(vias)} vias, {len(tracks)} stubs, {len(zones)} planes; skipped: {skipped or 'none'}")
    r = A.call("native_edit_transaction", req)
    print(json.dumps(r, indent=1)[:2500])


if __name__ == "__main__":
    main("--apply" in sys.argv)
