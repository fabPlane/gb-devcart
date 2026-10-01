# Bit Catcher — build with GBDK-2020 (https://github.com/gbdk-2020/gbdk-2020/releases).
#   make GBDK_HOME=/path/to/gbdk
# Cart header: MBC5+RAM+BATTERY (0x1B), 32 KB ROM, 8 KB RAM — matches the devcart's
# bank register at 0x2000 and its 8 KB F-RAM window at 0xA000.
GBDK_HOME ?= ../../gbdk
LCC = $(GBDK_HOME)/bin/lcc

ROM = dist/bitcatcher.gb
LCCFLAGS = -Wl-yt0x1B -Wl-ya1 -Wm-yn"BITCATCHER" -Wm-yc

all: $(ROM)

$(ROM): src/main.c
	mkdir -p build dist
	$(LCC) $(LCCFLAGS) -Wl-m -o build/bitcatcher.gb $<
	cp build/bitcatcher.gb $@
	@echo "built $@"

clean:
	rm -rf build

.PHONY: all clean
