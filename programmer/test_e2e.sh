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
echo
echo "######## r2: FPGA mapper (MBC5 + dev mode) + 8 MB AMD flash ########"
host2=(python3 "$here/host/gbflash.py" --rev 2 --sim "$work/cart_sim" --sim-flash "$work/flash2.bin" --sim-fram "$work/fram2.bin")
head -c 8388608 /dev/urandom > "$work/flash2.bin"
echo "== info"; "${host2[@]}" info
echo "== flash $rom"; "${host2[@]}" flash "$rom"
"${host2[@]}" dump "$work/dump2.bin" --size "$(stat -c%s "$rom")"
cmp "$rom" "$work/dump2.bin" && echo "r2: dump matches ROM"
echo "== 8 MB image, 512 banks"
python3 - "$work/big2.gb" <<'PY'
import sys, os
img = bytearray(os.urandom(8 << 20))
for bank in range(512):
    img[bank * 0x4000 : bank * 0x4000 + 4] = bytes([0xB2, bank & 0xFF, bank >> 8, 0xB2])
open(sys.argv[1], "wb").write(img)
PY
"${host2[@]}" flash "$work/big2.gb" 2>/dev/null | tail -1
"${host2[@]}" dump "$work/big2-dump.bin" >/dev/null
cmp "$work/big2.gb" "$work/big2-dump.bin" && echo "r2: 8 MB image round-trips through all 512 banks (9-bit MBC5 banking)"
echo "== 32 KB F-RAM save (4 RAM banks)"
head -c 32768 /dev/urandom > "$work/save2.sav"
"${host2[@]}" save-restore "$work/save2.sav" | tail -1
"${host2[@]}" save-backup "$work/save2b.sav" | tail -1
cmp "$work/save2.sav" "$work/save2b.sav" && echo "r2: 32 KB save round-trips"
echo "ALL OK"
