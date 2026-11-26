#!/bin/sh
# Build Kaiju Siege: Manhattan.
# Needs the HuCC toolchain (https://github.com/pce-devel/huc) built; set HUC to its folder.
HUC=${HUC:-$HOME/huc}
cd "$(dirname "$0")/src" || exit 1
export PCE_INCLUDE=$HUC/include/hucc PCE_PCEAS=$HUC/bin/pceas
rm -f kaiju.pce
$HUC/bin/hucc -O2 -fno-recursive kaiju.c > build.log 2>&1
if [ -f kaiju.pce ]; then echo "OK: src/kaiju.pce"; else cat build.log; exit 1; fi
