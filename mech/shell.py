#!/usr/bin/env python3
"""Parametric Game Boy (DMG/GBC/Chromatic) cartridge shell for GB DEVCART, built with CadQuery.

    pip install cadquery && python3 mech/shell.py      # -> mech/out/*.step, *.stl, *.glb

Two halves split at z = SPLIT_Z. Dimensions come from mech/dims.py (sourced in
docs/gb-cart-mechanical.md). Variants:
  shell_std  : plain DMG-style shell (r1.1-style boards)
  shell_usb  : r2 shell with a USB-C opening in the top wall, the top cross rib removed over the
               connector and the front wall thinned above it for clearance
Printing: PETG or ABS, 0.12-0.16 mm layers, back half face-down, front half label-face-down.
The shell is a community-measured replica, not a Nintendo drawing; test-fit before a batch.
"""
import os
import sys
from pathlib import Path

import cadquery as cq

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dims import SHELL as S, USB_C, PCB_STD, PCB_INSET_Y, PCB_X_IN_SHELL  # noqa: E402

OUT = Path(__file__).resolve().parent / "out"
SPLIT_Z = 4.0           # back half 0..4.0, front half 4.0..7.8
SIDE_WALL = (S["width"] - S["cavity_width"]) / 2   # 1.9
CX = S["width"] / 2


def outer():
    body = (cq.Workplane("XY").box(S["width"], S["height"], S["thickness"], centered=(False, False, False))
            .edges("|Z").fillet(S["corner_r"]))
    notch = cq.Workplane("XY").box(S["notch_w"], S["notch_d"], 20, centered=(False, False, True)) \
        .translate((S["width"] - S["notch_w"], S["height"] - S["notch_d"], 0))
    return body.cut(notch)


def cavity(z0, z1, y0=None):
    """The inner pocket between the side walls, from y0 to under the top wall."""
    y0 = S["back_wall"] if y0 is None else y0
    top_wall = 1.6
    return cq.Workplane("XY").box(S["cavity_width"], S["height"] - top_wall - y0, z1 - z0,
                                  centered=(False, False, False)).translate((SIDE_WALL, y0, z0))


def back_half():
    half = outer().intersect(cq.Workplane("XY").box(100, 100, SPLIT_Z, centered=(True, True, False)).translate((CX, 30, 0)))
    half = half.cut(cavity(S["back_wall"], 20, y0=-1))                       # open at the connector end
    t = PCB_STD["thickness"]
    pcb_back = S["pcb_front_z"] - t
    # perimeter ledge the PCB rests on (inside the side walls, above the mouth)
    for x in (SIDE_WALL, S["width"] - SIDE_WALL - 1.0):
        half = half.union(cq.Workplane("XY").box(1.0, S["height"] - 1.6 - S["mouth_depth"], pcb_back - S["back_wall"],
                                                  centered=(False, False, False))
                          .translate((x, S["mouth_depth"], S["back_wall"])))
    # back lip under the PCB edge at the mouth
    half = half.union(cq.Workplane("XY").box(49.0, 0.75, 2.0 - S["back_wall"], centered=(True, False, False))
                      .translate((CX, 0, S["back_wall"])))
    # screw tube through the PCB's big hole, with counterbore + shank hole from the back face
    tube = cq.Workplane("XY").circle(S["screw_tube_od"] / 2).extrude(S["screw_tube_top_z"]).translate((CX, S["screw_y"], 0))
    half = half.union(tube)
    half = half.cut(cq.Workplane("XY").circle(S["counterbore_d"] / 2).extrude(S["counterbore_depth"]).translate((CX, S["screw_y"], 0)))
    half = half.cut(cq.Workplane("XY").circle(S["shank_d"] / 2).extrude(10).translate((CX, S["screw_y"], 0)))
    # locating post through the PCB's small hole
    post = cq.Workplane("XY").circle(S["post_d"] / 2).extrude(S["post_top_z"]).translate((CX, S["post_y"], 0))
    return half.union(post)


