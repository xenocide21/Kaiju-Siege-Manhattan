#!/usr/bin/env python3
"""Instruction manual for Kaiju Siege: Manhattan -> docs/kaiju_siege_manual.pdf
Pocket booklet size (5.5 x 8.5 in), like a HuCard manual.
Usage: python3 tools/manual.py [image_dir]   (image_dir holds the screenshots)"""
import os, sys
from reportlab.lib.pagesizes import inch
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Image,
                                Table, TableStyle, PageBreak, NextPageTemplate, KeepTogether)

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, '..', 'docs')
IMG = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DOCS, 'manual_images')
OUT = os.path.join(DOCS, 'kaiju_siege_manual.pdf')

PW, PH = 5.5 * inch, 8.5 * inch
M = 0.5 * inch
NAVY = colors.HexColor('#14102e')
ORANGE = colors.HexColor('#ff7a00')
RED = colors.HexColor('#c81e1e')
GREEN = colors.HexColor('#3c8c3c')
INK = colors.HexColor('#1a1a1a')
PALE = colors.HexColor('#f3eee2')

body = ParagraphStyle('body', fontName='Helvetica', fontSize=11, leading=14.5, textColor=INK, spaceAfter=7)
small = ParagraphStyle('small', parent=body, fontSize=11, leading=14)
h1 = ParagraphStyle('h1', fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=RED, spaceAfter=8)
h2 = ParagraphStyle('h2', fontName='Helvetica-Bold', fontSize=13.5, leading=17, textColor=NAVY, spaceBefore=6, spaceAfter=4)
cap = ParagraphStyle('cap', parent=body, fontSize=9.5, leading=12, textColor=colors.HexColor('#555555'), alignment=TA_CENTER)
cell = ParagraphStyle('cell', parent=body, fontSize=10.5, leading=13, spaceAfter=0)
cellb = ParagraphStyle('cellb', parent=cell, fontName='Helvetica-Bold')
cellh = ParagraphStyle('cellh', parent=cellb, textColor=colors.white)
center = ParagraphStyle('center', parent=body, alignment=TA_CENTER)


def cover(c, doc):
    c.saveState()
    c.setFillColor(NAVY); c.rect(0, 0, PW, PH, fill=1, stroke=0)
    bg = os.path.join(DOCS, 'backglass.png')
    iw = PW - 0.5 * inch; ih = iw * 1080 / 960
    c.drawImage(bg, (PW - iw) / 2, PH - ih - 0.3 * inch, iw, ih)
    c.setFillColor(ORANGE); c.setFont('Helvetica-Bold', 15)
    c.drawCentredString(PW / 2, 1.1 * inch, 'INSTRUCTION MANUAL')
    c.setFillColor(colors.white); c.setFont('Helvetica', 10.5)
    c.drawCentredString(PW / 2, 0.82 * inch, 'TurboGrafx-16 / PC Engine HuCard  -  1 Player')
    c.drawCentredString(PW / 2, 0.58 * inch, 'A Xenocide21 Game')
    c.restoreState()


def page(c, doc):
    c.saveState()
    c.setFillColor(NAVY); c.rect(0, PH - 0.32 * inch, PW, 0.32 * inch, fill=1, stroke=0)
    c.setFillColor(ORANGE); c.rect(0, PH - 0.36 * inch, PW, 0.04 * inch, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont('Helvetica-Bold', 9)
    c.drawString(M, PH - 0.22 * inch, 'KAIJU SIEGE: MANHATTAN')
    c.setFont('Helvetica', 9)
    c.drawRightString(PW - M, PH - 0.22 * inch, 'Instruction Manual')
    c.setFillColor(INK); c.setFont('Helvetica', 9.5)
    c.drawCentredString(PW / 2, 0.3 * inch, str(doc.page))
    c.restoreState()


def img(name, w, h=None, src=IMG):
    from PIL import Image as P
    path = os.path.join(src, name)
    iw, ih = P.open(path).size
    if h is None:
        h = w * ih / iw
    return Image(path, w, h)


def table(rows, widths, head=True):
    data = [[Paragraph(str(x), cellh if (head and r == 0) else (cellb if k == 0 else cell)) for k, x in enumerate(row)]
            for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths)
    st = [('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#999999')),
          ('VALIGN', (0, 0), (-1, -1), 'TOP'),
          ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
          ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PALE])]
    if head:
        st += [('BACKGROUND', (0, 0), (-1, 0), NAVY), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white)]
    t.setStyle(TableStyle(st))
    return t


