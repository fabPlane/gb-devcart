#!/usr/bin/env python3
"""Copy MPN / Manufacturer / LCSC fields from circuit.netlist.json into board.kicad_pcb and
board.kicad_sch (footprints and placed symbols), so KiCad, JLC's tools and BOM exports see them.

    python3 scripts/sync_fields.py
"""
import json
import re
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ("MPN", "Manufacturer", "LCSC")


def block_end(text: str, start: int) -> int:
    """Index just past the s-expression that opens at text[start] == '('."""
    depth, i, in_str = 0, start, False
    while i < len(text):
        ch = text[i]
        if in_str:
            if ch == "\\":
                i += 1
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError("unbalanced s-expression")


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def set_props(block: str, values: dict[str, str]) -> str:
    """Set or add each property; new ones are cloned from the hidden Datasheet/Description property."""
    for name, value in values.items():
        m = re.search(r'\(property "%s" "' % re.escape(name), block)
        if m:
            end = block_end(block, m.start())
            prop = block[m.start():end]
            prop = re.sub(r'^\(property "%s" "(?:[^"\\]|\\.)*"' % re.escape(name), f'(property "{name}" "{esc(value)}"', prop)
            block = block[: m.start()] + prop + block[end:]
            continue
        t = re.search(r'\(property "(Datasheet|Description)" "', block)
        if not t:
            raise ValueError("no template property to clone")
        end = block_end(block, t.start())
        tmpl = block[t.start():end]
        new = re.sub(r'^\(property "(?:Datasheet|Description)" "(?:[^"\\]|\\.)*"', f'(property "{name}" "{esc(value)}"', tmpl)
        new = re.sub(r'\(uuid "[^"]*"\)', lambda _: f'(uuid "{uuid.uuid4()}")', new)  # KiCad needs unique ids
        line_start = block.rfind("\n", 0, t.start()) + 1
        indent = block[line_start:t.start()]
        block = block[:end] + "\n" + indent + new + block[end:]
    return block


def sync(path: Path, opener: str, fields_by_ref: dict[str, dict[str, str]]) -> int:
    text = path.read_text()
    out, pos, n = [], 0, 0
    for m in re.finditer(opener, text):
        if m.start() < pos:
            continue
        end = block_end(text, m.start())
        block = text[m.start():end]
        ref = re.search(r'\(property "Reference" "([^"]+)"', block)
        out.append(text[pos:m.start()])
        if ref and ref.group(1) in fields_by_ref:
            block = set_props(block, fields_by_ref[ref.group(1)])
            n += 1
        out.append(block)
        pos = end
    out.append(text[pos:])
    path.write_text("".join(out))
    return n


def main() -> None:
    comps = json.load(open(ROOT / "circuit.netlist.json"))["netlist"]["components"]
    want = {c["ref"]: {k: c["fields"][k] for k in FIELDS if c["fields"].get(k)} for c in comps}
    want = {r: f for r, f in want.items() if f}
    n_pcb = sync(ROOT / "board.kicad_pcb", r"\(footprint \"", want)
    # placed symbols only (lib_symbols holds the library copies, which have no Reference value)
    n_sch = sync(ROOT / "board.kicad_sch", r"\(symbol\s+\(lib_id ", want)
    print(f"updated {n_pcb} footprints and {n_sch} symbols with {', '.join(FIELDS)}")


if __name__ == "__main__":
    main()
