#!/usr/bin/env python3
"""Protocol-level model of a GB DEVCART r2 in USB mode, over stdin/stdout, for testing the host.

Mirrors r2/rtl/usb_engine.v (I/M/R/W/P) and an S29GL064N in byte mode (AMD unlock 0xAAA/0x555,
byte program, write-buffer program 0x25/0x29, chip erase 0x80/0x10, autoselect 0x90, reset 0xF0,
Data# polling while busy). The RTL itself is checked by r2/tb/tb_mapper.v.

    usb_cart_model.py [flash.bin] [fram.bin]   # images loaded at start, saved at EOF
"""
import os
import random
import sys

FLASH_SIZE, FRAM_SIZE = 8 << 20, 32 << 10
flash = bytearray(b"\xff" * FLASH_SIZE)
fram = bytearray(os.urandom(FRAM_SIZE))
inp, out = sys.stdin.buffer, sys.stdout.buffer

st, in_id, busy, busy_val = 0, False, 0, 0
wb_left, wb = 0, []


def rd(n: int) -> bytes:
    b = inp.read(n)
    if len(b) != n:
        raise EOFError
    return b


def flash_read(a: int) -> int:
    global busy
    if busy:
        busy -= 1
        return (~busy_val & 0x80) | (0x40 if busy & 1 else 0)
    if in_id:
        return {0: 0x01, 2: 0x7E}.get(a & 0xFF, 0x00)
    return flash[a]


def flash_write(a: int, d: int) -> None:
    global st, in_id, busy, busy_val, wb_left, wb
    c = a & 0xFFF
    if d == 0xF0 and st not in (3, 5):
        st, in_id = 0, False
        return
    if st == 0:
        st = 1 if (c == 0xAAA and d == 0xAA) else 0
    elif st == 1:
        st = 2 if (c == 0x555 and d == 0x55) else 0
    elif st == 2:
        st = 0
        if c == 0xAAA and d == 0xA0:
            st = 3
        elif c == 0xAAA and d == 0x80:
            st = 7
        elif c == 0xAAA and d == 0x90:
            in_id = True
        elif d == 0x25:
            st = 4
    elif st == 3:
        flash[a] &= d
        busy, busy_val, st = random.randint(1, 4), d, 0
    elif st == 4:
        wb_left, wb, st = d + 1, [], 5
    elif st == 5:
        wb.append((a, d))
        wb_left -= 1
        if wb_left == 0:
            st = 6
    elif st == 6:
        if d == 0x29:
            for wa, wd in wb:
                flash[wa] &= wd
            busy, busy_val = random.randint(1, 6), wb[-1][1]
        st = 0
    elif st == 7:
        st = 8 if (c == 0xAAA and d == 0xAA) else 0
    elif st == 8:
        st = 9 if (c == 0x555 and d == 0x55) else 0
    elif st == 9:
        if c == 0xAAA and d == 0x10:
            flash[:] = b"\xff" * FLASH_SIZE
            busy, busy_val = 5, 0xFF
        elif d == 0x30:
            s0 = a & ~0xFFFF
            flash[s0 : s0 + 0x10000] = b"\xff" * 0x10000
            busy, busy_val = 3, 0xFF
        st = 0


def main() -> None:
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        flash[:] = open(sys.argv[1], "rb").read()[:FLASH_SIZE].ljust(FLASH_SIZE, b"\xff")
    if len(sys.argv) > 2 and os.path.exists(sys.argv[2]):
        fram[:] = open(sys.argv[2], "rb").read()[:FRAM_SIZE].ljust(FRAM_SIZE, b"\x00")
    try:
        while True:
            op = rd(1)
            if op == b"I":
                out.write(b"GBFPGA1\n")
            elif op == b"M":
                out.write(b"\x01")  # USB mode, no dev mode
            elif op in (b"R", b"W", b"P"):
                hdr = rd(6)
                t, a, n = hdr[0] & 1, int.from_bytes(hdr[1:4], "little") & 0x7FFFFF, int.from_bytes(hdr[4:6], "little")
                if op == b"R":
                    out.write(bytes((fram[(a + i) & 0x7FFF] if t else flash_read((a + i) & 0x7FFFFF)) for i in range(n)))
                elif op == b"W":
                    data = rd(n)
                    for i, d in enumerate(data):
                        if t:
                            fram[(a + i) & 0x7FFF] = d
                        else:
                            flash_write((a + i) & 0x7FFFFF, d)
                    out.write(b"K")
                else:  # P: same page splitting as the RTL
                    data = rd(min(n, 256))
                    i = 0
                    while i < len(data):
                        cnt = min(32 - (a & 31), len(data) - i)
                        for ca, cd in [(0xAAA, 0xAA), (0x555, 0x55), (a, 0x25), (a, cnt - 1)]:
                            flash_write(ca, cd)
                        for j in range(cnt):
                            flash_write(a + j, data[i + j])
                        flash_write(a, 0x29)
                        while (flash_read(a + cnt - 1) & 0x80) != (data[i + cnt - 1] & 0x80):
                            pass
                        a, i = a + cnt, i + cnt
                    out.write(b"K")
            out.flush()
    except EOFError:
        pass
    if len(sys.argv) > 1:
        open(sys.argv[1], "wb").write(flash)
    if len(sys.argv) > 2:
        open(sys.argv[2], "wb").write(fram)


if __name__ == "__main__":
    main()