def headcell(t):
    # white text in header row
    return t


CW = PW - 2 * M
s = []
s.append(NextPageTemplate('inner'))
s.append(PageBreak())

# ---------------- story
s.append(Paragraph('The Drowned King Rises', h1))
s.append(Paragraph('Something old has woken beneath the Hudson. <b>ZHA\'GORATH, The Drowned King</b>, has dragged '
                   'his bulk ashore at Central Park. He has three eyes, a crown of horns and a beard of writhing '
                   'tentacles, and he means to drown Manhattan.', body))
s.append(Paragraph('The army is rolling tanks down the avenues. Fighter jets are scrambling. Lady Liberty holds her '
                   'torch high over the harbor. The fight to save the city comes down to one steel ball and two '
                   'flippers.', body))
s.append(Paragraph('Battle your way up the island from the Financial District, through Times Square, to the kaiju '
                   'himself. Open his eyes, survive his awakening and drive him back into the deep.', body))
s.append(Spacer(1, 4))
s.append(img('f_title.png', CW * 0.8))
s.append(Paragraph('Title screen', cap))

# ---------------- getting started / controls
s.append(PageBreak())
s.append(Paragraph('Getting Started', h1))
s.append(Paragraph('Load the HuCard (<b>kaiju_siege_manhattan.pce</b>) in your TurboGrafx-16 or PC Engine '
                   'emulator, or on a flash cart. When the title screen appears, press <b>RUN</b>.', body))
s.append(Paragraph('You start with <b>3 balls</b>. The ball waits in the plunger lane on the right side of the '
                   'table. Hold button I to pull back the plunger, and release it to launch.', body))
s.append(Paragraph('Controls', h2))
t = table([['Button', 'Action'],
           ['RUN', 'Start a game / pause'],
           ['D-pad (any direction)', 'Left flipper'],
           ['I or II', 'Right flipper'],
           ['Hold I (or II / Down)', 'Pull the plunger. Release to launch. A longer hold launches harder.'],
           ['SELECT', 'Nudge the table']], [CW * 0.38, CW * 0.62])
s.append(headcell(t))
s.append(Spacer(1, 8))
s.append(Paragraph('The Screen', h2))
s.append(Paragraph('The bar at the top shows your <b>score</b>, the <b>ball</b> in play and your score '
                   '<b>multiplier</b>. The line under it carries messages: what just happened, and what the '
                   'kaiju is up to.', body))
s.append(Paragraph('The table is more than two screens tall. The view scrolls to follow the ball, from the '
                   'flippers up to the kaiju.', body))
s.append(Paragraph('<b>Ball save:</b> if you lose the ball in the first 10 seconds after launching, it comes back. '
                   'This works once per ball.', body))

# ---------------- the table
s.append(PageBreak())
s.append(Paragraph('The Table', h1))
tbl_img = img('table.png', CW * 0.42, src=IMG)
zones = [Paragraph('<b><font color="#3c8c3c">CENTRAL PARK &amp; THE HUDSON</font></b><br/>The kaiju\'s lair. '
                   'Hit his face and his tentacles.', small),
         Spacer(1, 6),
         Paragraph('<b><font color="#c81e1e">MIDTOWN</font></b><br/>Times Square bumpers, the army tank, the '
                   'Subway hole and the Empire State Building.', small),
         Spacer(1, 6),
         Paragraph('<b><font color="#14102e">LOWER MANHATTAN</font></b><br/>Flippers, slingshots, the taxi, the '
                   'Wall Street targets, Liberty and the Brooklyn Bridge.', small)]
side = Table([[tbl_img, zones]], colWidths=[CW * 0.46, CW * 0.54])
side.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('LEFTPADDING', (0, 0), (-1, -1), 0)]))
s.append(side)
s.append(Spacer(1, 6))
s.append(Paragraph('Lower Manhattan', h2))
s.append(Paragraph('<b>Statue of Liberty:</b> when her torch is lit, a ball that falls down the left outlane is '
                   'kicked back into play. Each kickback uses up the torch.', body))
