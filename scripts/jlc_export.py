#!/usr/bin/env python3
"""Write JLCPCB assembly files: exports/jlcpcb/{gerbers.zip, bom.csv, cpl.csv}.

    KICAD_CLI=/path/to/kicad-cli python3 scripts/jlc_export.py

BOM rows come from circuit.netlist.json (grouped by LCSC part number); CPL rows from
`kicad-cli pcb export pos`. Parts without an LCSC field (test pads, edge fingers) are not placed.
Check the rotation preview in JLC's order page: SOIC/PLCC reels sometimes need a +/-90 deg fix.
"""
import csv
import io
import json
import os
import subprocess
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "exports" / "jlcpcb"
KICAD_CLI = os.environ.get("KICAD_CLI", "kicad-cli")
BOARD = ROOT / "board.kicad_pcb"
LAYERS = "F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"


def run(*args: str) -> None:
    subprocess.run([KICAD_CLI, *args], check=True, stdout=subprocess.DEVNULL)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    comps = json.load(open(ROOT / "circuit.netlist.json"))["netlist"]["components"]
    lcsc = {c["ref"]: c for c in comps if c["fields"].get("LCSC")}

    # BOM: Comment, Designator, Footprint, LCSC Part #
    groups: dict[str, list[dict]] = defaultdict(list)
    for c in lcsc.values():
        groups[c["fields"]["LCSC"]].append(c)
    with open(OUT / "bom.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for part, cs in sorted(groups.items(), key=lambda kv: kv[1][0]["ref"]):
            refs = sorted((c["ref"] for c in cs), key=lambda r: (r[0], int(r[1:])))
            w.writerow([f'{cs[0]["value"]} {cs[0]["fields"].get("MPN", "")}'.strip(), ",".join(refs),
                        cs[0]["footprint"].split(":")[-1], part])

    with tempfile.TemporaryDirectory() as tmp:
        # CPL: Designator, Mid X, Mid Y, Layer, Rotation
        pos = Path(tmp) / "pos.csv"
        run("pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "front", "-o", str(pos), str(BOARD))
        with open(pos) as f, open(OUT / "cpl.csv", "w", newline="") as g:
            w = csv.writer(g)
            w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
            for row in csv.DictReader(f):
                if row["Ref"] in lcsc:
                    w.writerow([row["Ref"], f'{float(row["PosX"]):.4f}mm', f'{float(row["PosY"]):.4f}mm',
                                "Top" if row["Side"] == "top" else "Bottom", f'{float(row["Rot"]):.1f}'])

        # Gerbers + drill
        gdir = Path(tmp) / "gerbers"
        gdir.mkdir()
        run("pcb", "export", "gerbers", "--layers", LAYERS, "--no-protel-ext", "-o", str(gdir) + "/", str(BOARD))
        run("pcb", "export", "drill", "--format", "excellon", "--excellon-separate-th", "-o", str(gdir) + "/", str(BOARD))
        with zipfile.ZipFile(OUT / "gerbers.zip", "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(gdir.iterdir()):
                z.write(p, p.name)
    print(f"wrote {OUT}/gerbers.zip, bom.csv ({len(groups)} lines), cpl.csv ({len(lcsc)} parts)")


if __name__ == "__main__":
    main()
