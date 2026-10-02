#!/usr/bin/env python3
"""gbflash — flash, dump and back up the GB DEVCART r1 over USB (Arduino Mega programmer).

    pip install pyserial
    python3 gbflash.py --port /dev/ttyACM0 info
    python3 gbflash.py --port /dev/ttyACM0 flash game.gb          # erase, program, verify
    python3 gbflash.py --port /dev/ttyACM0 dump backup.gb [--size 524288]
    python3 gbflash.py --port /dev/ttyACM0 save-backup game.sav   # 8 KB F-RAM at 0xA000
    python3 gbflash.py --port /dev/ttyACM0 save-restore game.sav
    python3 gbflash.py --port /dev/ttyACM0 --rev 2 flash big.gb      # GB DEVCART r2 (FPGA, 8 MB)

`--sim path/to/cart_sim [--sim-flash f.bin --sim-fram r.bin]` runs the same protocol against the native cart simulator instead of a
serial port (used by programmer/test_e2e.sh).
"""
from __future__ import annotations

import argparse
import os
import struct
import subprocess
import sys
import time

FLASH_SIZE = 512 * 1024      # r1: SST39SF040
FLASH_SIZE_R2 = 8 * 1024 * 1024  # r2: S29GL064 (x8)
BANK_SIZE = 0x4000
SAVE_SIZE = 0x2000
CHUNK = 256
KNOWN_FLASH = {(0x01, 0x7E): "S29GL064N (8 MB, r2)", (0xBF, 0xB7): "SST39SF040 (512 KB)", (0xBF, 0xB6): "SST39SF020A (256 KB)", (0xBF, 0xB5): "SST39SF010A (128 KB)"}


class Link:
    def __init__(self, port: str | None, sim: str | None, sim_args: list[str], rev: int = 1):
        self.rev = rev
        if sim:
            env = {**os.environ, "GBCART_REV": str(rev)}
            self.proc = subprocess.Popen([sim, *sim_args], stdin=subprocess.PIPE, stdout=subprocess.PIPE, env=env)
            self._w, self._r = self.proc.stdin, self.proc.stdout
        else:
            import serial  # pyserial

            self.proc = None
            self.ser = serial.Serial(port, 1_000_000, timeout=5)
            time.sleep(2.0)  # the Mega resets when the port opens
            self.ser.reset_input_buffer()
            self._w = self._r = None

    def write(self, data: bytes) -> None:
        if self.proc:
            self._w.write(data)
            self._w.flush()
        else:
            self.ser.write(data)

    def read(self, n: int) -> bytes:
        buf = self._r.read(n) if self.proc else self.ser.read(n)
        if len(buf) != n:
            raise IOError(f"programmer timed out ({len(buf)}/{n} bytes)")
        return buf

    def status(self, what: str) -> None:
        s = self.read(1)
        if s != b"K":
            raise IOError(f"{what} failed: {s!r} ({'timeout' if s == b'T' else 'verify mismatch' if s == b'F' else 'protocol error'})")

    def close(self) -> None:
        if self.proc:
            self._w.close()
            self.proc.wait(timeout=30)
        else:
            self.ser.close()

    # --- commands -------------------------------------------------------------------------
    def hello(self) -> str:
        self.write(b"I")
        line = self.read(9)
        if line != b"GBFLASH1\n":
            raise IOError(f"unexpected greeting {line!r}: is gbflash.ino flashed to the Mega?")
        return line.decode().strip()

    def flash_id(self) -> tuple[int, int]:
        self.write(b"D")
        m, d = self.read(2)
        return m, d

    def set_rev(self) -> None:
        """Tell the firmware which cart this is; r2 also enters the mapper's dev mode."""
        self.write(b"V" + bytes([self.rev]))
        self.status("cart revision")

    def leave_dev_mode(self) -> None:
        if self.rev == 2:
            self.write_bus(0x0000, b"\xD0")

    def bank(self, n: int) -> None:
        if self.rev == 2:
            self.write(b"b" + struct.pack("<H", n))
        else:
            self.write(b"B" + bytes([n & 0xFF]))
        self.status("bank select")

    def read_bus(self, addr: int, n: int) -> bytes:
        self.write(b"R" + struct.pack("<HH", addr, n))
        return self.read(n)

    def write_bus(self, addr: int, data: bytes) -> None:
        self.write(b"W" + struct.pack("<HH", addr, len(data)) + data)
        self.status("bus write")

    def chip_erase(self) -> None:
        self.write(b"E")
        if not self.proc:
            self.ser.timeout = 320  # 8 MB parts take tens of seconds, up to a few minutes
        try:
            self.status("chip erase")
        finally:
            if not self.proc:
                self.ser.timeout = 5

    def program(self, fa: int, data: bytes) -> None:
        self.write(b"P" + struct.pack("<I", fa)[:3] + struct.pack("<H", len(data)) + data)
        self.status(f"program @0x{fa:05x}")