s.append(Paragraph('<b>Yellow cab:</b> drives back and forth across the street. Smash it for points. The first '
                   'smash <b>lights the Subway</b>.', body))
s.append(Paragraph('<b>Wall Street:</b> knock down all three gold bars for <b>MARKET CRASH</b>. Your multiplier '
                   'goes up by 1 (to a maximum of x5) and Liberty\'s torch is relit.', body))
s.append(PageBreak())
s.append(Paragraph('Midtown', h2))
s.append(Paragraph('<b>Times Square:</b> three neon pop bumpers.', body))
s.append(Paragraph('<b>Army tank:</b> hit it and it fires a shell at the kaiju, damaging him if it lands.', body))
s.append(Paragraph('<b>Subway:</b> sink the ball for a Subway Express bonus. When the Subway is lit, the hole '
                   'takes you to the <b>Subway Tunnel</b> bonus room instead.', body))
s.append(Paragraph('<b>Empire State Building:</b> each hit climbs a floor. Reach the top to call in '
                   '<b>AIRSTRIKE</b>: jets drop two more balls for 3-ball multiball. During multiball, every hit '
                   'on the kaiju does double damage.', body))
s.append(Spacer(1, 6))
s.append(img('aw1.png', CW * 0.85))
s.append(Paragraph('Times Square, the Subway and the army tank', cap))

# ---------------- the kaiju
s.append(PageBreak())
s.append(Paragraph("Zha'gorath", h1))
s.append(img('awake.png', CW))
s.append(Paragraph('Zha\'gorath awakened: red eyes and pulsing wings', cap))
s.append(Paragraph('Opening the Eyes', h2))
s.append(Paragraph('Damage the kaiju by hitting his <b>face</b>, severing his four <b>tentacles</b> (3 hits '
                   'each) and landing <b>tank shells</b>. Enough damage opens one of his three eyes. The tentacles '
                   'grow back after a while.', body))
s.append(Paragraph('The Awakening', h2))
s.append(Paragraph('When the third eye opens, <b>ZHA\'GORATH AWAKENS</b>. His eyes burn red and his wings pulse. '
                   'His tentacles move faster and hit harder. He <b>STOMPs</b>, shaking the whole table, and '
                   'breathes <b>FIRE</b>: three fireballs rain down the table and knock the ball off course.', body))
s.append(Paragraph('Defeating Him', h2))
s.append(Paragraph('Keep hitting the awakened kaiju to drive him back into the Hudson for <b>1,000,000 points</b> '
                   'times your multiplier. Your first victory also awards an <b>extra ball</b>. Each time he '
                   'comes back he is tougher: his eyes take more damage to open and he breathes fire more '
                   'often.', body))

# ---------------- bonus rooms
s.append(PageBreak())
s.append(Paragraph('Bonus Rooms', h1))
s.append(Paragraph('Each bonus room is a one-screen mini table with its own flippers and a <b>45-second</b> '
                   'timer. If you drain in a bonus room, you <b>don\'t</b> lose the ball. It goes back to the '
                   'main table.', body))
rooms = [
    ('r1_9.png', 'Subway Tunnel',
     '<b>Get in:</b> smash the taxi to light the Subway, then sink the ball in the Subway hole.',
     '<b>Goal:</b> throw the three track switches on the top wall to <b>derail the train</b> '
     '(+250,000). A train roars through every few seconds and flings the ball if it hits it.'),
    ('r2_3.png', 'Rooftop Showdown',
     '<b>Get in:</b> once two eyes are open (or he is awake), hit the Empire State target.',
     '<b>Goal:</b> face the kaiju from a skyscraper roof. Shoot out his three giant eyes '
     'through fire breath and swinging tentacles. Destroy all three to <b>slay the kaiju</b>.'),
    ('r3_12.png', 'The Sunken Shrine',
     '<b>Get in:</b> every 4th tentacle you sever opens the shrine.',
     '<b>Goal:</b> a flooded subway station where hooded cultists patrol. Smash the altar in six hits '
     '(+500,000). Destroying it also deals heavy damage to the kaiju.'),
]
for (f, name, a, b) in rooms:
    block = Table([[img(f, CW * 0.44), [Paragraph(name, h2), Paragraph(a, small), Paragraph(b, small)]]],
                  colWidths=[CW * 0.47, CW * 0.53])
    block.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 0),
                               ('BOTTOMPADDING', (0, 0), (-1, -1), 8)]))
    s.append(KeepTogether(block))

