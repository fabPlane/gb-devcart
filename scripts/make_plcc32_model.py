#!/usr/bin/env python3
"""Generate 3dmodels/PLCC-32_11.4x14.0mm_P1.27mm.step (JEDEC MS-016 PLCC-32, J-lead).

KiCad's official 3D library has no PLCC-32 model, so this builds one with CadQuery that lines up
with the KiCad footprint Package_LCC:PLCC-32_11.4x14.0mm_P1.27mm (origin = package centre, pin 1
at the centre of the top short edge; KiCad 3D +Y = footprint -Y).

    pip install cadquery && python3 scripts/make_plcc32_model.py
"""
from pathlib import Path

import cadquery as cq

OUT = Path(__file__).resolve().parent.parent / "3dmodels" / "PLCC-32_11.4x14.0mm_P1.27mm.step"

BODY_X, BODY_Y = 11.43, 13.97  # E, D body (mm)
Z0, Z1 = 0.6, 3.5  # body bottom / top above the board
PITCH = 1.27
LEAD_W, LEAD_T = 0.43, 0.20
LEAD_OUT = 0.35  # how far the J-bend sits outside the body
SHORT_N, LONG_N = 7, 9  # leads per short (X) / long (Y) side

body = (
    cq.Workplane("XY")
    .box(BODY_X, BODY_Y, Z1 - Z0, centered=(True, True, False))
    .translate((0, 0, Z0))
    .edges("|Z")
    .chamfer(0.5)
    .faces(">Z")
    .edges()
    .chamfer(0.25)
)
# pin-1 corner bevel (top-left in KiCad 3D view) and pin-1 dimple at top centre
body = body.cut(
    cq.Workplane("XY").box(2.0, 2.0, 10).rotate((0, 0, 0), (0, 0, 1), 45).translate((-BODY_X / 2, BODY_Y / 2, 0))
)
body = body.cut(cq.Workplane("XY").circle(0.5).extrude(0.15).translate((0, BODY_Y / 2 - 1.6, Z1 - 0.15)))


def j_lead(x: float, y: float, outward: tuple[float, float], width_along_x: bool) -> cq.Workplane:
    """Vertical lead plate just outside the body plus a short tuck under it."""
    ox, oy = outward
    wx, wy = (LEAD_W, LEAD_T) if width_along_x else (LEAD_T, LEAD_W)
    plate = cq.Workplane("XY").box(wx, wy, 2.2, centered=(True, True, False)).translate(
        (x + ox * LEAD_OUT, y + oy * LEAD_OUT, 0.15)
    )
    top = cq.Workplane("XY").box(
        LEAD_W if width_along_x else LEAD_OUT + 0.3,
        LEAD_OUT + 0.3 if width_along_x else LEAD_W,
        LEAD_T,
        centered=(True, True, False),
    ).translate((x + ox * LEAD_OUT / 2, y + oy * LEAD_OUT / 2, 2.15))
    foot = cq.Workplane("XY").box(
        LEAD_W if width_along_x else 0.9,
        0.9 if width_along_x else LEAD_W,
        LEAD_T,
        centered=(True, True, False),
    ).translate((x - ox * 0.2 + ox * LEAD_OUT, y - oy * 0.2 + oy * LEAD_OUT, 0.0))
    return plate.union(top).union(foot)


leads = None
for i in range(SHORT_N):
    x = (i - (SHORT_N - 1) / 2) * PITCH
    for y, oy in ((BODY_Y / 2, 1), (-BODY_Y / 2, -1)):
        lead = j_lead(x, y, (0, oy), True)
        leads = lead if leads is None else leads.union(lead)
for i in range(LONG_N):
    y = (i - (LONG_N - 1) / 2) * PITCH
    for x, ox in ((BODY_X / 2, 1), (-BODY_X / 2, -1)):
        leads = leads.union(j_lead(x, y, (ox, 0), False))

asm = cq.Assembly(name="PLCC-32")
asm.add(body, name="body", color=cq.Color(0.15, 0.15, 0.15))
asm.add(leads, name="leads", color=cq.Color(0.82, 0.82, 0.84))
OUT.parent.mkdir(exist_ok=True)
asm.save(str(OUT), "STEP")
print(f"wrote {OUT}")
