#!/usr/bin/env python3
"""Estimate a JLCPCB order (bare PCB + parts + assembly) from parts_check.json and PCB quotes.

    python3 scripts/jlc_check.py [BOARD_DIR]      # first: live part prices / stock
    python3 scripts/jlc_cost.py NAME BOARD_DIR PCB_QUOTES_JSON SMD_JOINTS THT_JOINTS

PCB_QUOTES_JSON maps "qty" -> order total in USD from JLC's quote engine (ENIG, 1.0 mm).
Assembly fees are JLCPCB's published fee table (help page "PCB Assembly Cost", 2026-09-09):
Economic: $8.18 setup + $1.53 stencil + $3.07 per unique Extended part; Standard: $25.56 setup +
$8.21 stencil + $1.53 per unique part. SMT joints $0.0016 each. Hand-soldered THT joints (Standard
only) are an estimate: $0.0173 each plus a $3.50 setup.
Parts: unit price at the bought quantity, which is per-board count x boards + JLC's attrition
(lossNumber), and at least the part's minimum (leastPatchNumber).
"""
import json
import sys
from pathlib import Path


def unit(prices, n):
    for p in prices:
        if p["startNumber"] <= n and (p["endNumber"] == -1 or n <= p["endNumber"]):
            return p["productPrice"]
    return prices[-1]["productPrice"] if prices else 0.0


def estimate(parts, pcb, n, smd, tht):
    parts_cost, short = 0.0, []
    for p in parts:
        buy = max(p["per_board"] * n + (p["loss"] or 0), p["least"] or 0)
        parts_cost += unit(p["prices"], buy) * buy
        if p["stock"] < buy:
            short.append(f"{p['lcsc']} ({','.join(p['refs'])}): need {buy}, stock {p['stock']}")
    ext = sum(1 for p in parts if p["library"] != "base")
    joints = max(smd * 0.0016, 0.48) * n
    econ = 8.18 + 1.53 + 3.07 * ext + joints
    std = 25.56 + 8.21 + 1.53 * len(parts) + joints + ((3.50 + tht * 0.0173 * n) if tht else 0)
    return dict(n=n, pcb=pcb, parts=round(parts_cost, 2), econ_fees=round(econ, 2), std_fees=round(std, 2),
                econ_total=round(pcb + parts_cost + econ, 2), std_total=round(pcb + parts_cost + std, 2),
                short=short, ext=ext, unique=len(parts))


def main():
    name, board, quotes, smd, tht = sys.argv[1], Path(sys.argv[2]), json.load(open(sys.argv[3])), int(sys.argv[4]), int(sys.argv[5])
    parts = json.load(open(board / "exports/jlcpcb/parts_check.json"))
    rows = [estimate(parts, quotes[str(n)], n, smd, tht) for n in (5, 10, 30, 100)]
    (board / "exports/jlcpcb/cost_estimate.json").write_text(json.dumps(rows, indent=1))
    print(f"{name}: {rows[0]['unique']} unique parts ({rows[0]['ext']} Extended), {smd} SMT + {tht} THT joints")
    for r in rows:
        print(f"  {r['n']:>3} boards: PCB ${r['pcb']:.2f}  parts ${r['parts']:.2f}  "
              f"Economic ${r['econ_total']:.2f} (${r['econ_total'] / r['n']:.2f}/board)  "
              f"Standard ${r['std_total']:.2f} (${r['std_total'] / r['n']:.2f}/board)"
              + (f"  SHORT: {'; '.join(r['short'])}" if r["short"] else ""))


if __name__ == "__main__":
    main()
