"""USB link to a GB DEVCART r2 plugged straight into the computer (CH347F UART -> FPGA).

The FPGA only knows raw memory cycles plus a write-buffer program command; the flash algorithms
(ID, chip erase, Data# polling) live here. Protocol: r2/rtl/usb_engine.v.
"""
from __future__ import annotations

import struct
import subprocess
import time

FLASH, FRAM = 0, 1
FLASH_SIZE = 8 << 20
FRAM_SIZE = 32 << 10
P_MAX = 256
R_MAX = 4096


class UsbCart:
    def __init__(self, port: str | None = None, sim: list[str] | None = None):
        if sim:
            self.proc = subprocess.Popen(sim, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            self.ser = None
        else:
            import serial  # pyserial

            self.proc = None
            self.ser = serial.Serial(port, 1_000_000, timeout=5)
            self.ser.reset_input_buffer()

    # ---- transport ----
    def _w(self, b: bytes) -> None:
        if self.proc:
            self.proc.stdin.write(b)
            self.proc.stdin.flush()
        else:
            self.ser.write(b)

    def _r(self, n: int) -> bytes:
        b = self.proc.stdout.read(n) if self.proc else self.ser.read(n)
        if len(b) != n:
            raise IOError(f"cart timed out ({len(b)}/{n} bytes)")
        return b

    def close(self) -> None:
        if self.proc:
            self.proc.stdin.close()
            self.proc.wait(timeout=30)
        else:
            self.ser.close()

    # ---- protocol ----
    def hello(self) -> str:
        self._w(b"I")
        s = self._r(8)
        if s != b"GBFPGA1\n":
            raise IOError(f"unexpected greeting {s!r}: is this a GB DEVCART r2 with the r2 bitstream?")
        return s.decode().strip()

    def mode(self) -> tuple[bool, bool]:
        self._w(b"M")
        m = self._r(1)[0]
        return bool(m & 1), bool(m & 2)

    def read(self, t: int, addr: int, n: int) -> bytes:
        out = b""
        while n:
            k = min(n, R_MAX)
            self._w(b"R" + bytes([t]) + struct.pack("<I", addr)[:3] + struct.pack("<H", k))
            out += self._r(k)
            addr += k
            n -= k
        return out

    def write(self, t: int, addr: int, data: bytes) -> None:
        self._w(b"W" + bytes([t]) + struct.pack("<I", addr)[:3] + struct.pack("<H", len(data)) + data)
        self._ack("write")

    def program(self, addr: int, data: bytes) -> None:
        assert 0 < len(data) <= P_MAX
        self._w(b"P\x00" + struct.pack("<I", addr)[:3] + struct.pack("<H", len(data)) + data)
        self._ack(f"program @0x{addr:06x}")

    def _ack(self, what: str) -> None:
        a = self._r(1)
        if a != b"K":
            why = {b"C": "a console is powering the cart; unplug it from the console",
                   b"T": "flash program timeout", b"F": "flash reported a program failure"}.get(a, "protocol error")
            raise IOError(f"{what} failed: {a!r} ({why})")

    # ---- flash algorithms (S29GL064N, AMD command set, byte mode) ----
    def flash_cmd(self, *cycles: tuple[int, int]) -> None:
        for a, d in cycles:
            self.write(FLASH, a, bytes([d]))

    def flash_id(self) -> tuple[int, int]:
        self.flash_cmd((0xAAA, 0xAA), (0x555, 0x55), (0xAAA, 0x90))
        mfr, dev = self.read(FLASH, 0x000, 1)[0], self.read(FLASH, 0x002, 1)[0]
        self.flash_cmd((0x000, 0xF0))
        return mfr, dev

    def chip_erase(self, timeout_s: float = 300) -> None:
        self.flash_cmd((0xAAA, 0xAA), (0x555, 0x55), (0xAAA, 0x80), (0xAAA, 0xAA), (0x555, 0x55), (0xAAA, 0x10))
        t0 = time.time()
        while self.read(FLASH, 0, 1)[0] != 0xFF:  # Data# polling: DQ7 reads 0 until done
            if time.time() - t0 > timeout_s:
                raise IOError("chip erase timed out")
            time.sleep(0.1)
