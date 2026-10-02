#!/usr/bin/env python3
"""Check a JLC BOM against JLCPCB's live parts library: stock, Basic/Extended, price, MPN.

    python3 scripts/jlc_check.py [BOARD_DIR] [QTY]   # default: repo root (r1.1), 5 boards
Writes <BOARD_DIR>/exports/jlcpcb/parts_check.json and prints a table.
"""
import csv
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOARD = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT
QTY = int(sys.argv[2]) if len(sys.argv) > 2 else 5
API = "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList"


def lookup(code):
    req = urllib.request.Request(API, data=json.dumps({"keyword": code, "currentPage": 1, "pageSize": 10}).encode(),
                                 headers={"content-type": "application/json", "user-agent": "gb-devcart-bom-check"})
    data = json.load(urllib.request.urlopen(req, timeout=30))["data"]["componentPageInfo"]["list"] or []
    return next((c for c in data if c.get("componentCode") == code), None)


def unit_price(c, n):
    for p in c.get("componentPrices") or []:
        if p["startNumber"] <= n and (p["endNumber"] == -1 or n <= p["endNumber"]):
            return p["productPrice"]
    return None


def main():
    comps = {c["ref"]: c for c in json.load(open(BOARD / "circuit.netlist.json"))["netlist"]["components"]}
    rows = list(csv.DictReader(open(BOARD / "exports/jlcpcb/bom.csv")))
    out = []
    for r in rows:
        code = r["LCSC Part #"]
        refs = r["Designator"].split(",")
        mpn = comps[refs[0]]["fields"].get("MPN", "")
        c = lookup(code)
        time.sleep(0.3)
        if not c:
            out.append(dict(lcsc=code, refs=refs, mpn=mpn, found=False))
            continue
        need = len(refs) * QTY
        out.append(dict(lcsc=code, refs=refs, mpn=mpn, found=True, jlc_mpn=c.get("componentModelEn"),
                        package=c.get("componentSpecificationEn"), library=c.get("componentLibraryType"),
                        stock=c.get("stockCount"), need=need, unit=unit_price(c, need),
                        least=c.get("leastPatchNumber"), loss=c.get("lossNumber"),
                        prices=c.get("componentPrices") or [], per_board=len(refs)))
    (BOARD / "exports/jlcpcb/parts_check.json").write_text(json.dumps(out, indent=1))
    for o in out:
        if not o["found"]:
            print(f"{o['lcsc']:10s} NOT FOUND  {','.join(o['refs'])}")
            continue
        flag = "" if o["stock"] >= o["need"] + (o["loss"] or 0) else "  LOW STOCK"
        mpn_ok = "" if not o["mpn"] or o["mpn"].replace(" ", "").upper() in (o["jlc_mpn"] or "").replace(" ", "").upper() \
            or (o["jlc_mpn"] or "").replace(" ", "").upper() in o["mpn"].replace(" ", "").upper() else f"  MPN? {o['jlc_mpn']}"
        print(f"{o['lcsc']:10s} {o['library']:8s} stock {o['stock']:>9} need {o['need']:>4} ${o['unit'] or 0:.4f} "
              f"{o['package'] or '':14s} {','.join(o['refs'])[:40]}{flag}{mpn_ok}")


if __name__ == "__main__":
    main()
