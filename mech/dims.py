"""Game Boy (DMG/GBC) cartridge mechanical reference, in mm. Single source for the shell model and
the fit check. Numbers and sources: docs/gb-cart-mechanical.md (GK = gekkio/gb-hardware CC BY 4.0,
RGR/FUN = Printables shell STLs, WP = Wikipedia). Where sources disagree the conservative value is used.

Shell frame: x across (0 at the left edge seen from the label side), y up from the shell's bottom
(connector) end, z through the thickness (0 = back outer face, +z = label side).
PCB frame: origin at the PCB bottom-left corner, fingers at the bottom, component side facing +z.
"""

SHELL = dict(
    width=57.0, height=65.0, thickness=7.8,          # WP/RGR/FUN; sources give 7.5-7.8, 65.0-65.5
    corner_r=1.0,
    back_wall=1.15,                                  # RGR (FUN 1.3)
    front_wall=2.0,                                  # rails; 1.65 under the label recess
    pcb_front_z=2.5,                                 # PCB component face plane above the back face
    front_inner_z=5.8,                               # -> 3.3 mm component height on the label side
    mouth_depth=10.0,                                # connector mouth at the bottom end
    mouth_front_inner_z=6.45,
    cavity_width=53.2,
    side_rib_w=1.45,                                 # component zone 50.3 wide between the ribs
    cross_rib_low_y=11.4, cross_rib_high_y=61.7,     # component zone along y (shell frame)
    notch_w=4.8, notch_d=3.3,                        # DMG power-lock notch, top right seen from the label
    label_w=44.0, label_h=35.5, label_depth=0.35,
    label_bottom_y=13.0,
    screw_y=16.95, screw_tube_od=7.0, screw_tube_top_z=2.9,
    front_boss_od=4.0, pilot_d=1.5,
    post_y=16.95 + 24.95, post_d=1.9, post_top_z=3.15,
    counterbore_d=5.1, counterbore_depth=2.25, shank_d=2.25,
)

# OEM-style PCB (gekkio GB-CART256K-A outline, CC BY 4.0) — the target for r1.1 / r2.1
PCB_STD = dict(
    width=51.4, height=61.0, thickness=1.0,          # GK 1.0; MouseBite and many repros use 0.8
    tongue_x0=1.1, tongue_x1=50.3, tongue_h=8.6,     # finger tongue, R0.9 bottom corners
    notch_x0=47.4, notch_y0=58.4,                    # top-right notch 4.0 x 2.6
    big_hole=(25.7, 15.35, 7.2),                     # the shell's screw tube passes through
    small_hole=(25.7, 40.35, 2.3),                   # locating post
    finger_pitch=1.5, finger_n=32, finger_w=1.0, finger_len=5.5, finger_gap=1.5,
    pin1_x=2.3, pin2_x=3.95,
)
PCB_INSET_Y = 1.6          # PCB bottom edge above the shell's bottom end (GK hole 15.35 vs screw 16.95)
PCB_X_IN_SHELL = (SHELL["width"] - PCB_STD["width"]) / 2   # PCB centred across the shell
COMPONENT_MAX_H = SHELL["front_inner_z"] - SHELL["pcb_front_z"]   # 3.3

# r2: USB-C on the top edge needs a custom shell: a cutout in the top wall plus a thinner front wall
USB_C = dict(body_w=8.94, body_len=7.35, height=3.26, mouth_w=9.4, mouth_h=3.6, pocket_extra=0.8)
