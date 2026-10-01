#!/usr/bin/env python3
"""Headless smoke test: boot Bit Catcher in PyBoy, start a game, play blind, check HUD + save."""
import sys
from pyboy import PyBoy
from pyboy.utils import WindowEvent

rom = sys.argv[1] if len(sys.argv) > 1 else "dist/bitcatcher.gb"
out = sys.argv[2] if len(sys.argv) > 2 else "dist"
pb = PyBoy(rom, window="null", sound_emulated=False)
pb.set_emulation_speed(0)

def run(n):
    for _ in range(n):
        pb.tick()

def press(ev_down, ev_up, hold=4):
    pb.send_input(ev_down); run(hold); pb.send_input(ev_up); run(2)

def screen_text():
    rows = []
    tm = pb.tilemap_background
    for y in range(18):
        rows.append("".join(chr(t - 256 + 0x20) if 256 <= t < 256 + 0x60 else " " for t in (tm[x, y] for x in range(20))))
    return "\n".join(rows)

run(120)
pb.screen.image.save(f"{out}/screenshot-title.png")
title = screen_text()
print(title)
assert "BIT CATCHER" in title, "title screen not shown"

press(WindowEvent.PRESS_BUTTON_START, WindowEvent.RELEASE_BUTTON_START)
# simple bot: chase the lowest falling cartridge sprite
for frame in range(60 * 40):
    sprites = [pb.get_sprite(i) for i in range(3, 7)]
    carts = [s for s in sprites if s.on_screen and s.tiles[0].tile_identifier == 1]
    paddle = pb.get_sprite(1).x
    pb.send_input(WindowEvent.RELEASE_ARROW_LEFT); pb.send_input(WindowEvent.RELEASE_ARROW_RIGHT)
    if carts:
        target = max(carts, key=lambda s: s.y).x
        if target < paddle - 4: pb.send_input(WindowEvent.PRESS_ARROW_LEFT)
        elif target > paddle + 4: pb.send_input(WindowEvent.PRESS_ARROW_RIGHT)
    pb.tick()
    if frame == 60 * 12:
        pb.screen.image.save(f"{out}/screenshot-game.png")
    if "GAME OVER" in screen_text():
        break
text = screen_text()
print(text)
pb.screen.image.save(f"{out}/screenshot-end.png")
assert "GAME OVER" in text, "game did not end"
score = int(text.split("SCORE")[-1].split()[0])
press(WindowEvent.PRESS_BUTTON_START, WindowEvent.RELEASE_BUTTON_START)
run(60)
title2 = screen_text()
assert f"HI SCORE {score}" in title2, f"high score {score} not kept in cart RAM"
print(f"high score {score} stored in F-RAM and shown on the title screen")
pb.stop(save=False)
print("ok")