# ---------------- scoring
s.append(PageBreak())
s.append(Paragraph('Scoring', h1))
s.append(Paragraph('Every value is multiplied by your current multiplier (x1 to x5). The multiplier goes back to '
                   'x1 when you lose a ball.', body))
t = table([['Target', 'Points'],
           ['Pop bumper', '100'],
           ['Slingshot', '10'],
           ['Wall Street gold bar', '1,500'],
           ['Market Crash (all three bars)', '25,000'],
           ['Taxi smash', '2,500'],
           ['Tank hit / shell on the kaiju', '500 / 5,000'],
           ['Empire State floor', '3,000'],
           ['Airstrike multiball', '50,000'],
           ['Subway Express', '5,000'],
           ['Tentacle hit / severed', '1,000 / 10,000'],
           ['Kaiju face hit', '2,500'],
           ['Eye opens', '25,000'],
           ['Kaiju defeated', '1,000,000'],
           ['Track switch / train derailed', '25,000 / 250,000'],
           ['Rooftop eye hit / destroyed', '10,000 / 50,000'],
           ['Cultist banished', '2,500'],
           ['Altar hit / shrine destroyed', '10,000 / 500,000']], [CW * 0.62, CW * 0.38])
s.append(headcell(t))
s.append(PageBreak())
s.append(Paragraph('Tips', h1))
for tip in ['Crash the market early. A higher multiplier makes everything else worth more.',
            'Keep Liberty\'s torch lit. It is the only thing between the left outlane and a lost ball.',
            'Send the tank\'s shells up the middle. They damage the kaiju even when you can\'t reach him.',
            'Save the Rooftop for when two eyes are open. Slaying him there counts as a full victory.',
            'Use SELECT to nudge a ball that is heading for an outlane, but don\'t overdo it.']:
    s.append(Paragraph('&bull; ' + tip, body))

s.append(Spacer(1, 10))
s.append(img('fm5.png', CW * 0.8))
s.append(Paragraph('AIRSTRIKE! Multiball over Lower Manhattan', cap))

# ---------------- credits
s.append(PageBreak())
s.append(Paragraph('Credits', h1))
s.append(Paragraph('<b>Concept and design:</b> Xenocide21', body))
s.append(Paragraph('<b>Code, art and sound:</b> built with Claude (Anthropic\'s AI), working from Xenocide21\'s '
                   'design', body))
s.append(Paragraph('<b>Toolchain:</b> HuCC by the pce-devel project (github.com/pce-devel/huc)', body))
s.append(Spacer(1, 10))
s.append(Paragraph('Source code and the latest ROM:<br/><b>github.com/xenocide21/Kaiju-Siege-Manhattan</b>', body))
s.append(Paragraph('Released under the MIT License. Copyright (c) 2026 Xenocide21.', body))
s.append(Paragraph('Kaiju Siege: Manhattan is an unofficial homebrew game. It is not licensed or endorsed by any '
                   'console maker. Zha\'gorath is an original character inspired by public-domain cosmic horror.',
                   body))

doc = BaseDocTemplate(OUT, pagesize=(PW, PH), title='Kaiju Siege: Manhattan - Instruction Manual',
                      author='Xenocide21', leftMargin=M, rightMargin=M, topMargin=0.6 * inch, bottomMargin=0.55 * inch)
fr = Frame(M, 0.55 * inch, PW - 2 * M, PH - 1.15 * inch, id='f', leftPadding=0, rightPadding=0)
doc.addPageTemplates([PageTemplate('cover', frames=[fr], onPage=cover),
                      PageTemplate('inner', frames=[fr], onPage=page)])
doc.build(s)
print('wrote', OUT)
