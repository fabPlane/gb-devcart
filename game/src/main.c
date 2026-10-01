// Bit Catcher — tiny homebrew game for the GB DEVCART r1 (GBDK-2020).
//
// Catch the falling cartridges with the paddle, dodge the bugs. Missing a cartridge or catching a
// bug costs a life; the high score is kept in the cart's F-RAM (no battery needed).
#include <gb/gb.h>
#include <gbdk/console.h>
#include <rand.h>
#include <stdint.h>
#include <stdio.h>

// ---- cart glue --------------------------------------------------------------------------------
// The devcart's 74HC574 bank latch powers up random. Bank 0 (0x0000-0x3FFF) is fixed, so select
// bank 1 before anything touches 0x4000-0x7FFF. Everything in this game lives in bank 0, and the
// write is also what an MBC5 expects, so the ROM runs the same in emulators.
#define BANK_REG (*(volatile uint8_t *)0x2000)

// High score in F-RAM (0xA000). The devcart's F-RAM is always enabled; the 0x0A write to 0x0000
// is for MBC5 emulators and is ignored by the devcart's decoder.
#define SRAM ((volatile uint8_t *)0xA000)  // [0..3] = "GBDC", [4..5] = high score (LE)
static const uint8_t magic[4] = {'G', 'B', 'D', 'C'};

static uint16_t load_hiscore(void) {
  uint16_t hi = 0;
  uint8_t ok = 1;
  ENABLE_RAM;
  for (uint8_t i = 0; i < 4; i++)
    if (SRAM[i] != magic[i]) ok = 0;
  if (ok) hi = SRAM[4] | ((uint16_t)SRAM[5] << 8);
  DISABLE_RAM;
  return hi;
}

static void store_hiscore(uint16_t hi) {
  ENABLE_RAM;
  for (uint8_t i = 0; i < 4; i++) SRAM[i] = magic[i];
  SRAM[4] = (uint8_t)hi;
  SRAM[5] = (uint8_t)(hi >> 8);
  DISABLE_RAM;
}

// ---- graphics (2bpp, colour 3 = both planes set) ----------------------------------------------
static const uint8_t sprite_tiles[] = {
    // 0: paddle segment
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0xFF,
    // 1: cartridge
    0x7C, 0x7C, 0x44, 0x7C, 0x54, 0x7C, 0x44, 0x7C, 0x7C, 0x7C, 0x7C, 0x7C, 0x54, 0x54, 0x54, 0x54,
    // 2: bug
    0x24, 0x24, 0x18, 0x18, 0x7E, 0x7E, 0xDB, 0xFF, 0x7E, 0x7E, 0x3C, 0x3C, 0x66, 0x66, 0x42, 0x42,
};
#define T_PADDLE 0
#define T_CART 1
#define T_BUG 2

// ---- game state ---------------------------------------------------------------------------------
#define PADDLE_SPRITES 3
#define PADDLE_W 24
#define PADDLE_Y 136  // screen y of the paddle bar
#define N_OBJ 4
#define FIRST_OBJ_SPRITE PADDLE_SPRITES

typedef struct {
  uint8_t active, kind, x;
  uint16_t y;  // 1/16 pixel
} obj_t;

static obj_t objs[N_OBJ];
static uint8_t paddle_x;
static uint16_t score, hiscore;
static uint8_t lives, speed, spawn_timer;

static void draw_hud(void) {
  gotoxy(0, 0);
  printf("SCORE %u  HI %u   ", score, hiscore);
  gotoxy(0, 1);
  printf("LIVES %u           ", (uint16_t)lives);
}

static void place_paddle(void) {
  for (uint8_t i = 0; i < PADDLE_SPRITES; i++) move_sprite(i, paddle_x + 8 + i * 8, PADDLE_Y + 16 - 4);
}

static void hide_obj(uint8_t i) {
  objs[i].active = 0;
  move_sprite(FIRST_OBJ_SPRITE + i, 0, 0);
}