def read_flash(link: Link, size: int) -> bytes:
    out = bytearray(link.read_bus(0x0000, BANK_SIZE))  # bank 0, fixed window
    for bank in range(1, size // BANK_SIZE):
        link.bank(bank)
        out += link.read_bus(0x4000, BANK_SIZE)
    return bytes(out[:size])


def progress(done: int, total: int, label: str) -> None:
    pct = done * 100 // max(total, 1)
    sys.stderr.write(f"\r{label} {pct:3d}% ({done}/{total} bytes)")
    if done >= total:
        sys.stderr.write("\n")


def header_info(rom: bytes) -> str:
    title = rom[0x134:0x144].split(b"\0")[0].decode("ascii", "replace")
    chk = (-sum(rom[0x134:0x14D]) - 25) & 0xFF  # header checksum: x = x - b - 1 over 0x134..0x14C
    ok = "ok" if chk == rom[0x14D] else f"BAD (expected 0x{chk:02x})"
    return f"title={title!r} type=0x{rom[0x147]:02x} rom_size_code=0x{rom[0x148]:02x} header_checksum={ok}"


def flash_size(link: Link) -> int:
    return FLASH_SIZE_R2 if link.rev == 2 else FLASH_SIZE


def read_save(link: Link) -> bytes:
    if link.rev != 2:
        return link.read_bus(0xA000, SAVE_SIZE)
    link.leave_dev_mode()            # RAM-bank writes are ignored in dev mode
    link.write_bus(0x0000, b"\x0A")  # MBC5 RAM enable
    out = b""
    for bank in range(4):            # 4 x 8 KB = the whole 32 KB F-RAM
        link.write_bus(0x4000, bytes([bank]))
        out += link.read_bus(0xA000, SAVE_SIZE)
    return out


def write_save(link: Link, data: bytes) -> None:
    if link.rev == 2:
        link.leave_dev_mode()
        link.write_bus(0x0000, b"\x0A")
    for base in range(0, len(data), SAVE_SIZE):
        if link.rev == 2:
            link.write_bus(0x4000, bytes([base // SAVE_SIZE]))
        part = data[base : base + SAVE_SIZE]
        for off in range(0, len(part), CHUNK):
            link.write_bus(0xA000 + off, part[off : off + CHUNK])


def cmd_flash(link: Link, path: str) -> None:
    rom = open(path, "rb").read()
    if len(rom) > flash_size(link):
        raise SystemExit(f"{path}: {len(rom)} bytes does not fit the {flash_size(link) >> 10} KB flash")
    if len(rom) >= 0x150:
        print(f"{path}: {len(rom)} bytes, {header_info(rom)}")
    print("erasing chip...")
    link.chip_erase()
    t0 = time.time()
    for off in range(0, len(rom), CHUNK):
        chunk = rom[off : off + CHUNK]
        if chunk.count(0xFF) != len(chunk):  # erased chunks need no programming
            link.program(off, chunk)
        progress(min(off + CHUNK, len(rom)), len(rom), "programming")
    print(f"programmed in {time.time() - t0:.1f}s; verifying...")
    size = (len(rom) + BANK_SIZE - 1) // BANK_SIZE * BANK_SIZE
    back = read_flash(link, size)[: len(rom)]
    if back != rom:
        bad = next(i for i in range(len(rom)) if back[i] != rom[i])
        raise SystemExit(f"verify FAILED at 0x{bad:05x}: wrote 0x{rom[bad]:02x}, read 0x{back[bad]:02x}")
    link.bank(1)  # leave the cart in the state a 32 KB game expects
    print("verify ok")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", help="serial port of the Mega, e.g. /dev/ttyACM0 or COM5")
    ap.add_argument("--sim", help="path to programmer/sim/cart_sim instead of a serial port")
    ap.add_argument("--sim-flash", help="cart_sim: flash image file (loaded at start, saved at exit)")
    ap.add_argument("--sim-fram", help="cart_sim: F-RAM image file")
    ap.add_argument("--rev", type=int, choices=(1, 2), default=1, help="cart revision: 1 = discrete mapper, 2 = FPGA mapper")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("info")
    p = sub.add_parser("flash"); p.add_argument("rom")
    p = sub.add_parser("dump"); p.add_argument("out"); p.add_argument("--size", type=int, default=None)
    sub.add_parser("erase")
    p = sub.add_parser("save-backup"); p.add_argument("out")
    p = sub.add_parser("save-restore"); p.add_argument("sav")
    a = ap.parse_args()
    if not a.port and not a.sim:
        ap.error("give --port (or --sim)")

    link = Link(a.port, a.sim, [p for p in (a.sim_flash, a.sim_fram) if p], a.rev)
    try:
        print(link.hello())
        link.set_rev()
        m, d = link.flash_id()
        print(f"flash id: 0x{m:02x} 0x{d:02x} {KNOWN_FLASH.get((m, d), 'UNKNOWN - check the cart is seated')}")
        if a.cmd == "flash":
            cmd_flash(link, a.rom)
        elif a.cmd == "dump":
            data = read_flash(link, a.size or flash_size(link))
            open(a.out, "wb").write(data)
            print(f"wrote {len(data)} bytes to {a.out}; {header_info(data)}")
        elif a.cmd == "erase":
            link.chip_erase()
            print("chip erased")
        elif a.cmd == "save-backup":
            data = read_save(link)
            open(a.out, "wb").write(data)
            print(f"saved {len(data)} bytes of F-RAM to {a.out}")
        elif a.cmd == "save-restore":
            data = open(a.sav, "rb").read()[: SAVE_SIZE * (4 if link.rev == 2 else 1)]
            write_save(link, data)
            if read_save(link)[: len(data)] != data:
                raise SystemExit("F-RAM verify failed")
            print(f"restored {len(data)} bytes to F-RAM")
    finally:
        try:
            link.leave_dev_mode()  # r2: back to a plain MBC5 cart so a game can't write flash
        except Exception:
            pass
        link.close()


if __name__ == "__main__":
    main()
