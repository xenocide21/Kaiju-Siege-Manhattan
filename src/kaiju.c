/*
 * KAIJU SIEGE: MANHATTAN  --  TurboGrafx-16 / PC Engine homebrew pinball
 * Concept & design: Xenocide21      Code & art: Claude
 * Build: hucc -O2 -fno-recursive kaiju.c   (HuCC toolchain)
 *
 * Positions are in 1/32 pixel units, velocities in 1/32 px per physics substep
 * (4 substeps per frame). The table is 256x512 px; the BAT is 64x64 tiles:
 * columns 0-31 hold the table, columns 32-63 hold the HUD (rows 0-1) and the
 * title screen (rows 4-31).
 */
#include "hucc-systemcard.h"
#include "hucc-baselib.h"
#include "hucc-gfx.h"
#include "hucc-scroll.h"
#include "hucc-old-spr.h"
#include <stdlib.h>
#include <string.h>
#include "data/gen.h"

#incbin(bgchr_bin, "data/bg_chr.bin");
#incbin(bgbat_bin, "data/bg_bat.bin");
#incbin(bgpal_bin, "data/bg_pal.bin");
#incbin(sprchr_bin, "data/spr_chr.bin");
#incbin(sprpal_bin, "data/spr_pal.bin");
#incbin(coll, "data/coll.bin");
#incbin(r1chr_bin, "data/room1_chr.bin");
#incbin(r1bat_bin, "data/room1_bat.bin");
#incbin(r1pal_bin, "data/room1_pal.bin");
#incbin(r1coll, "data/room1_coll.bin");
#incbin(r2chr_bin, "data/room2_chr.bin");
#incbin(r2bat_bin, "data/room2_bat.bin");
#incbin(r2pal_bin, "data/room2_pal.bin");
#incbin(r2coll, "data/room2_coll.bin");
#incbin(r3chr_bin, "data/room3_chr.bin");
#incbin(r3bat_bin, "data/room3_bat.bin");
#incbin(r3pal_bin, "data/room3_pal.bin");
#incbin(r3coll, "data/room3_coll.bin");

#define VRAM_CHR 0x1000
#define VMAX 72
#define CAM_MAX 304
#define MAXB 3

#define MAT_WALL 1
#define MAT_SLING 2
#define MAT_BUMP 3
#define MAT_BOSS 4
#define MAT_EMPIRE 5

/* sprite slots */
#define S_BALL 0
#define S_LFLIP 3
#define S_RFLIP 4
#define S_EYE 5
#define S_TENT 8
#define S_TAXI 12
#define S_TANK 13
#define S_SHELL 14
#define S_EXPL 15
#define S_PLUNGER 16
#define S_FIRE 17
#define S_TRAIN 20
#define S_CULT 24
#define S_BIGEYE 28
#define NSPR 31

#define BS_NONE 0
#define BS_PLAY 1
#define BS_PLUNGER 2
#define BS_SUBWAY 3

/* ------------------------------------------------------------------ state */
int ballx[MAXB], bally[MAXB], ballvx[MAXB], ballvy[MAXB];
unsigned char bst[MAXB];
int stuckx[MAXB], stucky[MAXB];
__zp int qx, qy, qvx, qvy;
unsigned char cur;
unsigned char dbg_c, dbg_n;

unsigned char lstep, rstep, lmove, rmove, lbtn, rbtn;
unsigned int frame;
int cam, shake;
unsigned char j1, jt;

unsigned char score[8], hiscore[8];
unsigned char score_dirty, mult, ball_no, balls_left, extra_balls;
unsigned char msg_t;
unsigned int save_t;
unsigned char launched, plunge_pow, kick_lit, nudge_cool;

/* objects */
int taxi_x; signed char taxi_dir; unsigned char taxi_wreck;
int tank_x; signed char tank_dir; unsigned char tank_cool;
int shell_x, shell_y; unsigned char shell_on;
int expl_x, expl_y; unsigned char expl_t;
unsigned char ten_hp[4], ten_cool[4], ten_flash[4];
unsigned int ten_regrow[4];
unsigned char tgt_up[3], tgt_reset;
unsigned char emp_lvl, emp_cool;
unsigned char bump_flash[3];
unsigned char sub_t, sub_cool;
unsigned char boss_cool, boss_stage, boss_dmg, boss_eyes, boss_awake, boss_hp;
unsigned int stomp_t;
unsigned char multiball;

/* bonus rooms: 0 = main table, 1 = Subway Tunnel, 2 = Rooftop Showdown, 3 = Sunken Shrine */
unsigned char room, pending_room, exit_req, room_done_t, sub_lit;
unsigned int room_t;
int fl_lx, fl_rx, fl_py, flip_zone;
int fire_x[3], fire_y[3], fire_vx[3];
unsigned char fire_on[3];
unsigned int fire_t;
int train_x; unsigned char train_on, train_cool; unsigned int train_wait;
unsigned char sw_lit[3], sw_count;
unsigned char reye_hp[3], reye_flash[3], reye_cool[3];
unsigned char altar_hp, sever_count;
int cult_x[4]; signed char cult_dir[4]; unsigned char cult_gone[4];
const int CULT_Y[] = { 56, 56, 112, 112 };
const int REYE_X[] = { REYE0_X, REYE1_X, REYE2_X };
const int REYE_Y[] = { REYE0_Y, REYE1_Y, REYE2_Y };

/* sound */
unsigned char sfx_t[6], sfx_v[6], sfx_dv[6];
int sfx_f[6], sfx_df[6];
unsigned char mus_step, mus_t, mus_on;

const int TEN_X[] = { 96, 109, 123, 136 };
const int EYE_X[] = { 116, 100, 132 };
const int EYE_Y[] = { 47, 54, 54 };
const unsigned int BASS[] = { 1357, 1357, 1141, 1357, 960, 1017, 1141, 1209,
                              1357, 1357, 1141, 1357, 1524, 1357, 1209, 1141 };


/* PSG register writes: one macro per register so the value expression can't
   clobber an address pointer (poke() uses __si, which isn't IRQ/expression safe) */
extern void __fastcall __macro psg_ch( unsigned char v<acc> );
extern void __fastcall __macro psg_main( unsigned char v<acc> );
extern void __fastcall __macro psg_flo( unsigned char v<acc> );
extern void __fastcall __macro psg_fhi( unsigned char v<acc> );
extern void __fastcall __macro psg_ctl( unsigned char v<acc> );
extern void __fastcall __macro psg_bal( unsigned char v<acc> );
extern void __fastcall __macro psg_wav( unsigned char v<acc> );
extern void __fastcall __macro psg_noise( unsigned char v<acc> );
#asm
_psg_ch.1	.macro
		sta	$0800
		.endm
_psg_main.1	.macro
		sta	$0801
		.endm
_psg_flo.1	.macro
		sta	$0802
		.endm
_psg_fhi.1	.macro
		sta	$0803
		.endm
_psg_ctl.1	.macro
		sta	$0804
		.endm
_psg_bal.1	.macro
		sta	$0805
		.endm
_psg_wav.1	.macro
		sta	$0806
		.endm
_psg_noise.1	.macro
		sta	$0807
		.endm
#endasm

#define ABS(a) ((a) < 0 ? -(a) : (a))

/* ------------------------------------------------------------------ sound */
const unsigned char WAVE_SQ[] = { 31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,
                                  0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0 };
const unsigned char WAVE_SAW[] = { 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31 };
const unsigned char WAVE_TRI[] = { 0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,31,29,27,25,23,21,19,17,15,13,11,9,7,5,3,1 };

void psg_wave(unsigned char ch, unsigned char *w)
{
	unsigned char i;
	psg_ch(ch);
	psg_ctl(0x40);
	psg_ctl(0x00);
	for (i = 0; i < 32; i++) psg_wav(w[i]);
	psg_bal(0xFF);
}

