// gbflash_core.h — USB programmer protocol for the GB DEVCART r1, hardware independent.
//
// The board-specific sketch (gbflash.ino) or the native simulator (programmer/sim) provides:
//   uint8_t bus_read(uint16_t addr);              // one Game Boy bus read cycle
//   void    bus_write(uint16_t addr, uint8_t d);  // one Game Boy bus write cycle
//   int     ser_read();                           // blocking, returns 0..255
//   void    ser_write(uint8_t b);
//   void    ser_flush();
//   void    delay_us(uint32_t us);
// Both drive /CS low for 0xA000-0xFDFF, exactly like the console.
//
// Cart mapping (see README "Memory map"): the SST39SF040 sees
//   chip A13..A0  = CPU A13..A0
//   chip A18..A14 = bank latch Q4..Q0 when CPU A14 = 1, else 0 (pull-downs)
// and its /WE is only asserted for CPU writes to 0x4000-0x7FFF. So every flash command goes
// through the 0x4000 window: chip 0x5555 = bank 1 + CPU 0x5555, chip 0x2AAA = bank 0 + CPU 0x6AAA.
//
// Wire protocol (host -> device, little endian); every command answers with a status byte
// 'K' (ok), 'T' (timeout) or 'F' (verify failure) unless it returns data:
//   'I'                          -> "GBFLASH1\n"
//   'D'                          -> manufacturer id, device id (SST39SF040: 0xBF 0xB7)
//   'B' bank                     -> K   (writes the bank latch at 0x2000)
//   'R' a16 n16                  -> n raw bus bytes starting at CPU address a
//   'W' a16 n16 data[n]          -> K   (raw bus writes, e.g. F-RAM restore at 0xA000)
//   'E'                          -> K|T (chip erase, up to ~100 ms)
//   'S' fa24                     -> K|T (4 KB sector erase at flash address fa)
//   'P' fa24 n16 data[n] (n<=256)-> K|T|F (byte-program n bytes at flash address fa)
//   'V' rev                      -> K   (cart revision: 1 = r1 discrete mapper, 2 = r2 FPGA mapper;
//                                        2 also enters the r2 dev mode, see below)
//   'b' bank16                   -> K   (16-bit bank select: r2 uses 0x2000 low byte + 0x3000 bit 8)
//
// r2 (GB DEVCART r2, FPGA mapper, 3.3 V x8 AMD-command-set NOR flash, up to 8 MB):
//   dev mode is entered by writing "GBDV" to 0x6000; in dev mode writes to 0x4000-0x7FFF reach the
//   flash. Byte-mode command addresses 0xAAA / 0x555 sit in bank 0, so they are CPU 0x4AAA / 0x4555.
//   Writing 0xD0 to 0x0000 leaves dev mode (the host does that when it is done).
#pragma once
#include <stdint.h>

uint8_t bus_read(uint16_t addr);
void bus_write(uint16_t addr, uint8_t d);
int ser_read();
void ser_write(uint8_t b);
void ser_flush();
void delay_us(uint32_t us);

