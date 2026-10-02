#!/usr/bin/env python3
"""Convert the shell STLs to compact JSON triangle lists for mech/fit.html (artifact hosts can't serve .stl).

    python3 mech/stl2json.py      # mech/out/*.stl -> mech/out/*.mesh.json
"""
import json
import struct
from pathlib import Path

OUT = Path(__file__).resolve().parent / "out"
for stl in sorted(OUT.glob("shell_*.stl")):
    b = stl.read_bytes()
    n = struct.unpack_from("<I", b, 80)[0]
    pos = []
    for i in range(n):
        v = struct.unpack_from("<9f", b, 84 + i * 50 + 12)
        pos.extend(round(x, 3) for x in v)
    (OUT / f"{stl.stem}.mesh.json").write_text(json.dumps({"positions": pos}, separators=(",", ":")))
    print(f"{stl.name}: {n} triangles")
