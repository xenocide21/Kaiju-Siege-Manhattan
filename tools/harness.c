/* Headless test harness for Kaiju Siege, built on HuC's tgemu core.
 * Usage: harness rom.pce script.txt outdir
 * Script commands (one per line):
 *   run N [buttons]   run N frames holding buttons (L R U D 1 2 S R=run as 'X')
 *   shot NAME         save screenshot outdir/NAME.ppm
 *   ram ADDR LEN      print LEN bytes of work RAM starting at CPU address ADDR (hex, 0x2000-based)
 *   watch ADDR N      print 16-bit word at ADDR every frame for next run (N words)
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "shared.h"
#include "h6280.h"
#include "vdc.h"

#define SCR_W 320
#define SCR_H 240
unsigned char *pixels;
FILE *recf = 0; long recn = 0;
static void rec_frame(void) { int i; if (!recf) return; for (i = 0; i < snd.buffer_size; i++) { short l = snd.buffer[0][i], r = snd.buffer[1][i]; fwrite(&l,2,1,recf); fwrite(&r,2,1,recf); recn++; } }
void dump_screen(void) {}

static void save_ppm(const char *path) {
    FILE *f = fopen(path, "wb");
    int x, y;
    fprintf(f, "P6\n256 224\n255\n");
    for (y = 0; y < 224; y++) {
        for (x = 0; x < 256; x++) {
            unsigned short p = ((unsigned short *)pixels)[y * SCR_W + x + 0x20];
            unsigned char rgb[3];
            rgb[0] = ((p >> 13) & 7) * 255 / 7;
            rgb[1] = ((p >> 8) & 7) * 255 / 7;
            rgb[2] = ((p >> 2) & 7) * 255 / 7;
            fwrite(rgb, 3, 1, f);
        }
    }
    fclose(f);
}

static unsigned parse_buttons(const char *s) {
    unsigned b = 0;
    for (; s && *s; s++) {
        switch (*s) {
        case 'L': b |= INPUT_LEFT; break;
        case 'R': b |= INPUT_RIGHT; break;
        case 'U': b |= INPUT_UP; break;
        case 'D': b |= INPUT_DOWN; break;
        case '1': b |= INPUT_B1; break;
        case '2': b |= INPUT_B2; break;
        case 'S': b |= INPUT_SELECT; break;
        case 'X': b |= INPUT_RUN; break;
        }
    }
    return b;
}

int main(int argc, char **argv) {
    FILE *sf;
    char line[256], outdir[200];
    unsigned watch_addr = 0, watch_n = 0;
    long frame = 0;
    if (argc < 4) { fprintf(stderr, "usage\n"); return 1; }
    strcpy(outdir, argv[3]);
    if (load_rom(argv[1], 0, 0) != 1) { fprintf(stderr, "rom load failed\n"); return 1; }
    pixels = calloc(SCR_W * SCR_H * 2, 1);
    bitmap.width = SCR_W; bitmap.height = SCR_H; bitmap.depth = 16;
    bitmap.granularity = 2; bitmap.data = pixels; bitmap.pitch = SCR_W * 2;
    bitmap.viewport.w = 256; bitmap.viewport.h = 240;
    bitmap.viewport.x = 0x20; bitmap.viewport.y = 0;
    system_init(44100);
    system_reset();
    sf = fopen(argv[2], "r");
    while (fgets(line, sizeof line, sf)) {
        char cmd[32], arg1[64] = "", arg2[64] = "";
        if (sscanf(line, "%31s %63s %63s", cmd, arg1, arg2) < 1) continue;
        if (!strcmp(cmd, "run")) {
            int n = atoi(arg1), i;
            input.pad[0] = parse_buttons(arg2);
            for (i = 0; i < n; i++) {
                bitmap.data = pixels;
                system_frame(0); rec_frame();
                frame++;
                if (watch_n) {
                    unsigned k;
                    printf("f%ld:", frame);
                    for (k = 0; k < watch_n; k++) {
                        unsigned a = (watch_addr - 0x2000) + k * 2;
                        printf(" %d", (short)(ram[a] | (ram[a + 1] << 8)));
                    }
                    printf("\n");
                }
            }
        } else if (!strcmp(cmd, "shot")) {
            char path[300];
            sprintf(path, "%s/%s.ppm", outdir, arg1);
            save_ppm(path);
        } else if (!strcmp(cmd, "ram")) {
            unsigned a = strtoul(arg1, 0, 16) - 0x2000, n = atoi(arg2), k;
            printf("ram %s:", arg1);
            for (k = 0; k < n; k++) printf(" %02x", ram[a + k]);
            printf("\n");
        } else if (!strcmp(cmd, "watch")) {
            watch_addr = strtoul(arg1, 0, 16); watch_n = atoi(arg2);
        } else if (!strcmp(cmd, "pc")) {
            int k;
            for (k = 0; k < 8; k++) {
                system_frame(0); frame++;
                printf("pc %04x mpr2..7?\n", h6280_get_pc());
            }
        } else if (!strcmp(cmd, "auto")) {
            /* auto N ballx bally bst : simple flipper bot */
            char a3[64], a4[64], a5[64], a6[64] = "0"; int n, i, k; unsigned ar; static int hl = 0, hr = 0, pl = 0;
            unsigned ax, ay, as;
            sscanf(line, "%*s %d %63s %63s %63s %63s", &n, a3, a4, a5, a6);
            ar = strtoul(a6, 0, 16); if (ar) ar -= 0x2000;
            ax = strtoul(a3, 0, 16) - 0x2000; ay = strtoul(a4, 0, 16) - 0x2000; as = strtoul(a5, 0, 16) - 0x2000;
            for (i = 0; i < n; i++) {
                unsigned b = 0;
                for (k = 0; k < 3; k++) {
                    int st = ram[as + k];
                    int x = (short)(ram[ax + k*2] | (ram[ax + k*2 + 1] << 8)) / 32;
                    int y = (short)(ram[ay + k*2] | (ram[ay + k*2 + 1] << 8)) / 32;
                    int inroom = ar ? ram[ar] : 0;
                    int ylo = inroom ? 168 : 448, yhi = inroom ? 198 : 482, cxm = inroom ? 128 : 117;
                    if (st == 1 && y > ylo && y < yhi) {
                        if (x < cxm && hl == 0) hl = 10;
                        if (x >= cxm && hr == 0) hr = 10;
                    }
                    if (st == 2 && k == 0) { pl++; }
                }
                if (pl > 0 && pl < 45) b |= INPUT_B1;
                if (pl >= 60) pl = 0;
                if (hl > 0) { if (hl > 3) b |= INPUT_LEFT; hl--; if (hl == 0) hl = -8; }
                else if (hl < 0) hl++;
                if (hr > 0) { if (hr > 3) b |= INPUT_B2; hr--; if (hr == 0) hr = -8; }
                else if (hr < 0) hr++;

                input.pad[0] = b;
                bitmap.data = pixels; system_frame(0); rec_frame(); frame++;
                if (watch_n && (frame % (watch_n > 100 ? 1 : 60)) == 0) {
                    unsigned kk; printf("f%ld:", frame);
                    for (kk = 0; kk < watch_n; kk++) { unsigned a = (watch_addr - 0x2000) + kk; printf(" %d", ram[a]); }
                    printf("\n");
                }
            }
        } else if (!strcmp(cmd, "poke")) {
            ram[strtoul(arg1, 0, 16) - 0x2000] = strtoul(arg2, 0, 0);
        } else if (!strcmp(cmd, "rec")) {
            recf = fopen(arg1, "wb"); recn = 0;
        } else if (!strcmp(cmd, "endrec")) {
            fclose(recf); recf = 0; fprintf(stderr, "recorded %ld samples\n", recn);
        } else if (!strcmp(cmd, "log")) { extern int vdc_log_on; vdc_log_on = 1;
        } else if (!strcmp(cmd, "vdc")) {
            int k; printf("vdc:");
            for (k = 0; k < 20; k++) printf(" r%d=%04x", k, reg[k]);
            printf(" status=%02x\n", status);
        } else if (!strcmp(cmd, "unwatch")) {
            watch_n = 0;
        }
    }
    fprintf(stderr, "ran %ld frames\n", frame);
    return 0;
}