namespace gbflash {

static const uint16_t BANK_REG = 0x2000;
static const uint16_t WINDOW = 0x4000;
static const uint16_t CMD_5555 = 0x5555;  // with bank 1
static const uint16_t CMD_2AAA = 0x6AAA;  // with bank 0
static const uint16_t MAX_CHUNK = 256;

static const uint16_t R2_CMD_AAA = 0x4AAA;  // flash 0xAAA with bank 0
static const uint16_t R2_CMD_555 = 0x4555;  // flash 0x555 with bank 0

static uint16_t g_bank = 0xFFFF;
static uint8_t g_rev = 1;

inline void set_bank(uint16_t bank) {
  bus_write(BANK_REG, (uint8_t)bank);
  if (g_rev == 2) bus_write(0x3000, (uint8_t)(bank >> 8) & 1);
  g_bank = bank;
}

inline void enter_dev_mode() {
  const char* key = "GBDV";
  while (*key) bus_write(0x6000, (uint8_t)*key++);
}

inline void unlock() {
  if (g_rev == 2) {
    if (g_bank != 0) set_bank(0);
    bus_write(R2_CMD_AAA, 0xAA);
    bus_write(R2_CMD_555, 0x55);
    return;
  }
  set_bank(1); bus_write(CMD_5555, 0xAA);
  set_bank(0); bus_write(CMD_2AAA, 0x55);
}

inline void command(uint8_t cmd) {
  unlock();
  if (g_rev == 2) { bus_write(R2_CMD_AAA, cmd); return; }
  set_bank(1); bus_write(CMD_5555, cmd);
}

inline uint16_t window_addr(uint32_t fa) { return WINDOW | (uint16_t)(fa & 0x3FFF); }

// Data# polling: DQ7 reads back inverted until the internal operation finishes.
inline bool wait_done(uint16_t cpu_addr, uint8_t expect, uint32_t timeout_us, uint32_t step_us) {
  for (uint32_t t = 0; t <= timeout_us; t += step_us) {
    if ((bus_read(cpu_addr) & 0x80) == (expect & 0x80)) {
      // DQ7 can flip a cycle before DQ0..6 settle; confirm with a second read.
      return (bus_read(cpu_addr) & 0x80) == (expect & 0x80);
    }
    if (step_us) delay_us(step_us);
  }
  return false;
}

inline bool program_byte(uint32_t fa, uint8_t d) {
  if (d == 0xFF) return true;  // erased state, nothing to program
  command(0xA0);
  set_bank((uint16_t)(fa >> 14));
  uint16_t a = window_addr(fa);
  bus_write(a, d);
  return wait_done(a, d, 200, 1);  // TBP is 20 us max
}

inline bool chip_erase() {
  command(0x80);
  command(0x10);
  // SST39SF040: 100 ms max. 4-8 MB AMD-style parts: tens of seconds, up to a few minutes.
  return g_rev == 2 ? wait_done(WINDOW, 0xFF, 300000000UL, 20000) : wait_done(WINDOW, 0xFF, 300000, 1000);
}

inline bool sector_erase(uint32_t fa) {
  command(0x80);
  unlock();
  set_bank((uint16_t)(fa >> 14));
  uint16_t a = window_addr(fa & ~0xFFFUL);
  bus_write(a, 0x30);
  return wait_done(a, 0xFF, g_rev == 2 ? 5000000UL : 100000UL, 500);  // 25 ms (r1) / ~1-3 s (r2)
}

inline void read_id(uint8_t* mfr, uint8_t* dev) {
  command(0x90);
  // Bank 0 is the fixed window at 0x0000 (latch outputs off, pull-downs hold A14..A18 low).
  *mfr = bus_read(0x0000);
  *dev = bus_read(g_rev == 2 ? 0x0002 : 0x0001);  // byte mode: word 1 is byte address 2
  if (g_rev == 2) bus_write(WINDOW, 0xF0); else command(0xF0);
}

inline uint16_t rd16() { uint16_t lo = (uint16_t)ser_read(); return lo | ((uint16_t)ser_read() << 8); }
inline uint32_t rd24() { uint32_t lo = rd16(); return lo | ((uint32_t)ser_read() << 16); }

// Handles one command; returns false on an unknown opcode.
inline bool handle(int op) {
  static uint8_t buf[MAX_CHUNK];
  switch (op) {
    case 'I': {
      const char* s = "GBFLASH1\n";
      while (*s) ser_write((uint8_t)*s++);
      break;
    }
    case 'D': {
      uint8_t m, d;
      read_id(&m, &d);
      ser_write(m); ser_write(d);
      break;
    }
    case 'B':
      set_bank((uint8_t)ser_read());
      ser_write('K');
      break;
    case 'b':
      set_bank(rd16());
      ser_write('K');
      break;
    case 'V':
      g_rev = (uint8_t)ser_read() == 2 ? 2 : 1;
      g_bank = 0xFFFF;
      if (g_rev == 2) enter_dev_mode();
      ser_write('K');
      break;
    case 'R': {
      uint16_t a = rd16(), n = rd16();
      for (uint16_t i = 0; i < n; i++) ser_write(bus_read((uint16_t)(a + i)));
      break;
    }
    case 'W': {
      uint16_t a = rd16(), n = rd16();
      for (uint16_t i = 0; i < n; i++) bus_write((uint16_t)(a + i), (uint8_t)ser_read());
      ser_write('K');
      break;
    }
    case 'E':
      ser_write(chip_erase() ? 'K' : 'T');
      break;
    case 'S': {
      uint32_t fa = rd24();
      ser_write(sector_erase(fa) ? 'K' : 'T');
      break;
    }
    case 'P': {
      uint32_t fa = rd24();
      uint16_t n = rd16();
      if (n > MAX_CHUNK) n = MAX_CHUNK;
      for (uint16_t i = 0; i < n; i++) buf[i] = (uint8_t)ser_read();
      uint8_t status = 'K';
      for (uint16_t i = 0; i < n && status == 'K'; i++) {
        if (!program_byte(fa + i, buf[i])) status = 'T';
      }
      if (status == 'K') {  // read back through the window
        for (uint16_t i = 0; i < n; i++) {
          uint32_t f = fa + i;
          if (g_bank != (uint16_t)(f >> 14)) set_bank((uint16_t)(f >> 14));
          if (bus_read(window_addr(f)) != buf[i]) { status = 'F'; break; }
        }
      }
      ser_write(status);
      break;
    }
    default:
      return false;
  }
  ser_flush();
  return true;
}

}  // namespace gbflash
