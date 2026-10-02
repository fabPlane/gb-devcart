"""Tiny client for the fabdesk daemon's tool endpoint (same call as `fabpcb tool call`)."""
import json
import subprocess
from pathlib import Path

PROJECT = "prj_muqh2goie9a9a5228a"
SCRATCH = Path("/tmp/claude-0/-home-user/9f140ab8-b730-535b-a66a-9f6f80b11e1a/scratchpad")


def call(name, args, timeout=900, proj_dir="/home/user/fabdesk-projects/gb-devcart-r2-2"):
    args = {"project": PROJECT, **args}
    f = SCRATCH / f"req_{name}.json"
    f.write_text(json.dumps(args))
    out = subprocess.run(["/home/user/tools/fabtool.sh", name, f"@{f}"], capture_output=True, text=True,
                         timeout=timeout, env={"FABPROJ": proj_dir,
                                               "PATH": "/usr/local/bin:/usr/bin:/bin:/root/.bun/bin:/opt/node22/bin"})
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(out.stdout[-2000:] + out.stderr[-2000:])


def pads(refs):
    rows = []
    for i in range(0, len(refs), 4):
        r = call("pcb_inspect", {"references": refs[i:i + 4], "kinds": ["pads"], "limitPerKind": 200})
        res = r["json"]["results"]["pads"]
        assert not res["truncated"], refs[i:i + 4]
        rows += res["rows"]
    return rows, r["json"]["revision"]


R1 = dict(project="prj_muq09vhgc7de0ce740", proj_dir="/home/user/fabdesk-projects/gb-devcart")


def hole_keepouts(holes, layers, margin=0.5, n=24):
    """Rule areas keeping all copper off the shell holes (the DSN export does not carry Edge.Cuts circles)."""
    import math
    return [dict(name=f"hole_keepout_{i}", layers=layers, copper=True, vias=True, tracks=True, pads=False,
                 footprints=False,
                 points=[{"x": round(x + (d / 2 + margin) * math.cos(2 * math.pi * k / n), 3),
                          "y": round(y + (d / 2 + margin) * math.sin(2 * math.pi * k / n), 3)} for k in range(n)])
            for i, (x, y, d) in enumerate(holes)]