void psg_init(void)
{
	psg_main(0xFF);
	psg_wave(0, WAVE_SQ);
	psg_wave(1, WAVE_SQ);
	psg_wave(2, WAVE_SAW);
	psg_wave(3, WAVE_TRI);
	psg_wave(4, WAVE_SQ);
	psg_wave(5, WAVE_SAW);
}

/* noise channels: 4 and 5. f is noise freq (0-31) for those */
void sfx(unsigned char ch, int f, int df, unsigned char v, unsigned char dv, unsigned char t)
{
	sfx_f[ch] = f; sfx_df[ch] = df; sfx_v[ch] = v; sfx_dv[ch] = dv; sfx_t[ch] = t;
}

void sound_update(void)
{
	unsigned char ch;
	for (ch = 0; ch < 6; ch++) {
		if (ch == 3) continue;
		psg_ch(ch);
		if (sfx_t[ch]) {
			sfx_t[ch]--;
			if (ch >= 4) {
				psg_noise(0x80 | (sfx_f[ch] & 31));
			} else {
				psg_flo(sfx_f[ch] & 255);
				psg_fhi((sfx_f[ch] >> 8) & 15);
			}
			psg_ctl(0x80 | sfx_v[ch]);
			sfx_f[ch] += sfx_df[ch];
			if (sfx_v[ch] > sfx_dv[ch]) sfx_v[ch] -= sfx_dv[ch]; else sfx_v[ch] = 0;
		} else {
			psg_ctl(0);
			if (ch >= 4) psg_noise(0);
		}
	}
	/* music: menacing bass ostinato on channel 3 */
	psg_ch(3);
	if (!mus_on) { psg_ctl(0); return; }
	if (mus_t == 0) {
		mus_t = boss_awake ? 9 : 13;
		psg_flo(BASS[mus_step] & 255);
		psg_fhi(BASS[mus_step] >> 8);
		mus_step = (mus_step + 1) & 15;
	}
	mus_t--;
	psg_ctl(0x80 | (mus_t > 6 ? 18 : 10));
}

void snd_flipper(void) { sfx(4, 28, -4, 20, 6, 3); }
void snd_bumper(void) { sfx(1, 120, 14, 28, 2, 12); }
void snd_sling(void) { sfx(1, 160, 20, 26, 3, 8); }
void snd_hit(void) { sfx(0, 200, -6, 24, 2, 10); }
void snd_growl(void) { sfx(2, 1800, 40, 31, 1, 30); sfx(5, 6, 0, 24, 1, 24); }
void snd_roar(void) { sfx(2, 1500, 25, 31, 0, 70); sfx(5, 4, 0, 31, 0, 60); }
void snd_boom(void) { sfx(5, 2, 1, 31, 1, 30); }
void snd_drain(void) { sfx(0, 300, 30, 28, 0, 50); }
void snd_launch(void) { sfx(4, 2, 1, 28, 1, 20); }
void snd_bonus(void) { sfx(0, 400, -12, 28, 0, 30); sfx(1, 300, -9, 20, 0, 30); }

/* ------------------------------------------------------------------ BAT helpers */
void put_text(unsigned char col, unsigned char row, char *s, unsigned char pal)
{
	unsigned int a;
	unsigned char c;
	a = (row << 6) + col;
	while ((c = *s++)) {
		put_vram(a++, FONT[c - 32] | (pal << 12));
	}
}

void put_block(unsigned char c0, unsigned char r0, unsigned char w, unsigned char h, unsigned int *data)
{
	unsigned char x, y;
	unsigned int a;
	for (y = 0; y < h; y++) {
		a = ((r0 + y) << 6) + c0;
		for (x = 0; x < w; x++) put_vram(a++, *data++);
	}
}

char msgbuf[33];
char msgline[33];

void show_msg(char *s, unsigned char t)
{
	unsigned char n, i, o;
	n = 0;
	while (s[n]) n++;
	o = (32 - n) >> 1;
	if (n > 32) n = 32;
	o = (32 - n) >> 1;
	for (i = 0; i < 32; i++) msgline[i] = ' ';
	for (i = 0; i < n; i++) msgline[o + i] = s[i];
	msgline[32] = 0;
	put_text(32, 1, msgline, 13);
	msg_t = t;
}

void default_msg(void)
{
	if (boss_awake) show_msg("AWAKE! EMPIRE STATE TO ROOFTOP", 0);
	else if (boss_eyes == 0) show_msg("THE DROWNED KING RISES", 0);
	else if (boss_eyes == 1) show_msg("ONE EYE OPEN - KEEP HITTING", 0);
	else show_msg("EMPIRE STATE: ROOFTOP IS OPEN", 0);
}

/* ------------------------------------------------------------------ score */
void add_digits(unsigned int p, signed char pos)
{
	unsigned char c, s, dg;
	c = 0;
	while (pos >= 0) {
		dg = p % 10;
		p = p / 10;
		s = score[pos] + dg + c;
		if (s >= 10) { s -= 10; c = 1; } else c = 0;
		score[pos] = s;
		if (p == 0 && c == 0) break;
		pos--;
	}
	score_dirty = 1;
}

void add_score(unsigned int p)
{
	unsigned char i;
	for (i = 0; i < mult; i++) add_digits(p, 7);
}

void add_k(unsigned int k)  /* thousands */
{
	unsigned char i;
	for (i = 0; i < mult; i++) add_digits(k, 4);
}

void draw_hud(void)
{
	unsigned char i;
	unsigned int a;
	a = 32 + 6;
	for (i = 0; i < 8; i++) put_vram(a + i, FONT['0' - 32 + score[i]] | (15 << 12));
	put_vram(32 + 21, FONT['0' - 32 + ball_no] | (14 << 12));
	put_vram(32 + 30, FONT['0' - 32 + mult] | (15 << 12));
	score_dirty = 0;
}

void hud_frame(void)
{
	put_text(32, 0, "SCORE 00000000  BALL 1  MULT x1 ", 14);
	draw_hud();
}

/* ------------------------------------------------------------------ collision */
unsigned char grid_at(int x, int y)
{
	unsigned int off;
	if (x < 0 || y < 0 || x >= 8192) return 0x38;
	off = (unsigned int)(y >> 6);
	off = (off << 7) + (x >> 6);
	if (room == 0) {
		if (y >= 16384) return 0x38;
		set_far_offset(off, BANK(coll), coll);
	} else {
		if (y >= 6656) return 0;
		if (room == 1) set_far_offset(off, BANK(r1coll), r1coll);
		else if (room == 2) set_far_offset(off, BANK(r2coll), r2coll);
		else set_far_offset(off, BANK(r3coll), r3coll);
	}
	return far_peek();
}

void clamp_v(void)
{
	if (qvx > VMAX) qvx = VMAX;
	if (qvx < -VMAX) qvx = -VMAX;
	if (qvy > VMAX) qvy = VMAX;
	if (qvy < -VMAX) qvy = -VMAX;
}

void bumper_hit(void)
{
	unsigned char i, b;
	int px, py, d, best;
	if (room) { add_score(100); snd_bumper(); return; }
	px = qx >> 5; py = qy >> 5;
	best = 999; b = 0;
	for (i = 0; i < 3; i++) {
		if (i == 0) d = ABS(px - BUMP0_X) + ABS(py - BUMP0_Y);
		else if (i == 1) d = ABS(px - BUMP1_X) + ABS(py - BUMP1_Y);
		else d = ABS(px - BUMP2_X) + ABS(py - BUMP2_Y);
		if (d < best) { best = d; b = i; }
	}
	if (bump_flash[b] == 0)
		put_block(VAR_BUMP_POS[b * 4], VAR_BUMP_POS[b * 4 + 1], VAR_BUMP_POS[b * 4 + 2], VAR_BUMP_POS[b * 4 + 3], VAR_BUMP_ON + b * 16);
	bump_flash[b] = 8;
	add_score(100);
	snd_bumper();
}

