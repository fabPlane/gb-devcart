#!/usr/bin/env bash
# Build + test the GB DEVCART r2 FPGA design (GW1N-LV4QN88) with open-source tools.
#   pip install yowasp-yosys yowasp-nextpnr-himbaechel-gowin apycula   (or use oss-cad-suite)
#   apt install iverilog
# Program the FPGA's internal flash over the cart's own USB port (CH347F JTAG):
#   openFPGALoader -c ch347_jtag -f build/gbdevcart_r2.fs
set -euo pipefail
cd "$(dirname "$0")"
YOSYS=${YOSYS:-yowasp-yosys}
NEXTPNR=${NEXTPNR:-yowasp-nextpnr-himbaechel-gowin}
RTL="rtl/gbcart_mapper.v rtl/usb_engine.v rtl/gbcart_core.v"
mkdir -p build
python3 hw/fpga_pins.py
for w in 480 240 150; do
  iverilog -g2012 -o build/tb $RTL tb/tb_mapper.v
  vvp -n build/tb +wr_ns=$w | grep -E "PASS|FAIL"
done
$YOSYS -q -p "read_verilog $RTL rtl/top_gw1n4.v; synth_gowin -top top_gw1n4 -json build/top.json"
$NEXTPNR --json build/top.json --write build/pnr.json --device GW1N-LV4QN88C6/I5 \
  --vopt family=GW1N-4 --vopt cst=gw1n4_qn88.cst --freq 48 > build/pnr.log 2>&1
grep -A14 "Device utilisation" build/pnr.log | grep -E "IOB|LUT4|DFF|BSRAM"
grep "Max frequency" build/pnr.log | tail -1
gowin_pack -d GW1N-4 --sspi_as_gpio --mspi_as_gpio -o build/gbdevcart_r2.fs build/pnr.json
echo "bitstream: r2/build/gbdevcart_r2.fs"