static void spawn(void) {
  for (uint8_t i = 0; i < N_OBJ; i++) {
    if (objs[i].active) continue;
    objs[i].active = 1;
    objs[i].kind = (rand() & 3) == 0 ? T_BUG : T_CART;  // 1 in 4 is a bug
    objs[i].x = 8 + (uint8_t)(rand() % 144);
    objs[i].y = (uint16_t)24 << 4;
    set_sprite_tile(FIRST_OBJ_SPRITE + i, objs[i].kind);
    return;
  }
}

static void wait_start(void) {
  while (!(joypad() & J_START)) vsync();
  while (joypad() & J_START) vsync();
}

static void title(void) {
  HIDE_SPRITES;
  cls();
  gotoxy(4, 4);  printf("BIT CATCHER");
  gotoxy(2, 6);  printf("GB DEVCART r1 demo");
  gotoxy(2, 9);  printf("catch the carts,");
  gotoxy(2, 10); printf("dodge the bugs!");
  gotoxy(4, 13); printf("HI SCORE %u", hiscore);
  gotoxy(4, 16); printf("PRESS START");
  wait_start();
  initrand(DIV_REG);
}

static void play(void) {
  cls();
  score = 0; lives = 3; speed = 12; spawn_timer = 30;
  paddle_x = 68;
  for (uint8_t i = 0; i < N_OBJ; i++) hide_obj(i);
  place_paddle();
  SHOW_SPRITES;
  draw_hud();

  while (lives) {
    uint8_t keys = joypad();
    if ((keys & J_LEFT) && paddle_x > 2) paddle_x -= 2;
    if ((keys & J_RIGHT) && paddle_x < 160 - PADDLE_W - 2) paddle_x += 2;
    place_paddle();

    if (--spawn_timer == 0) {
      spawn();
      spawn_timer = (uint8_t)(40 - (speed > 36 ? 36 : speed));
    }

    uint8_t hud_dirty = 0;
    for (uint8_t i = 0; i < N_OBJ; i++) {
      if (!objs[i].active) continue;
      objs[i].y += speed;
      uint8_t sy = (uint8_t)(objs[i].y >> 4);
      uint8_t ox = objs[i].x;
      if (sy + 8 >= PADDLE_Y && sy <= PADDLE_Y + 4 && ox + 6 >= paddle_x && ox <= paddle_x + PADDLE_W - 2) {
        if (objs[i].kind == T_CART) {
          score++;
          if ((score & 7) == 0 && speed < 48) speed += 2;  // faster every 8 catches
        } else {
          lives--;
        }
        hide_obj(i);
        hud_dirty = 1;
      } else if (sy > 144) {
        if (objs[i].kind == T_CART) { lives--; hud_dirty = 1; }
        hide_obj(i);
      } else {
        move_sprite(FIRST_OBJ_SPRITE + i, ox + 8, sy + 16);
      }
    }
    if (hud_dirty) draw_hud();
    vsync();
  }

  for (uint8_t i = 0; i < N_OBJ; i++) hide_obj(i);
  if (score > hiscore) {
    hiscore = score;
    store_hiscore(hiscore);
  }
  gotoxy(5, 8);  printf("GAME OVER");
  gotoxy(4, 10); printf("SCORE %u", score);
  gotoxy(3, 13); printf("PRESS START");
  wait_start();
}

void main(void) {
  BANK_REG = 1;

  DISPLAY_OFF;
  set_sprite_data(0, 3, sprite_tiles);
  for (uint8_t i = 0; i < PADDLE_SPRITES; i++) set_sprite_tile(i, T_PADDLE);
  OBP0_REG = 0xE4;
  BGP_REG = 0xE4;
  SHOW_BKG;
  DISPLAY_ON;

  hiscore = load_hiscore();
  for (;;) {
    title();
    play();
  }
}