void boss_damage(unsigned char n);
void empire_hit(void);
void room_boss_hit(void);
void room_target_hit(void);

void boss_face_hit(void)
{
	boss_cool = 12;
	shake = 6;
	add_score(2500);
	snd_growl();
	boss_damage(multiball ? 2 : 1);
}

void collide(unsigned char m, unsigned char k, int d)
{
	int dd;
	if (m == MAT_BUMP) {
		dd = d + d;
		qvx -= (NX[k] * dd) >> 6; qvy -= (NY[k] * dd) >> 6;
		qvx += (NX[k] * 5) >> 3; qvy += (NY[k] * 5) >> 3;
		bumper_hit();
	} else if (m == MAT_SLING) {
		dd = d + d;
		qvx -= (NX[k] * dd) >> 6; qvy -= (NY[k] * dd) >> 6;
		if (d < -4) {
			qvx += (NX[k] * 3) >> 2; qvy += (NY[k] * 3) >> 2;
			add_score(10);
			snd_sling();
		}
	} else {
		dd = d + (d >> 1);
		qvx -= (NX[k] * dd) >> 6; qvy -= (NY[k] * dd) >> 6;
		if (m == MAT_BOSS && d < -10 && boss_cool == 0) {
			if (room) room_boss_hit(); else boss_face_hit();
		} else if (m == MAT_EMPIRE && d < -8 && emp_cool == 0) {
			if (room) room_target_hit(); else empire_hit();
		}
	}
	clamp_v();
}

void flip_check(unsigned char right)
{
	int rx, ry, t, d, r, u, vn, dx, dy, nx, ny, push;
	unsigned char s;
	if (right) {
		rx = (qx >> 3) - (fl_rx << 2);
		if (rx > 44 || rx < -140) return;
		s = rstep;
		dx = -FDX[s]; nx = -FNX[s];
	} else {
		rx = (qx >> 3) - (fl_lx << 2);
		if (rx < -44 || rx > 140) return;
		s = lstep;
		dx = FDX[s]; nx = FNX[s];
	}
	ry = (qy >> 3) - (fl_py << 2);
	if (ry < -88 || ry > 96) return;
	dy = FDY[s]; ny = FNY[s];
	t = (rx * dx + ry * dy) >> 6;
	if (t > 112) return;
	if (t < 0) t = 0;
	d = (rx * nx + ry * ny) >> 6;
	r = 34 - ((t * 19) >> 8);
	if (d >= r || d <= -r) return;
	if (d > -8) {
		push = r - d;
		qx += (nx * push) >> 3; qy += (ny * push) >> 3;
		u = 0;
		if ((right && rmove) || (!right && lmove)) u = (t * 13) >> 4;
		vn = ((qvx * nx + qvy * ny) >> 6) - u;
		if (vn < 0) {
			vn = vn + (vn >> 2);
			qvx -= (nx * vn) >> 6; qvy -= (ny * vn) >> 6;
		}
	} else {
		push = -r - d;
		qx += (nx * push) >> 3; qy += (ny * push) >> 3;
		vn = (qvx * nx + qvy * ny) >> 6;
		if (vn > 0) {
			qvx -= (nx * vn) >> 6; qvy -= (ny * vn) >> 6;
		}
	}
	clamp_v();
}

void substep(void)
{
	int nx, ny, d;
	unsigned char c, k, n;
	nx = qx + qvx; ny = qy + qvy;
	c = grid_at(nx, ny);
	dbg_c = c; dbg_n++;
	if (c == 0) {
		qx = nx; qy = ny;
	} else {
		k = c & 31;
		d = (qvx * NX[k] + qvy * NY[k]) >> 6;
		if (d < 0) collide(c >> 5, k, d);
		else { qx = nx; qy = ny; }
		for (n = 0; n < 3; n++) {
			c = grid_at(qx, qy);
			if (c == 0) break;
			k = c & 31;
			qx += NX[k] >> 1; qy += NY[k] >> 1;
		}
	}
	if (qy > flip_zone) {
		flip_check(0);
		flip_check(1);
	}
}

/* ------------------------------------------------------------------ game objects */
void spawn_ball(unsigned char i, int x, int y, int vx, int vy, unsigned char st)
{
	ballx[i] = x << 5; bally[i] = y << 5; ballvx[i] = vx; ballvy[i] = vy; bst[i] = st;
}

unsigned char count_balls(void)
{
	unsigned char i, n;
	n = 0;
	for (i = 0; i < MAXB; i++) if (bst[i]) n++;
	return n;
}

void serve_ball(unsigned char allow_save)
{
	spawn_ball(0, 240, 494, 0, 0, BS_PLUNGER);
	bst[1] = 0; bst[2] = 0;
	launched = 0;
	plunge_pow = 0;
	save_t = allow_save ? 0 : 1;
}

void reset_targets(void)
{
	unsigned char i;
	for (i = 0; i < 3; i++) {
		tgt_up[i] = 1;
		put_block(11 + i * 3, 40, 2, 1, VAR_TARGET_OFF + i * 2);
	}
}

void set_torch(unsigned char lit)
{
	kick_lit = lit;
	put_block(4, 55, 2, 2, lit ? VAR_TORCH_ON : VAR_TORCH_OFF);
}

void reset_empire(void)
{
	unsigned char l;
	emp_lvl = 0;
	for (l = 0; l < 5; l++) put_block(26, 34 - l, 2, 1, VAR_EMPIRE_OFF + l * 2);
}

void start_multiball(void)
{
	show_msg("AIRSTRIKE! MULTIBALL!", 150);
	snd_bonus();
	add_k(50);
	multiball = 1;
	if (!bst[1]) spawn_ball(1, 40, 60, 24, 0, BS_PLAY);
	if (!bst[2]) spawn_ball(2, 190, 60, -24, 0, BS_PLAY);
	shake = 10;
}

void empire_hit(void)
{
	emp_cool = 20;
	snd_hit();
	if ((boss_awake || boss_eyes >= 2) && !multiball && !pending_room) {
		add_score(5000);
		pending_room = 2;
		return;
	}
	if (emp_lvl < 5) {
		put_block(26, 34 - emp_lvl, 2, 1, VAR_EMPIRE_ON + emp_lvl * 2);
		emp_lvl++;
		add_score(3000);
		if (emp_lvl == 5 && !multiball) start_multiball();
		else if (emp_lvl < 5) {
			strcpy(msgbuf, "EMPIRE STATE CLIMB 0/5");
			msgbuf[19] = '0' + emp_lvl;
			show_msg(msgbuf, 90);
		}
	} else add_score(1000);
}

void kaiju_colors(void)
{
	unsigned char i;
	int k;
	unsigned int c, c2;
	if (boss_awake) {
		k = SINT[(frame << 1) & 63];
		k = (k + 64) >> 5;                  /* 0..4 */
		c = ((2 + k) << 3) | 1;             /* membrane: r 2-6 */
		c2 = ((3 + (k >> 1) + (k >> 2)) << 3) | (1 << 6) | 2;
		if (c2 > ((7 << 3) | (1 << 6) | 2)) c2 = (7 << 3) | (1 << 6) | 2;
		for (i = 0; i < N_WING_SLOTS; i++) set_color(WING_SLOTS[i], WING_ORIG[i] == WING_ORIG[0] ? c : c2);
		set_color(256 + SP_EYE * 16 + 1, (7 << 3) | (1 << 6) | 1);
		set_color(256 + SP_EYE * 16 + 2, (5 << 3));
	} else {
		for (i = 0; i < N_WING_SLOTS; i++) set_color(WING_SLOTS[i], WING_ORIG[i]);
		set_color(256 + SP_EYE * 16 + 1, (6 << 3) | (7 << 6) | 2);
		set_color(256 + SP_EYE * 16 + 2, (3 << 3) | (5 << 6) | 1);
	}
}

