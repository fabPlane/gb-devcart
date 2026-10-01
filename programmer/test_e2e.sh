#!/usr/bin/env bash
# End-to-end programmer test without hardware: builds the cart simulator from the same
# gbflash_core.h the Mega runs, then flashes, dumps and verifies ROMs and the F-RAM through
# the real host tool. Usage: programmer/test_e2e.sh [rom.gb]
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
rom="${1:-$here/../game/dist/bitcatcher.gb}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

c++ -O2 -Wall -Wextra -std=c++17 -I"$here/firmware/gbflash" "$here/sim/cart_sim.cpp" -o "$work/cart_sim"
host=(python3 "$here/host/gbflash.py" --sim "$work/cart_sim" --sim-flash "$work/flash.bin" --sim-fram "$work/fram.bin")

# a dirty cart: random flash contents and a random bank latch
head -c 524288 /dev/urandom > "$work/flash.bin"

echo "== info"; "${host[@]}" info
echo "== flash $rom"; "${host[@]}" flash "$rom"
echo "== dump"; "${host[@]}" dump "$work/dump.bin" --size "$(stat -c%s "$rom")"
cmp "$rom" "$work/dump.bin" && echo "dump matches ROM"
cmp <(head -c "$(stat -c%s "$rom")" "$work/flash.bin") "$rom" && echo "simulated flash chip holds the ROM at 0x00000"

echo "== 512 KB multi-bank image (every bank different)"
python3 - "$work/big.gb" <<'EOF'
import sys, os
img = bytearray(os.urandom(512 * 1024))
for bank in range(32):
    img[bank * 0x4000 : bank * 0x4000 + 4] = bytes([0xB0, bank, 0xB0, bank])
img[0x2000:0x2100] = b"\xff" * 256  # an erased-looking chunk is skipped by the host
open(sys.argv[1], "wb").write(img)
EOF
"${host[@]}" flash "$work/big.gb"
"${host[@]}" dump "$work/big-dump.bin"
cmp "$work/big.gb" "$work/big-dump.bin" && echo "512 KB image round-trips through all 32 banks"

echo "== F-RAM save backup/restore"
head -c 8192 /dev/urandom > "$work/save.sav"
"${host[@]}" save-restore "$work/save.sav"
"${host[@]}" save-backup "$work/save2.sav"
cmp "$work/save.sav" "$work/save2.sav" && echo "save round-trips"
echo "ALL OK"
