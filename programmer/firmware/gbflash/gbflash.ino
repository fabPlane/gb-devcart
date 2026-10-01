// gbflash.ino — Arduino Mega 2560 (5 V) USB programmer for the GB DEVCART r1.
//
// Wiring (see programmer/README.md for the full table):
//   cart A0..A7   <- PORTA  (D22..D29)
//   cart A8..A15  <- PORTC  (D37..D30, PC0 = D37)
//   cart D0..D7  <-> PORTL  (D49..D42, PL0 = D49)
//   cart /WR <- D2 (PE4), /RD <- D3 (PE5), /CS <- D4 (PG5), /RESET <- D5 (PE3)
//   cart VCC <- 5V, GND <- GND, CLK and AUDIO_IN unconnected.
// Host side: programmer/host/gbflash.py at 1 000 000 baud.
#include "gbflash_core.h"

#define WR_BIT _BV(PE4)
#define RD_BIT _BV(PE5)
#define RST_BIT _BV(PE3)
#define CS_BIT _BV(PG5)

static inline void set_addr(uint16_t a) {
  PORTA = (uint8_t)a;
  PORTC = (uint8_t)(a >> 8);
}

static inline bool cs_region(uint16_t a) { return a >= 0xA000 && a < 0xFE00; }

// ~70 ns access time on the flash / F-RAM: 4 NOPs at 16 MHz is 250 ns, plenty of margin.
#define BUS_SETTLE() __asm__ __volatile__("nop\n\tnop\n\tnop\n\tnop\n\t")

uint8_t bus_read(uint16_t addr) {
  DDRL = 0x00;
  PORTL = 0x00;
  set_addr(addr);
  if (cs_region(addr)) PORTG &= ~CS_BIT;
  PORTE &= ~RD_BIT;
  BUS_SETTLE(); BUS_SETTLE();
  uint8_t d = PINL;
  PORTE |= RD_BIT;
  PORTG |= CS_BIT;
  return d;
}

void bus_write(uint16_t addr, uint8_t d) {
  set_addr(addr);
  PORTL = d;
  DDRL = 0xFF;
  if (cs_region(addr)) PORTG &= ~CS_BIT;
  PORTE &= ~WR_BIT;  // falling /WR: latch-clock and flash /WE go low
  BUS_SETTLE();
  PORTE |= WR_BIT;   // rising /WR: bank latch clocks in, flash latches data
  PORTG |= CS_BIT;
  DDRL = 0x00;
}

int ser_read() {
  while (!Serial.available()) {}
  return Serial.read();
}
void ser_write(uint8_t b) { Serial.write(b); }
void ser_flush() { Serial.flush(); }
void delay_us(uint32_t us) {
  if (us >= 1000) delay(us / 1000);
  delayMicroseconds(us % 1000);
}

void setup() {
  DDRA = 0xFF;
  DDRC = 0xFF;
  DDRL = 0x00;
  PORTE |= WR_BIT | RD_BIT | RST_BIT;
  DDRE |= WR_BIT | RD_BIT | RST_BIT;
  PORTG |= CS_BIT;
  DDRG |= CS_BIT;
  Serial.begin(1000000);
}

void loop() {
  if (Serial.available()) gbflash::handle(Serial.read());
}