void boss_reset_stage(void)
{
	unsigned char i;
	boss_dmg = 0; boss_eyes = 0; boss_awake = 0;
	for (i = 0; i < 4; i++) { ten_hp[i] = 3; ten_regrow[i] = 0; }
}

void boss_defeat(void)
{
	boss_hp = 0;
	add_k(1000);
	if (boss_stage > 1) add_k(1000);
	show_msg("KAIJU DEFEATED! 1,000,000", 200);
	snd_roar(); snd_boom();
	shake = 40;
	if (!room) { expl_x = 116; expl_y = 64; expl_t = 40; }
	if (boss_stage < 9) boss_stage++;
	if (extra_balls == 0) { extra_balls = 1; balls_left++; }
	boss_reset_stage();
}

void boss_damage(unsigned char n)
{
	unsigned char per;
	per = 2 + boss_stage;
	if (!boss_awake) {
		boss_dmg += n;
		while (boss_dmg >= per && !boss_awake) {
			boss_dmg -= per;
			boss_eyes++;
			snd_roar();
			shake = 20;
			add_k(25);
			if (boss_eyes >= 3) {
				boss_awake = 1;
				boss_hp = 4 + boss_stage;
				stomp_t = 240;
				show_msg("ZHA'GORATH AWAKENS!", 150);
				fire_t = 150;
			} else {
				show_msg("AN EYE OPENS...", 120);
			}
		}
	} else {
		if (boss_hp > n) boss_hp -= n;
		else boss_defeat();
	}
}

void taxi_update(void)
{
	if (taxi_wreck) {
		taxi_wreck--;
		if (taxi_wreck == 0) { taxi_x = taxi_dir > 0 ? 40 : 194; }
		return;
	}
	taxi_x += taxi_dir;
	if (taxi_x > 194) taxi_dir = -1;
	if (taxi_x < 40) taxi_dir = 1;
}

void tank_update(void)
{
	if ((frame & 1) == 0) {
		tank_x += tank_dir;
		if (tank_x > 176) tank_dir = -1;
		if (tank_x < 70) tank_dir = 1;
	}
	if (tank_cool) tank_cool--;
	if (shell_on) {
		shell_y -= 5;
		if (shell_y < 96) {
			shell_on = 0;
			expl_x = shell_x; expl_y = shell_y; expl_t = 20;
			snd_boom();
			if (shell_x > 76 && shell_x < 156) {
				add_score(5000);
				boss_damage(2);
				shake = 8;
			}
		}
	}
}

void tentacle_update(void)
{
	unsigned char i;
	for (i = 0; i < 4; i++) {
		if (ten_cool[i]) ten_cool[i]--;
		if (ten_flash[i]) ten_flash[i]--;
		if (ten_hp[i] == 0) {
			if (ten_regrow[i]) ten_regrow[i]--;
			else ten_hp[i] = 3;
		}
	}
}

int ten_sway(unsigned char i)
{
	unsigned char spd;
	spd = boss_awake ? 2 : 1;
	return SINT[((frame * spd) + i * 19) & 63] >> 4;
}

/* object collisions for current ball (once per frame) */
void ball_objects(void)
{
	int px, py, dx, dy;
	unsigned char i;
	px = qx >> 5; py = qy >> 5;
	/* taxi */
	if (!taxi_wreck && py > 340 && py < 372) {
		dx = px - taxi_x;
		if (dx > -19 && dx < 19) {
			if (py < 356) qvy = -ABS(qvy) - 12; else qvy = ABS(qvy) + 8;
			qvx += dx;
			taxi_wreck = 150;
			add_score(2500);
			if (!sub_lit) { sub_lit = 1; show_msg("TAXI SMASHED! SUBWAY LIT", 90); }
			else show_msg("TAXI SMASHED! +2500", 60);
			snd_boom();
		}
	}
	/* tank */
	if (py > 278 && py < 314) {
		dx = px - tank_x;
		if (dx > -15 && dx < 15) {
			if (py < 290) qvy = -ABS(qvy) - 6; else qvy = ABS(qvy) + 6;
			qvx += dx;
			add_score(500);
			snd_hit();
			if (!tank_cool && !shell_on) {
				shell_on = 1; shell_x = tank_x; shell_y = 272;
				tank_cool = 60;
				show_msg("TANK FIRES!", 60);
				snd_launch();
			}
		}
	}
	/* tentacles */
	if (py > 90 && py < 130) {
		for (i = 0; i < 4; i++) {
			if (ten_hp[i] == 0 || ten_cool[i]) continue;
			dx = ten_sway(i);
			dx += TEN_X[i];
			dx = px - dx;
			if (dx > -7 && dx < 7) {
				qvy = ABS(qvy) + (boss_awake ? 24 : 10);
				qvx += dx * 3;
				ten_cool[i] = 15; ten_flash[i] = 10;
				ten_hp[i]--;
				add_score(1000);
				snd_hit();
				if (ten_hp[i] == 0) {
					ten_regrow[i] = 900;
					add_score(10000);
					show_msg("TENTACLE SEVERED!", 90);
					boss_damage(1);
					snd_growl();
					sever_count++;
					if (sever_count >= 4 && !multiball && !pending_room) {
						sever_count = 0;
						pending_room = 3;
					}
				}
				break;
			}
		}
	}
	/* drop targets */
	if (py > 314 && py < 334) {
		for (i = 0; i < 3; i++) {
			if (!tgt_up[i]) continue;
			dx = px - (TGT0_X + i * 24);
			if (dx > -5 && dx < 20) {
				if (py < 320) { qvy = -(ABS(qvy) >> 1); qy = 315 << 5; }
				else if (py > 327) { qvy = (ABS(qvy) >> 1) + 4; qy = 333 << 5; }
				else qvx = -qvx;
				tgt_up[i] = 0;
				put_block(11 + i * 3, 40, 2, 1, VAR_TARGET_ON + i * 2);
				add_score(1500);
				snd_hit();
				if (!tgt_up[0] && !tgt_up[1] && !tgt_up[2]) {
					if (mult < 5) mult++;
					add_k(25);
					strcpy(msgbuf, "MARKET CRASH! MULT x0");
					msgbuf[20] = '0' + mult;
					show_msg(msgbuf, 120);
					snd_bonus();
					set_torch(1);
					tgt_reset = 90;
				}
				break;
			}
		}
	}
	/* subway */
	if (!sub_cool) {
		dx = px - SUBWAY_X; dy = py - SUBWAY_Y;
		if (dx > -6 && dx < 6 && dy > -6 && dy < 6 && ABS(qvx) + ABS(qvy) < 70 && sub_lit && !multiball && !pending_room) {
			sub_lit = 0;
			pending_room = 1;
			sub_cool = 60;
		} else if (dx > -6 && dx < 6 && dy > -6 && dy < 6 && ABS(qvx) + ABS(qvy) < 70) {
			bst[cur] = BS_SUBWAY;
			sub_t = 80;
			add_score(5000);
			show_msg("SUBWAY EXPRESS! +5000", 90);
			snd_bonus();
		}
	}
	/* Liberty kickback */
	if (px < 20 && py > 446 && py < 480 && qvy > 0) {
		if (kick_lit) {
			qvy = -VMAX; qvx = 4;
			set_torch(0);
			show_msg("LIBERTY SAVES!", 90);
			snd_launch();
			shake = 6;
		}
	}
	/* plunger-lane one way gate */
	if (launched && px > 225 && py > 100 && py < 150 && qvy > 0) {
		qvy = -(qvy >> 1);
		qvx = -ABS(qvx) - 20;
		qx = 224 << 5;
	}
}

/* ------------------------------------------------------------------ sprites */
void spr_place(unsigned char n, int x, int wy, unsigned int pat, unsigned char ctrl, unsigned char pal)
{
	int sy;
	spr_set(n);
	sy = wy - cam + 16;
	if (sy < -64 || sy > 230) { spr_x(-64); spr_y(-64); return; }
	spr_x(x);
	spr_y(sy);
	spr_pattern(pat);
	spr_ctrl(FLIP_MAS | SIZE_MAS, ctrl);
	spr_pal(pal);
	spr_pri(1);
}