def front_half(usb_x=None):
    half = outer().intersect(cq.Workplane("XY").box(100, 100, 20, centered=(True, True, False)).translate((CX, 30, SPLIT_Z)))
    inner_z = S["front_inner_z"]
    half = half.cut(cavity(SPLIT_Z - 1, inner_z, y0=S["mouth_depth"]))
    # connector mouth: deeper pocket at the bottom end, open to the slot
    half = half.cut(cq.Workplane("XY").box(S["cavity_width"], S["mouth_depth"] + 1, S["mouth_front_inner_z"] - SPLIT_Z + 1,
                                           centered=(False, False, False)).translate((SIDE_WALL, -1, SPLIT_Z - 1)))
    # frame that clamps the PCB front face: side ribs and two cross ribs down to the PCB plane
    rib_h = inner_z - S["pcb_front_z"]
    for x in (SIDE_WALL, S["width"] - SIDE_WALL - S["side_rib_w"]):
        half = half.union(cq.Workplane("XY").box(S["side_rib_w"], S["height"] - 1.6 - S["mouth_depth"], rib_h,
                                                  centered=(False, False, False)).translate((x, S["mouth_depth"], S["pcb_front_z"])))
    for y in (S["cross_rib_low_y"] - 1.0, S["cross_rib_high_y"]):
        rib = cq.Workplane("XY").box(S["cavity_width"], 1.0, rib_h, centered=(False, False, False)) \
            .translate((SIDE_WALL, y, S["pcb_front_z"]))
        if usb_x is not None and y == S["cross_rib_high_y"]:
            rib = rib.cut(cq.Workplane("XY").box(USB_C["mouth_w"] + 2, 5, 10, centered=(True, True, False))
                          .translate((usb_x, y, 0)))
        half = half.union(rib)
    # front boss for the screw
    boss = cq.Workplane("XY").circle(S["front_boss_od"] / 2).extrude(inner_z - S["screw_tube_top_z"]).translate((CX, S["screw_y"], S["screw_tube_top_z"]))
    half = half.union(boss).cut(cq.Workplane("XY").circle(S["pilot_d"] / 2).extrude(inner_z).translate((CX, S["screw_y"], 0)))
    # label recess
    half = half.cut(cq.Workplane("XY").box(S["label_w"], S["label_h"], S["label_depth"] + 1, centered=(True, False, False))
                    .translate((CX, S["label_bottom_y"], S["thickness"] - S["label_depth"])))
    if usb_x is not None:
        top = S["height"]
        # opening in the top wall, from the PCB face up to the connector mouth height
        half = half.cut(cq.Workplane("XY").box(USB_C["mouth_w"], 6, USB_C["mouth_h"], centered=(True, False, False))
                        .translate((usb_x, top - 4, S["pcb_front_z"])))
        # thinner front wall over the connector body for clearance (3.26 tall part vs 3.3 room)
        half = half.cut(cq.Workplane("XY").box(USB_C["body_w"] + 1.0, USB_C["body_len"] + 1.0, USB_C["pocket_extra"] + 1,
                                               centered=(True, False, False))
                        .translate((usb_x, top - USB_C["body_len"] - 0.5, inner_z - 1)))
    return half


def pcb_std():
    """OEM-style PCB outline (gekkio GB-CART256K-A dimensions) placed in the shell, for the viewer."""
    P = PCB_STD
    t = P["thickness"]
    body = cq.Workplane("XY").box(P["width"], P["height"] - P["tongue_h"], t, centered=False).translate((0, P["tongue_h"], 0))
    tongue = cq.Workplane("XY").box(P["tongue_x1"] - P["tongue_x0"], P["tongue_h"] + 0.01, t, centered=False).translate((P["tongue_x0"], 0, 0))
    pcb = body.union(tongue)
    pcb = pcb.cut(cq.Workplane("XY").box(P["width"] - P["notch_x0"], P["height"] - P["notch_y0"], 5, centered=False)
                  .translate((P["notch_x0"], P["notch_y0"], -1)))
    for hx, hy, d in (P["big_hole"], P["small_hole"]):
        pcb = pcb.cut(cq.Workplane("XY").circle(d / 2).extrude(5).translate((hx, hy, -1)))
    return pcb.translate((PCB_X_IN_SHELL, PCB_INSET_Y, S["pcb_front_z"] - t))


def export(shape, name):
    OUT.mkdir(exist_ok=True)
    cq.exporters.export(shape, str(OUT / f"{name}.step"))
    cq.exporters.export(shape, str(OUT / f"{name}.stl"), tolerance=0.02, angularTolerance=0.15)


if __name__ == "__main__":
    usb_x = float(os.environ.get("USB_X", PCB_X_IN_SHELL + PCB_STD["width"] / 2 - 6.0))
    back = back_half()
    export(back, "shell_back")
    export(front_half(), "shell_front_std")
    export(front_half(usb_x), "shell_front_usb")
    export(pcb_std(), "pcb_std_outline")
    for n in ("shell_back", "shell_front_std", "shell_front_usb", "pcb_std_outline"):
        bb = cq.importers.importStep(str(OUT / f"{n}.step")).val().BoundingBox()
        print(f"{n:18s} {bb.xlen:6.2f} x {bb.ylen:6.2f} x {bb.zlen:5.2f}  z {bb.zmin:.2f}..{bb.zmax:.2f}")
