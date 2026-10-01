// cart_sim.cpp — native simulator: runs the real gbflash_core.h protocol over stdin/stdout
// against a model of the GB DEVCART r1 (glue logic as in circuit.netlist.json, SST39SF040
// command state machine, FM18W08 F-RAM). Used by programmer/host/gbflash.py --sim.
//
//   c++ -O2 -std=c++17 -I../firmware/gbflash cart_sim.cpp -o cart_sim
//   ./cart_sim [flash.bin] [fram.bin]   # images are loaded at start and saved on EOF
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <vector>

#include "gbflash_core.h"

namespace {

constexpr uint32_t FLASH_SIZE = 512 * 1024;
std::vector<uint8_t> flash(FLASH_SIZE, 0xFF);
std::vector<uint8_t> fram(32 * 1024, 0x00);
uint8_t latch = 0;  // 74HC574, random at power-up

// SST39SF040 command state machine (JEDEC, A14..A0 decoded for command addresses).
enum class St { Read, C1, C2, Prog, E3, E4, E5, Id };
St st = St::Read;
bool in_id = false;
int busy = 0;            // reads left that return Data# status
uint8_t busy_data = 0;   // value being programmed (0xFF for erase)
uint8_t toggle = 0;

bool bit(uint16_t a, int n) { return (a >> n) & 1; }

uint32_t chip_addr(uint16_t a) {
  // ROM A14..A18 come from the latch when CPU A14 = 1 (its /OE = !A14), else 2.2k pull-downs.
  uint32_t hi = bit(a, 14) ? (latch & 0x1F) : 0;
  return (hi << 14) | (a & 0x3FFF);
}

void flash_cmd(uint32_t ca, uint8_t d) {
  uint16_t c = ca & 0x7FFF;
  // The 4th cycle of a program sequence is data, whatever its value (0xF0 included).
  if (d == 0xF0 && st != St::Prog) { st = St::Read; in_id = false; return; }
  switch (st) {
    case St::Read:
    case St::Id:
      st = (c == 0x5555 && d == 0xAA) ? St::C1 : st;
      break;
    case St::C1:
      st = (c == 0x2AAA && d == 0x55) ? St::C2 : (in_id ? St::Id : St::Read);
      break;
    case St::C2:
      if (c != 0x5555) { st = St::Read; break; }
      if (d == 0xA0) st = St::Prog;
      else if (d == 0x80) st = St::E3;
      else if (d == 0x90) { in_id = true; st = St::Id; }
      else st = St::Read;
      break;
    case St::Prog:
      flash[ca] &= d;  // programming can only clear bits
      busy = 3; busy_data = d;
      st = St::Read;
      break;
    case St::E3: st = (c == 0x5555 && d == 0xAA) ? St::E4 : St::Read; break;
    case St::E4: st = (c == 0x2AAA && d == 0x55) ? St::E5 : St::Read; break;
    case St::E5:
      if (c == 0x5555 && d == 0x10) { std::fill(flash.begin(), flash.end(), 0xFF); busy = 20; busy_data = 0xFF; }
      else if (d == 0x30) { std::fill(flash.begin() + (ca & ~0xFFFu), flash.begin() + (ca & ~0xFFFu) + 0x1000, 0xFF); busy = 8; busy_data = 0xFF; }
      st = St::Read;
      break;
  }
}

uint8_t flash_read(uint32_t ca) {
  if (busy > 0) {
    busy--;
    toggle ^= 0x40;
    return (uint8_t)((~busy_data & 0x80) | toggle);
  }
  if (in_id) return (ca & 1) ? 0xB7 : 0xBF;
  return flash[ca];
}

uint16_t fram_addr(uint16_t a) { return a & 0x1FFF; }  // F-RAM A13/A14 tied to GND

}  // namespace

// ---- cart bus: decode exactly as the 74HC32/74HC00 network in the netlist ----
static bool cs_n(uint16_t a) { return !(a >= 0xA000 && a < 0xFE00); }

uint8_t bus_read(uint16_t a) {
  bool rom_ce_n = bit(a, 15);
  bool fram_ce_n = cs_n(a) || bit(a, 14) || !bit(a, 13);
  if (!rom_ce_n) return flash_read(chip_addr(a));
  if (!fram_ce_n) return fram[fram_addr(a)];
  return 0xFF;  // open bus
}

void bus_write(uint16_t a, uint8_t d) {
  bool wr_a15 = bit(a, 15);  // /WR is low during the write
  bool latch_clk_low = !(wr_a15 || bit(a, 14) || bit(a, 12) || !bit(a, 13));
  bool flash_we_n = wr_a15 || !bit(a, 14);
  bool fram_ce_n = cs_n(a) || bit(a, 14) || !bit(a, 13);
  if (latch_clk_low) latch = d;  // clocks on the rising /WR edge
  if (!flash_we_n) flash_cmd(chip_addr(a), d);
  if (!fram_ce_n) fram[fram_addr(a)] = d;
}

// ---- stdio transport ----
int ser_read() {
  int c = std::getchar();
  if (c == EOF) throw 0;
  return c;
}
void ser_write(uint8_t b) { std::putchar(b); }
void ser_flush() { std::fflush(stdout); }
void delay_us(uint32_t) {}

static void load(const char* path, std::vector<uint8_t>& mem) {
  if (FILE* f = std::fopen(path, "rb")) { size_t n = std::fread(mem.data(), 1, mem.size(), f); (void)n; std::fclose(f); }
}
static void save(const char* path, const std::vector<uint8_t>& mem) {
  if (FILE* f = std::fopen(path, "wb")) { std::fwrite(mem.data(), 1, mem.size(), f); std::fclose(f); }
}

int main(int argc, char** argv) {
  std::srand((unsigned)std::time(nullptr));
  latch = (uint8_t)std::rand();
  for (auto& b : fram) b = (uint8_t)std::rand();
  if (argc > 1) load(argv[1], flash);
  if (argc > 2) load(argv[2], fram);
  try {
    for (;;) {
      int op = ser_read();
      if (!gbflash::handle(op)) { std::fprintf(stderr, "cart_sim: unknown op 0x%02x\n", op); return 2; }
    }
  } catch (int) {
  }
  if (argc > 1) save(argv[1], flash);
  if (argc > 2) save(argv[2], fram);
  return 0;
}