void spr_off(unsigned char n)
{
	spr_set(n);
	spr_x(-64);
	spr_y(-64);
}

void draw_table_sprites(void)
{
	unsigned char i, k;
	int ex;
	for (i = 0; i < 3; i++) {
		if (boss_eyes > i || boss_awake) {
			ex = (ballx[0] >> 5) - EYE_X[i];
			k = 1;
			if (ex < -24) k = 0;
			if (ex > 24) k = 2;
			spr_place(S_EYE + i, EYE_X[i] - 8, EYE_Y[i] - 8, SPR_EYE[k], SZ_16x16, SP_EYE);
		} else spr_off(S_EYE + i);
	}
	for (i = 0; i < 4; i++) {
		ex = ten_sway(i);
		ex += TEN_X[i] - 8;
		if (ten_hp[i])
			spr_place(S_TENT + i, ex, 92, SPR_TENT[((frame >> 4) + i) % 3], SZ_16x32,
			          ten_flash[i] ? SP_TENTHIT : SP_TENT);
		else
			spr_place(S_TENT + i, TEN_X[i] - 8, 90, SPR_TENT[3], SZ_16x32, SP_TENT);
	}
	if (taxi_wreck)
		spr_place(S_TAXI, taxi_x - 16, 348, SPR_WRECK, SZ_32x16, SP_TAXI);
	else
		spr_place(S_TAXI, taxi_x - 16, 348, SPR_TAXI, taxi_dir > 0 ? SZ_32x16 : (SZ_32x16 | FLIP_X), SP_TAXI);
	spr_place(S_TANK, tank_x - 16, 280, SPR_TANK, SZ_32x32, SP_TANK);
	if (shell_on) spr_place(S_SHELL, shell_x - 8, shell_y - 8, SPR_SHELL, SZ_16x16, SP_FX);
	else spr_off(S_SHELL);
	if (bst[0] == BS_PLUNGER)
		spr_place(S_PLUNGER, 232, 498 + (plunge_pow >> 3), SPR_PLUNGER, SZ_16x16, SP_BALL);
	else
		spr_place(S_PLUNGER, 232, 498, SPR_PLUNGER, SZ_16x16, SP_BALL);
	for (i = S_TRAIN; i < NSPR; i++) spr_off(i);
}

void draw_room_sprites(void)
{
	unsigned char i, k;
	int ex;
	for (i = S_EYE; i < S_EXPL; i++) spr_off(i);
	spr_off(S_PLUNGER);
	for (i = S_TRAIN; i < NSPR; i++) spr_off(i);
	if (room == 1) {
		for (i = 0; i < 4; i++) {
			if (!train_on) break;
			ex = i << 5;
			ex = train_x - ex;
			spr_place(S_TRAIN + i, ex, 84, SPR_TRAIN[i ? 1 : 0], SZ_32x16, SP_TRAIN);
		}
	} else if (room == 2) {
		for (i = 0; i < 2; i++) {
			ex = ten_sway(i);
			ex += (i ? 156 : 100) - 8;
			spr_place(S_TENT + i, ex, 72, SPR_TENT[((frame >> 3) + i) % 3], SZ_16x32,
			          ten_flash[i] ? SP_TENTHIT : SP_TENT);
		}
		for (i = 0; i < 3; i++) {
			k = 0;
			if (reye_flash[i]) k = 1;
			if (reye_hp[i] == 0) k = 2;
			spr_place(S_BIGEYE + i, REYE_X[i] - 16, REYE_Y[i] - 16, SPR_BIGEYE[k], SZ_32x32, SP_BIGEYE);
		}
	} else {
		for (i = 0; i < 4; i++) {
			if (cult_gone[i]) continue;
			spr_place(S_CULT + i, cult_x[i], CULT_Y[i], SPR_CULT[(frame >> 4) & 1], SZ_16x32 | (cult_dir[i] < 0 ? FLIP_X : 0), SP_CULT);
		}
	}
}

void draw_sprites(void)
{
	unsigned char i;
	for (i = 0; i < MAXB; i++) {
		if (bst[i] == BS_PLAY || bst[i] == BS_PLUNGER)
			spr_place(S_BALL + i, (ballx[i] >> 5) - 8, (bally[i] >> 5) - 8, SPR_BALL, SZ_16x16, SP_BALL);
		else spr_off(S_BALL + i);
	}
	spr_place(S_LFLIP, fl_lx - 5, fl_py - 16, SPR_FLIP[lstep], SZ_32x32, SP_FLIP);
	spr_place(S_RFLIP, fl_rx - 26, fl_py - 16, SPR_FLIP[rstep], SZ_32x32 | FLIP_X, SP_FLIP);
	for (i = 0; i < 3; i++) {
		if (fire_on[i]) spr_place(S_FIRE + i, (fire_x[i] >> 3) - 8, (fire_y[i] >> 3) - 8, SPR_FIRE[((frame >> 2) + i) & 1], SZ_16x16, SP_FX);
		else spr_off(S_FIRE + i);
	}
	if (expl_t) spr_place(S_EXPL, expl_x - 16, expl_y - 16, SPR_EXPL[(expl_t >> 2) & 1], SZ_32x32, SP_FX);
	else spr_off(S_EXPL);
	if (room) draw_room_sprites(); else draw_table_sprites();
}

void hide_all_sprites(void)
{
	unsigned char i;
	for (i = 0; i < NSPR; i++) spr_off(i);
	satb_update();
}

/* ------------------------------------------------------------------ camera */
void update_camera(void)
{
	int target, my;
	unsigned char i;
	my = -1;
	for (i = 0; i < MAXB; i++)
		if ((bst[i] == BS_PLAY || bst[i] == BS_PLUNGER) && (bally[i] >> 5) > my) my = bally[i] >> 5;
	if (my < 0) my = 400;
	target = my - 120;
	if (target < 0) target = 0;
	if (target > CAM_MAX) target = CAM_MAX;
	if (target > cam) cam += ((target - cam) >> 2) + 1;
	else if (target < cam) cam -= ((cam - target) >> 2) + 1;
	if (cam < 0) cam = 0;
	if (cam > CAM_MAX) cam = CAM_MAX;
}

void set_scroll(void)
{
	int sy;
	sy = cam;
	if (shake) {
		shake--;
		sy += (shake & 2) ? 2 : -2;
		if (sy < 0) sy = 0;
	}
	scroll_split(0, 0, 256, 0, BKG_ON);
	if (room) scroll_split(1, 16, 256, sy + 256, BKG_ON | SPR_ON);
	else scroll_split(1, 16, 0, sy, BKG_ON | SPR_ON);
}

/* ------------------------------------------------------------------ setup */
unsigned int bat_off;

void load_far_vram(unsigned int vram, unsigned int words, unsigned char which)
{
	unsigned int off, n;
	off = 0;
	while (words) {
		n = words > 4096 ? 4096 : words;
		if (which == 0) set_far_offset(off, BANK(bgchr_bin), bgchr_bin);
		else if (which == 1) set_far_offset(off, BANK(bgbat_bin), bgbat_bin);
		else if (which == 2) set_far_offset(off, BANK(sprchr_bin), sprchr_bin);
		else if (which == 3) set_far_offset(off, BANK(r1chr_bin), r1chr_bin);
		else if (which == 4) set_far_offset(off, BANK(r2chr_bin), r2chr_bin);
		else if (which == 5) set_far_offset(off, BANK(r3chr_bin), r3chr_bin);
		else if (which == 6) set_far_offset(off + bat_off, BANK(r1bat_bin), r1bat_bin);
		else if (which == 7) set_far_offset(off + bat_off, BANK(r2bat_bin), r2bat_bin);
		else set_far_offset(off + bat_off, BANK(r3bat_bin), r3bat_bin);
		far_load_vram(vram, n);
		vram += n; off += n << 1; words -= n;
	}
}

