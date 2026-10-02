#!/usr/bin/env bash
# Build + test the GB DEVCART r2 FPGA mapper with open-source tools.
#   pip install yowasp-yosys yowasp-nextpnr-himbaechel-gowin apycula   (or use oss-cad-suite)
#   apt install iverilog
# Program the on-chip flash over JTAG:  openFPGALoader -b <cable> -f build/gbdevcart_r2.fs
set -euo pipefail
cd "$(dirname "$0")"
YOSYS=${YOSYS:-yowasp-yosys}
NEXTPNR=${NEXTPNR:-yowasp-nextpnr-himbaechel-gowin}
mkdir -p build
for w in 480 240 150; do
  iverilog -g2012 -o build/tb rtl/gbcart_mapper.v tb/tb_mapper.v
  vvp -n build/tb +wr_ns=$w | grep -E "PASS|FAIL"
done
$YOSYS -q -p "read_verilog rtl/gbcart_mapper.v rtl/top_gw1nz.v; synth_gowin -top top_gw1nz -json build/top.json"
$NEXTPNR --json build/top.json --write build/pnr.json --device GW1NZ-LV1QN48C6/I5 \
  --vopt family=GW1NZ-1 --vopt cst=gw1nz_qn48.cst > build/pnr.log 2>&1
grep -A8 "Device utilisation" build/pnr.log | grep -E "IOB|LUT4|DFF"
grep "Max frequency" build/pnr.log | tail -1
gowin_pack -d GW1NZ-1 -o build/gbdevcart_r2.fs build/pnr.json
echo "bitstream: r2/build/gbdevcart_r2.fs"
