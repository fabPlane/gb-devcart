# USB programmer

The devcart has no USB of its own. Its bus is the Game Boy's 5 V parallel bus, so the cheapest
and simplest programmer is a 5 V microcontroller with enough pins to *be* the Game Boy: an
**Arduino Mega 2560** (or clone, ~US$15), which has native 5 V I/O, 70 GPIOs and a USB-serial
bridge. You need no level shifters and no extra board.

```
PC ──USB── Arduino Mega 2560 ──27 wires── GB cartridge slot ── GB DEVCART r1
           (gbflash.ino)                   (32-pin, 1.5 mm)
```

| Path | What |
| --- | --- |
| `firmware/gbflash/gbflash.ino` | Mega sketch: bus timing on raw AVR ports, 1 Mbaud serial |
| `firmware/gbflash/gbflash_core.h` | Protocol + SST39SF040 algorithms, hardware independent |
| `host/gbflash.py` | PC tool: `info`, `flash`, `dump`, `erase`, `save-backup`, `save-restore` |
| `sim/cart_sim.cpp` | Native model of this cart (glue logic, flash, F-RAM) running the same core |
| `test_e2e.sh` | Flashes, dumps and verifies ROMs and saves against the simulator |

## Parts

- Arduino Mega 2560 R3 (or a clone with a CH340 USB chip; use the CH340 driver on macOS/Windows).
- A 32-pin, 1.5 mm pitch Game Boy cartridge slot. Replacement DMG slots sell for a few dollars
  (search "Game Boy DMG cartridge slot 32 pin"). Solder wires to its pins, or plug the devcart's
  fingers into it.
- 27 jumper wires. Keep them under ~20 cm.

## Wiring

Cart pin numbers are counted from the left with the cart's component side facing you
(the order of the devcart's `J1`).

| Cart pin | Signal | Mega pin | AVR port |
| --- | --- | --- | --- |
| 1 | VCC | 5V | — |
| 2 | CLK | not connected | — |
| 3 | /WR | D2 | PE4 |
| 4 | /RD | D3 | PE5 |
| 5 | /CS | D4 | PG5 |
| 6–13 | A0–A7 | D22–D29 | PORTA0–7 |
| 14–21 | A8–A15 | D37, D36, D35, D34, D33, D32, D31, D30 | PORTC0–7 |
| 22–29 | D0–D7 | D49, D48, D47, D46, D45, D44, D43, D42 | PORTL0–7 |
| 30 | /RESET | D5 (held high) | PE3 |
| 31 | AUDIO_IN | not connected | — |
| 32 | GND | GND | — |

## Use it

```bash
# 1. firmware (Arduino IDE: open firmware/gbflash/gbflash.ino, board "Arduino Mega or Mega 2560")
arduino-cli compile --fqbn arduino:avr:mega programmer/firmware/gbflash
arduino-cli upload  --fqbn arduino:avr:mega -p /dev/ttyACM0 programmer/firmware/gbflash

# 2. host tool
pip install pyserial
python3 programmer/host/gbflash.py --port /dev/ttyACM0 info          # expects "0xbf 0xb7 SST39SF040"
python3 programmer/host/gbflash.py --port /dev/ttyACM0 flash game/dist/bitcatcher.gb
python3 programmer/host/gbflash.py --port /dev/ttyACM0 dump  backup.gb --size 32768
python3 programmer/host/gbflash.py --port /dev/ttyACM0 save-backup bitcatcher.sav
```

`flash` erases the whole chip, programs the image in 256-byte chunks (skipping erased `0xFF`
chunks), reads every bank back and compares it with the file, then leaves the bank latch at 1.
Use `--port COM5` on Windows.

## How flashing works on this cart

The SST39SF040's `/WE` is only asserted for writes to `0x4000–0x7FFF`, and its address lines
A14–A18 come from the bank latch (written at `0x2000`). Every JEDEC command cycle therefore goes
through the switchable window:

| Flash address | Bank latch | CPU address |
| --- | --- | --- |
| `0x5555` | 1 (odd) | `0x5555` |
| `0x2AAA` | 0 (even) | `0x6AAA` |
| byte at flash `fa` | `fa >> 14` | `0x4000 + (fa & 0x3FFF)` |

Byte program = `AA@5555, 55@2AAA, A0@5555, data@fa`, then Data# polling on DQ7 (≤ 20 µs).
Chip erase = `AA, 55, 80, AA, 55, 10@5555` (≤ 100 ms). The bank-register writes at `0x2000`
never reach the flash (its `/WE` stays high), so they can sit between command cycles safely.
`gbflash_core.h` implements exactly this, and the same sequences work from Game Boy code running
in WRAM if you want to flash from the console itself.

## Test without hardware

```bash
programmer/test_e2e.sh   # needs a C++17 compiler and python3
```

This builds `sim/cart_sim` from the same `gbflash_core.h` the Mega runs, against a model of the
cart taken from `circuit.netlist.json`: the 74HC32/74HC00 decode, a 74HC574 latch that powers up
random, 2.2 kΩ pull-downs, an SST39SF040 command state machine with Data# polling and 1→0-only
programming, and the 8 KB F-RAM window. It flashes the game onto a cart full of random data,
flashes and dumps a 512 KB image with different data in each of the 32 banks, and round-trips an
F-RAM save. The test found one bug while it was being written: the model wrongly treated a `0xF0`
data byte as the flash's reset command.

**Not yet tested on real hardware.** Bus timing on the Mega has a wide margin (250 ns or more per
strobe against 70 ns parts), but long wires can ring, so keep them short.

## Alternatives

- **Flash from the Game Boy itself:** copy a small flasher into WRAM and run the same command
  sequences. You still need a way to get the data in, such as the link cable or a second cart.
- **Existing cart flashers** such as insideGadgets' GBxCart RW with FlashGBX may work with a
  custom cartridge profile that matches the bank-1/bank-0 command addresses above. This is
  untested.
- **Native USB (r2 idea):** an RP2040 with 74LVC245 level shifters, either on the cart (as on
  the ModRetro board) or as a slot-style dock.