void load_graphics(void)
{
	disp_off();
	set_screen_size(SCR_SIZE_64x64);
	load_far_vram(0x0000, 4096, 1);
	load_far_vram(VRAM_CHR, BG_CHR_WORDS, 0);
	load_far_vram(0x5800, SPR_WORDS, 2);
	load_palette(0, bgpal_bin, 16);
	load_palette(16, sprpal_bin, SPR_NPAL);
	init_satb();
	hide_all_sprites();
	disp_on();
}

/* ------------------------------------------------------------------ fire breath */
void spawn_fire(int x, int y)
{
	unsigned char i;
	for (i = 0; i < 3; i++) {
		fire_x[i] = x << 3; fire_y[i] = y << 3;
		fire_vx[i] = (i << 3) - 8;
		fire_on[i] = 1;
	}
	sfx(5, 3, 0, 30, 0, 40);
	sfx(2, 700, -6, 28, 0, 40);
}

void fire_update(void)
{
	unsigned char i;
	int lim;
	lim = room ? 1680 : 4096;
	for (i = 0; i < 3; i++) {
		if (!fire_on[i]) continue;
		fire_y[i] += 24; fire_x[i] += fire_vx[i];
		if (fire_y[i] > lim || fire_x[i] < 0 || fire_x[i] > 2040) fire_on[i] = 0;
	}
}

void fire_clear(void)
{
	fire_on[0] = 0; fire_on[1] = 0; fire_on[2] = 0;
}

/* current ball vs fireballs */
void fire_ball(void)
{
	unsigned char i;
	int px, py, dx, dy;
	px = qx >> 5; py = qy >> 5;
	for (i = 0; i < 3; i++) {
		if (!fire_on[i]) continue;
		dx = fire_x[i] >> 3; dx = px - dx;
		dy = fire_y[i] >> 3; dy = py - dy;
		if (dx > -9 && dx < 9 && dy > -9 && dy < 9) {
			qvy = ABS(qvy) + 24;
			qvx += fire_vx[i] + dx + dx;
			fire_on[i] = 0;
			show_msg("SCORCHED!", 40);
			snd_hit();
			shake = 6;
		}
	}
}

/* ------------------------------------------------------------------ bonus rooms */
void room_msg(void)
{
	unsigned char t;
	t = room_t / 60;
	if (room == 1) strcpy(msgbuf, "DERAIL THE TRAIN!  TIME 00");
	else if (room == 2) strcpy(msgbuf, "SHOOT HIS EYES!  TIME 00");
	else strcpy(msgbuf, "SMASH THE ALTAR!  TIME 00");
	if (room == 2) { msgbuf[22] = '0' + t / 10; msgbuf[23] = '0' + t % 10; }
	else if (room == 1) { msgbuf[24] = '0' + t / 10; msgbuf[25] = '0' + t % 10; }
	else { msgbuf[23] = '0' + t / 10; msgbuf[24] = '0' + t % 10; }
	show_msg(msgbuf, 0);
}

void room_target_hit(void)
{
	unsigned char i, px;
	emp_cool = 12;
	px = qx >> 5;
	i = 0;
	if (px > 96) i = 1;
	if (px > 160) i = 2;
	snd_hit();
	if (sw_lit[i] || room_done_t) { add_score(500); return; }
	sw_lit[i] = 1;
	sw_count++;
	put_block(32 + 7 + (i << 3), 33, 2, 1, ROOM1_VAR + (i << 1));
	add_score(25000);
	if (sw_count >= 3) {
		add_k(250);
		show_msg("TRAIN DERAILED! +250,000", 150);
		snd_bonus(); snd_boom();
		if (train_on) { expl_x = train_x + 16; expl_y = 92; expl_t = 40; }
		train_on = 0; train_wait = 9999;
		shake = 20;
		room_done_t = 150;
	} else show_msg("SWITCH THROWN! +25,000", 60);
}

void room_boss_hit(void)
{
	boss_cool = 12;
	shake = 6;
	if (room == 2) {
		add_score(500);
		snd_growl();
	} else if (room == 3) {
		if (!altar_hp) return;
		altar_hp--;
		add_score(10000);
		snd_boom();
		if (altar_hp == 3) put_block(32 + 12, 34, 8, 5, ROOM3_VAR);
		if (altar_hp == 0) {
			put_block(32 + 12, 34, 8, 5, ROOM3_VAR + 40);
			expl_x = 128; expl_y = 36; expl_t = 40;
			boss_damage(2 + boss_stage);
			add_k(500);
			show_msg("SHRINE DESTROYED! +500,000", 150);
			snd_bonus();
			shake = 24;
			room_done_t = 150;
		} else show_msg("THE ALTAR CRACKS!", 40);
	}
}

/* current ball vs room objects (once per frame) */
void room_objects(void)
{
	int px, py, dx, dy;
	unsigned char i;
	px = qx >> 5; py = qy >> 5;
	if (room == 1) {
		if (train_on && !train_cool && py > 78 && py < 106) {
			dx = px - train_x;
			if (dx > -100 && dx < 36) {
				qvx = 64; qvy = -24;
				train_cool = 20;
				add_score(1000);
				show_msg("CLANG!", 30);
				snd_hit(); shake = 8;
			}
		}
	} else if (room == 2) {
		for (i = 0; i < 3; i++) {
			if (reye_hp[i] == 0 || reye_cool[i]) continue;
			dx = px - REYE_X[i]; dy = py - REYE_Y[i];
			if (dx > -17 && dx < 17 && dy > -15 && dy < 15) {
				qvy = ABS(qvy) + 16; qvx += dx + dx;
				reye_cool[i] = 15; reye_flash[i] = 12;
				reye_hp[i]--;
				add_score(10000);
				snd_growl();
				shake = 8;
				if (reye_hp[i] == 0) {
					add_k(50);
					expl_x = REYE_X[i]; expl_y = REYE_Y[i]; expl_t = 24;
					if (!reye_hp[0] && !reye_hp[1] && !reye_hp[2] && !room_done_t) {
						boss_defeat();
						show_msg("SLAIN ON THE ROOFTOP!", 150);
						room_done_t = 150;
					} else show_msg("EYE DESTROYED! +50,000", 60);
				}
				break;
			}
		}
		if (py > 74 && py < 110) {
			for (i = 0; i < 2; i++) {
				if (ten_cool[i]) continue;
				dx = ten_sway(i);
				dx += i ? 156 : 100;
				dx = px - dx;
				if (dx > -7 && dx < 7) {
					qvy = ABS(qvy) + 14; qvx += dx * 3;
					ten_cool[i] = 15; ten_flash[i] = 10;
					add_score(500);
					snd_hit();
				}
			}
		}
		fire_ball();
	} else {
		for (i = 0; i < 4; i++) {
			if (cult_gone[i]) continue;
			dx = px - cult_x[i] - 8;
			dy = py - CULT_Y[i] - 16;
			if (dx > -10 && dx < 10 && dy > -18 && dy < 18) {
				qvy = -qvy; qvx += dx + dx;
				cult_gone[i] = 180;
				add_score(2500);
				show_msg("CULTIST BANISHED! +2500", 50);
				snd_bumper();
			}
		}
	}
}

void room_update(void)
{
	unsigned char i;
	if (room_t) {
		room_t--;
		if (room_t == 0 && !room_done_t) {
			show_msg("TIME UP!", 60);
			room_done_t = 60;
		}
	}
	if (room_done_t) { if (--room_done_t == 0) exit_req = 1; }
	if (msg_t == 0 && (frame & 31) == 0) room_msg();
	if (room == 1) {
		if (train_cool) train_cool--;
		if (train_on) {
			train_x += 4;
			if (train_x > 384) { train_on = 0; train_wait = 150; }
		} else if (train_wait < 9999) {
			train_wait--;
			if (train_wait == 40) { show_msg("TRAIN COMING!", 40); sfx(0, 500, 0, 28, 0, 30); sfx(1, 400, 0, 24, 0, 30); }
			if (train_wait == 0) { train_on = 1; train_x = -32; }
		}
	} else if (room == 2) {
		for (i = 0; i < 3; i++) { if (reye_cool[i]) reye_cool[i]--; if (reye_flash[i]) reye_flash[i]--; }
		for (i = 0; i < 2; i++) { if (ten_cool[i]) ten_cool[i]--; if (ten_flash[i]) ten_flash[i]--; }
		if (--fire_t == 0) { fire_t = 170 - boss_stage * 10; spawn_fire(128, 100); show_msg("FIRE BREATH!", 40); }
		fire_update();
	} else {
		for (i = 0; i < 4; i++) {
			if (cult_gone[i]) {
				if (--cult_gone[i] == 0) { cult_x[i] = cult_dir[i] > 0 ? 16 : 224; }
				continue;
			}
			if (frame & 1) {
				cult_x[i] += cult_dir[i];
				if (cult_x[i] > 224) cult_dir[i] = -1;
				if (cult_x[i] < 16) cult_dir[i] = 1;
			}
		}
		if ((frame & 63) == 0) sfx(5, 20, 0, 10, 0, 50);
	}
}

void load_room_screen(unsigned char r)
{
	unsigned char row;
	if (r == 1) load_far_vram(VRAM_CHR + FONT_TILES * 16, ROOM1_CHR_WORDS, 3);
	else if (r == 2) load_far_vram(VRAM_CHR + FONT_TILES * 16, ROOM2_CHR_WORDS, 4);
	else load_far_vram(VRAM_CHR + FONT_TILES * 16, ROOM3_CHR_WORDS, 5);
	for (row = 0; row < 26; row++) {
		bat_off = row << 6;
		load_far_vram(((32 + row) << 6) + 32, 32, 5 + r);
	}
	bat_off = 0;
	if (r == 1) load_palette(0, r1pal_bin, 13);
	else if (r == 2) load_palette(0, r2pal_bin, 13);
	else load_palette(0, r3pal_bin, 13);
}

void enter_room(unsigned char r)
{
	unsigned char i;
	pending_room = 0;
	fire_clear();
	hide_all_sprites();
	disp_off();
	room = r;
	load_room_screen(r);
	cam = 0; shake = 0;
	fl_lx = RLPX; fl_rx = RRPX; fl_py = RLPY; flip_zone = (RLPY - 25) << 5;
	room_t = 45 * 60; room_done_t = 0; exit_req = 0;
	for (i = 0; i < MAXB; i++) bst[i] = BS_NONE;
	expl_t = 0;
	if (r == 1) {
		for (i = 0; i < 3; i++) sw_lit[i] = 0;
		sw_count = 0; train_on = 0; train_wait = 120; train_cool = 0;
		spawn_ball(0, 30, 60, 40, 0, BS_PLAY);
		show_msg("SUBWAY TUNNEL!", 120);
	} else if (r == 2) {
		for (i = 0; i < 3; i++) { reye_hp[i] = 2 + boss_stage; reye_flash[i] = 0; reye_cool[i] = 0; }
		ten_cool[0] = 0; ten_cool[1] = 0;
		fire_t = 120;
		spawn_ball(0, 128, 170, 4, -66, BS_PLAY);
		show_msg("ROOFTOP SHOWDOWN!", 120);
	} else {
		altar_hp = 6;
		for (i = 0; i < 4; i++) { cult_x[i] = 30 + i * 50; cult_dir[i] = (i & 1) ? -1 : 1; cult_gone[i] = 0; }
		spawn_ball(0, 128, 150, 6, -60, BS_PLAY);
		show_msg("THE SUNKEN SHRINE!", 120);
	}
	snd_roar();
	disp_on();
}

void exit_room(void)
{
	unsigned char r, i;
	r = room;
	fire_clear();
	hide_all_sprites();
	disp_off();
	room = 0;
	load_far_vram(VRAM_CHR, BG_CHR_WORDS, 0);
	load_palette(0, bgpal_bin, 16);
	fl_lx = LPX; fl_rx = RPX; fl_py = LPY; flip_zone = 13600;
	for (i = 0; i < MAXB; i++) bst[i] = BS_NONE;
	for (i = 0; i < 4; i++) { ten_cool[i] = 0; ten_flash[i] = 0; }
	expl_t = 0; exit_req = 0;
	if (r == 1) { spawn_ball(0, SUBWAY_X + 4, SUBWAY_Y - 8, 36, -28, BS_PLAY); sub_cool = 60; }
	else if (r == 2) spawn_ball(0, 190, 232, -36, -12, BS_PLAY);
	else spawn_ball(0, 116, 132, 0, 24, BS_PLAY);
	stuckx[0] = 0; stucky[0] = 0;
	cam = (bally[0] >> 5) - 120;
	if (cam < 0) cam = 0;
	if (cam > CAM_MAX) cam = CAM_MAX;
	kaiju_colors();
	default_msg();
	disp_on();
}

/* ------------------------------------------------------------------ title */
void title_screen(void)
{
	unsigned int t;
	hide_all_sprites();
	mus_on = 1;
	put_text(32, 29, "       A XENOCIDE21 GAME        ", 14);
	put_text(32, 30, " CODE AND ART BUILT WITH CLAUDE ", 14);
	put_text(32, 31, "   HI 00000000                  ", 15);
	for (t = 0; t < 8; t++) put_vram((31 << 6) + 32 + 6 + t, FONT['0' - 32 + hiscore[t]] | (15 << 12));
	t = 0;
	for (;;) {
		scroll_split(0, 0, 256, 32, BKG_ON);
		disable_split(1);
		if ((t & 31) == 0) put_text(32, 27, "            PRESS RUN           ", 15);
		if ((t & 31) == 20) put_text(32, 27, "                                ", 15);
		sound_update();
		vsync();
		t++;
		if (joytrg(0) & JOY_RUN) break;
	}
	snd_bonus();
}

/* ------------------------------------------------------------------ main game */
void game_frame(void)
{
	unsigned char s, i, bl, br;
	j1 = joy(0); jt = joytrg(0);
	frame++;
	bl = (j1 & (JOY_LEFT | JOY_UP | JOY_DOWN | JOY_RIGHT)) ? 1 : 0;
	br = (j1 & (JOY_I | JOY_II)) ? 1 : 0;
	if (bst[0] == BS_PLUNGER) br = 0;
	if (bl && !lbtn) snd_flipper();
	if (br && !rbtn) snd_flipper();
	lbtn = bl; rbtn = br;

	/* plunger */
	if (bst[0] == BS_PLUNGER) {
		if (j1 & (JOY_I | JOY_II | JOY_DOWN)) {
			if (plunge_pow < 48) plunge_pow++;
		} else if (plunge_pow) {
			bst[0] = BS_PLAY;
			ballvy[0] = -(24 + plunge_pow);
			plunge_pow = 0;
			snd_launch();
			if (save_t == 0) save_t = 600;
		}
	}
	/* nudge */
	if (nudge_cool) nudge_cool--;
	if ((jt & JOY_SEL) && !nudge_cool) {
		nudge_cool = 45;
		shake = 6;
		for (i = 0; i < MAXB; i++) if (bst[i] == BS_PLAY) { ballvy[i] -= 14; ballvx[i] += (frame & 1) ? 12 : -12; }
	}

	/* physics: gravity per frame, 4 substeps */
	for (i = 0; i < MAXB; i++) {
		if (bst[i] != BS_PLAY) continue;
		qx = ballx[i]; qy = bally[i]; qvx = ballvx[i]; qvy = ballvy[i];
		if ((room || !(qx > 7232 && qy > 4480 && qvy < 0)) && (frame & 3)) qvy++;
		if (qvy > VMAX) qvy = VMAX;
		ballx[i] = qx; ballvy[i] = qvy;
	}
	for (s = 0; s < 4; s++) {
		lmove = 0; rmove = 0;
		if (lbtn) { if (lstep < 7) { lstep++; lmove = 1; } } else if (lstep) lstep--;
		if (rbtn) { if (rstep < 7) { rstep++; rmove = 1; } } else if (rstep) rstep--;
		for (i = 0; i < MAXB; i++) {
			if (bst[i] != BS_PLAY) continue;
			qx = ballx[i]; qy = bally[i]; qvx = ballvx[i]; qvy = ballvy[i];
			substep();
			ballx[i] = qx; bally[i] = qy; ballvx[i] = qvx; ballvy[i] = qvy;
		}
	}
	for (i = 0; i < MAXB; i++) {
		if (bst[i] == BS_SUBWAY) {
			if (--sub_t == 0) {
				spawn_ball(i, SUBWAY_X + 4, SUBWAY_Y - 8, 36, -28, BS_PLAY);
				sub_cool = 60;
				snd_launch();
			}
			continue;
		}
		if (bst[i] != BS_PLAY) continue;
		cur = i;
		qx = ballx[i]; qy = bally[i]; qvx = ballvx[i]; qvy = ballvy[i];
		if (room) {
			room_objects();
			if ((frame & 127) == 0) {
				if (ABS(qx - stuckx[i]) < 96 && ABS(qy - stucky[i]) < 96) { qvy = -40; qvx = (frame & 128) ? 24 : -24; }
				stuckx[i] = qx; stucky[i] = qy;
			}
			ballx[i] = qx; bally[i] = qy; ballvx[i] = qvx; ballvy[i] = qvy;
			if (qy > (204 << 5)) { exit_req = 1; bst[i] = BS_NONE; }
			continue;
		}
		if (!launched && qy < (130 << 5)) launched = 1;
		if ((frame & 127) == (i << 4)) {
			if (ABS(qx - stuckx[i]) < 96 && ABS(qy - stucky[i]) < 96) {
				qvy = -40; qvx = (frame & 128) ? 24 : -24;
				show_msg("BALL SEARCH!", 40);
			}
			stuckx[i] = qx; stucky[i] = qy;
		}
		ball_objects();
		fire_ball();
		/* fell back into plunger? */
		if (!launched && qx > 7232 && qy > (490 << 5)) { bst[i] = BS_PLUNGER; qvx = 0; qvy = 0; qy = 494 << 5; }
		ballx[i] = qx; bally[i] = qy; ballvx[i] = qvx; ballvy[i] = qvy;
		if (bally[i] > (506 << 5)) {
			/* drained */
			bst[i] = BS_NONE;
		}
	}
	if (sub_cool) sub_cool--;

	if (room) {
		room_update();
		if (boss_cool) boss_cool--;
		if (emp_cool) emp_cool--;
		if (expl_t) expl_t--;
		if (exit_req) exit_room();
		if (score_dirty) draw_hud();
		if (msg_t) { if (--msg_t == 0) room_msg(); }
		draw_sprites();
		set_scroll();
		satb_update();
		sound_update();
		vsync();
		return;
	}

	/* timers & objects */
	fire_update();
	taxi_update();
	tank_update();
	tentacle_update();
	if (boss_cool) boss_cool--;
	if (emp_cool) emp_cool--;
	if (expl_t) expl_t--;
	for (i = 0; i < 3; i++) {
		if (bump_flash[i]) {
			bump_flash[i]--;
			if (bump_flash[i] == 0)
				put_block(VAR_BUMP_POS[i * 4], VAR_BUMP_POS[i * 4 + 1], VAR_BUMP_POS[i * 4 + 2], VAR_BUMP_POS[i * 4 + 3], VAR_BUMP_OFF + i * 16);
		}
	}
	if (tgt_reset) { if (--tgt_reset == 0) reset_targets(); }
	if (save_t > 1) save_t--;
	if (boss_awake) {
		if (--stomp_t == 0) {
			stomp_t = 300 - boss_stage * 20;
			shake = 24;
			snd_roar();
			show_msg("STOMP!", 40);
			for (i = 0; i < MAXB; i++) if (bst[i] == BS_PLAY) { ballvy[i] -= 16; ballvx[i] += (frame & 2) ? 20 : -20; }
		}
		if (--fire_t == 0) {
			fire_t = 220 - boss_stage * 15;
			spawn_fire(116, 100);
			if (cam < 120) show_msg("FIRE BREATH!", 40);
		}
	}
	i = count_balls();
	if (multiball && i <= 1) {
		multiball = 0;
		reset_empire();
		show_msg("AIRSTRIKE OVER", 60);
	}
	if (boss_awake || (frame & 63) == 0) kaiju_colors();
	if (pending_room) { enter_room(pending_room); return; }
	if (msg_t) { if (--msg_t == 0) default_msg(); }
	if (score_dirty) draw_hud();

	update_camera();
	draw_sprites();
	set_scroll();
	satb_update();
	sound_update();
	vsync();
}

void pause_game(void)
{
	show_msg("PAUSED", 0);
	psg_ch(3); psg_ctl(0);
	for (;;) {
		vsync();
		if (joytrg(0) & JOY_RUN) break;
	}
	default_msg();
}

void play_game(void)
{
	unsigned char i, lost, saved;
	for (i = 0; i < 8; i++) score[i] = 0;
	mult = 1; ball_no = 1; balls_left = 3; extra_balls = 0;
	boss_stage = 1; boss_reset_stage();
	taxi_x = 60; taxi_dir = 1; taxi_wreck = 0;
	tank_x = 100; tank_dir = 1; tank_cool = 0; shell_on = 0; expl_t = 0;
	multiball = 0; sub_cool = 0; tgt_reset = 0;
	room = 0; pending_room = 0; exit_req = 0; sub_lit = 0; sever_count = 0; fire_clear();
	fl_lx = LPX; fl_rx = RPX; fl_py = LPY; flip_zone = 13600;
	for (i = 0; i < 3; i++) bump_flash[i] = 0;
	for (i = 0; i < 4; i++) { ten_cool[i] = 0; ten_flash[i] = 0; }
	reset_targets();
	reset_empire();
	set_torch(1);
	hud_frame();
	cam = CAM_MAX;
	saved = 0;
	while (balls_left) {
		serve_ball(!saved);
		if (!saved) {
			strcpy(msgbuf, "BALL 0 - HOLD I TO PLUNGE");
			msgbuf[5] = '0' + ball_no;
			show_msg(msgbuf, 150);
		}
		saved = 0;
		draw_hud();
		for (;;) {
			game_frame();
			if (joytrg(0) & JOY_RUN) pause_game();
			i = count_balls();
			if (i == 0) break;
		}
		if (save_t > 1) {
			show_msg("BALL SAVED!", 90);
			saved = 1;
			continue;
		}
		snd_drain();
		show_msg("BALL LOST", 90);
		multiball = 0;
		reset_empire();
		for (lost = 0; lost < 90; lost++) { update_camera(); set_scroll(); satb_update(); sound_update(); vsync(); }
		balls_left--;
		if (balls_left) { ball_no++; if (ball_no > 9) ball_no = 9; }
		mult = 1;
		draw_hud();
	}
	show_msg("GAME OVER", 0);
	for (i = 0; i < 8; i++) {
		if (score[i] > hiscore[i]) { for (lost = 0; lost < 8; lost++) hiscore[lost] = score[lost]; show_msg("NEW HIGH SCORE!", 0); break; }
		if (score[i] < hiscore[i]) break;
	}
	for (lost = 0; lost < 200; lost++) { sound_update(); vsync(); }
}

void main(void)
{
	load_graphics();
	psg_init();
	srand(7);
	for (;;) {
		title_screen();
		play_game();
	}
}
