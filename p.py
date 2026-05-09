#!/usr/bin/env python3

# ╔══════════════════════════════════════════════════════════════════╗
# ║           A S C I I   A R T   G E N E R A T O R                 ║
# ║                  by Mohammed Al-Badiah                           ║
# ╚══════════════════════════════════════════════════════════════════╝

import os
import sys
import time
import random
import shutil

# ─────────────────────────────────────────────
#   ANSI CODES
# ─────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
HIDE   = "\033[?25l"
SHOW   = "\033[?25h"
CLEAR  = "\033[2J\033[H"

def fg(r, g, b):   return f"\033[38;2;{r};{g};{b}m"
def bg(r, g, b):   return f"\033[48;2;{r};{g};{b}m"

# ─────────────────────────────────────────────
#   COLOR PALETTES
# ─────────────────────────────────────────────

PALETTES = {
    "fire"   : [(255,50,0),(255,100,0),(255,150,0),(255,200,0),(255,240,80)],
    "ocean"  : [(0,20,80),(0,60,160),(0,130,220),(0,200,240),(100,240,255)],
    "neon"   : [(255,0,200),(150,0,255),(0,100,255),(0,240,200),(0,255,100)],
    "gold"   : [(80,40,0),(160,90,0),(220,150,0),(255,210,50),(255,240,160)],
    "matrix" : [(0,20,0),(0,60,0),(0,120,0),(0,200,0),(80,255,80)],
    "ice"    : [(20,40,80),(60,100,180),(100,160,240),(180,220,255),(230,245,255)],
    "lava"   : [(50,0,0),(120,10,0),(200,40,0),(255,80,20),(255,160,80)],
    "rainbow": [(255,50,50),(255,180,0),(100,255,50),(0,200,255),(180,0,255)],
}

def palette_color(name, index, total):
    colors = PALETTES.get(name, PALETTES["neon"])
    n = len(colors)
    t = (index / max(total - 1, 1)) * (n - 1)
    i = int(t)
    f = t - i
    c1 = colors[min(i, n-1)]
    c2 = colors[min(i+1, n-1)]
    return (
        int(c1[0] + (c2[0]-c1[0])*f),
        int(c1[1] + (c2[1]-c1[1])*f),
        int(c1[2] + (c2[2]-c1[2])*f),
    )

# ─────────────────────────────────────────────
#   FONT DATA  (5 rows each)
# ─────────────────────────────────────────────

BLOCK = {
    'A': ["  ###  "," #   # "," ##### "," #   # "," #   # "],
    'B': [" ####  "," #   # "," ####  "," #   # "," ####  "],
    'C': ["  #### "," #     "," #     "," #     ","  #### "],
    'D': [" ####  "," #   # "," #   # "," #   # "," ####  "],
    'E': [" ##### "," #     "," ####  "," #     "," ##### "],
    'F': [" ##### "," #     "," ####  "," #     "," #     "],
    'G': ["  #### "," #     "," # ### "," #   # ","  #### "],
    'H': [" #   # "," #   # "," ##### "," #   # "," #   # "],
    'I': [" ##### ","   #   ","   #   ","   #   "," ##### "],
    'J': ["   ### ","     # ","     # "," #   # ","  ###  "],
    'K': [" #   # "," #  #  "," ###   "," #  #  "," #   # "],
    'L': [" #     "," #     "," #     "," #     "," ##### "],
    'M': [" #   # "," ## ## "," # # # "," #   # "," #   # "],
    'N': [" #   # "," ##  # "," # # # "," #  ## "," #   # "],
    'O': ["  ###  "," #   # "," #   # "," #   # ","  ###  "],
    'P': [" ####  "," #   # "," ####  "," #     "," #     "],
    'Q': ["  ###  "," #   # "," # # # "," #  ## ","  #### "],
    'R': [" ####  "," #   # "," ####  "," #  #  "," #   # "],
    'S': ["  #### "," #     ","  ###  ","     # "," ####  "],
    'T': [" ##### ","   #   ","   #   ","   #   ","   #   "],
    'U': [" #   # "," #   # "," #   # "," #   # ","  ###  "],
    'V': [" #   # "," #   # "," #   # ","  # #  ","   #   "],
    'W': [" #   # "," #   # "," # # # "," ## ## "," #   # "],
    'X': [" #   # ","  # #  ","   #   ","  # #  "," #   # "],
    'Y': [" #   # ","  # #  ","   #   ","   #   ","   #   "],
    'Z': [" ##### ","    #  ","   #   ","  #    "," ##### "],
    '0': ["  ###  "," #  ## "," # # # "," ##  # ","  ###  "],
    '1': ["   #   ","  ##   ","   #   ","   #   "," ##### "],
    '2': ["  ###  "," #   # ","   ##  ","  ##   "," ##### "],
    '3': [" ####  ","     # ","  ###  ","     # "," ####  "],
    '4': [" #  #  "," #  #  "," ##### ","    #  ","    #  "],
    '5': [" ##### "," #     "," ####  ","     # "," ####  "],
    '6': ["  #### "," #     "," ####  "," #   # ","  #### "],
    '7': [" ##### ","     # ","    #  ","   #   ","   #   "],
    '8': ["  ###  "," #   # ","  ###  "," #   # ","  ###  "],
    '9': ["  #### "," #   # ","  #### ","     # ","  #### "],
    ' ': ["       ","       ","       ","       ","       "],
    '!': ["   #   ","   #   ","   #   ","       ","   #   "],
    '?': ["  ###  "," #   # ","   ##  ","       ","   #   "],
    '.': ["       ","       ","       ","       ","   #   "],
    '-': ["       ","       "," ##### ","       ","       "],
    '*': ["       "," # # # ","  ###  "," # # # ","       "],
    '+': ["       ","   #   "," ##### ","   #   ","       "],
}

# ─────────────────────────────────────────────
#   FONT STYLE TRANSFORMS
# ─────────────────────────────────────────────

def style_block(rows):    return rows

def style_banner(rows):   return [r.replace('#','█') for r in rows]

def style_doom(rows):     return [r.replace('#','▓').replace(' ','░') for r in rows]

def style_3d(rows):
    n   = len(rows)
    out = []
    for i, row in enumerate(rows):
        new = ""
        for c in row:
            if c == '#':
                new += "▄" if i == 0 else ("▀" if i == n-1 else "█")
            else:
                new += " "
        out.append(new)
    return out

def style_digital(rows):  return [r.replace('#','▮').replace(' ','·') for r in rows]

def style_star(rows):     return [r.replace('#','✦') for r in rows]

def style_double(rows):   return ["".join(c*2 for c in row) for row in rows]

def style_hollow(rows):
    n   = len(rows)
    out = []
    for i, row in enumerate(rows):
        w   = len(row)
        new = ""
        for j, c in enumerate(row):
            if c == '#':
                edge = (
                    i == 0 or i == n-1 or j == 0 or j == w-1
                    or (i>0   and rows[i-1][j] != '#')
                    or (i<n-1 and rows[i+1][j] != '#')
                    or (j>0   and row[j-1]      != '#')
                    or (j<w-1 and row[j+1]      != '#')
                )
                new += "█" if edge else " "
            else:
                new += " "
        out.append(new)
    return out

STYLES = {
    "block"  : style_block,
    "banner" : style_banner,
    "doom"   : style_doom,
    "3d"     : style_3d,
    "digital": style_digital,
    "star"   : style_star,
    "double" : style_double,
    "hollow" : style_hollow,
}

# ─────────────────────────────────────────────
#   RENDER ENGINE
# ─────────────────────────────────────────────

def get_char(ch, style):
    rows = list(BLOCK.get(ch.upper(), BLOCK[' ']))
    return STYLES.get(style, style_block)(rows)

def render(text, style="block"):
    chars = [get_char(c, style) for c in text[:12].upper()]
    h     = max(len(c) for c in chars)
    lines = []
    for row in range(h):
        lines.append("  ".join(
            c[row] if row < len(c) else " " * len(c[0])
            for c in chars
        ))
    return lines

def add_border(lines):
    w   = max(len(l) for l in lines)
    top = "╔" + "═" * (w + 4) + "╗"
    bot = "╚" + "═" * (w + 4) + "╝"
    mid = ["║  " + l.ljust(w) + "  ║" for l in lines]
    return [top, "║  " + " "*w + "  ║"] + mid + ["║  " + " "*w + "  ║", bot]

def add_shadow(lines):
    w = max(len(l) for l in lines)
    result = []
    for i, line in enumerate(lines):
        shadow = ""
        if i > 0:
            prev = lines[i-1].ljust(w)
            shadow = "   " + "".join(
                "▒" if c not in (" ","░","·","▒") else " "
                for c in prev
            )
        result.append(line.ljust(w) + shadow)
    return result

# ─────────────────────────────────────────────
#   COLOR PRINTER
# ─────────────────────────────────────────────

def print_colored(lines, palette="neon", mode="rows"):
    total = len(lines)
    for i, line in enumerate(lines):
        if mode == "rows":
            r, g, b = palette_color(palette, i, total)
            print(fg(r,g,b) + line + RESET)
        elif mode == "chars":
            out = ""
            n   = len(line)
            for j, c in enumerate(line):
                if c.strip():
                    r,g,b = palette_color(palette, j, n)
                    out  += fg(r,g,b) + c
                else:
                    out  += " "
            print(out + RESET)
        else:   # random
            out = ""
            for c in line:
                if c.strip():
                    r = random.randint(80,255)
                    g = random.randint(80,255)
                    b = random.randint(80,255)
                    out += fg(r,g,b) + c
                else:
                    out += " "
            print(out + RESET)

# ─────────────────────────────────────────────
#   ANIMATIONS
# ─────────────────────────────────────────────

def up(n):   print(f"\033[{n}A", end="")

def animate_typewriter(lines, palette="neon", delay=0.007):
    total = len(lines)
    for i, line in enumerate(lines):
        r, g, b = palette_color(palette, i, total)
        col     = fg(r,g,b)
        for ch in line:
            print(col + ch + RESET, end="", flush=True)
            time.sleep(delay)
        print()
        time.sleep(delay * 3)

def animate_wave(lines, palette="neon", frames=28, delay=0.045):
    total = len(lines)
    w     = max(len(l) for l in lines)
    for frame in range(frames):
        if frame > 0: up(total)
        for i, line in enumerate(lines):
            r, g, b = palette_color(palette, (i + frame) % max(total,1), total)
            print(fg(r,g,b) + line.ljust(w) + RESET)
        time.sleep(delay)

def animate_reveal(lines, palette="neon", delay=0.05):
    w     = max(len(l) for l in lines)
    total = len(lines)
    for col in range(w + 1):
        if col > 0: up(total)
        for i, line in enumerate(lines):
            r, g, b = palette_color(palette, i, total)
            print(fg(r,g,b) + line[:col].ljust(col) + " " * max(0,len(line)-col) + RESET)
        time.sleep(delay / w * 2)

def animate_glitch(lines, palette="neon", cycles=4, delay=0.065):
    glitch = list("@#$%▓░▒▮■□◆◇○●")
    total  = len(lines)
    for _ in range(cycles):
        if _ > 0: up(total)
        for i, line in enumerate(lines):
            r, g, b  = palette_color(palette, i, total)
            glitched = ""
            for c in line:
                if c.strip() and random.random() < 0.3:
                    glitched += fg(255,0,0) + random.choice(glitch)
                else:
                    glitched += fg(r,g,b) + c
            print(glitched + RESET)
        time.sleep(delay)
    up(total)
    print_colored(lines, palette, "rows")

def animate_matrix(lines, palette="matrix", delay=0.04):
    art_w  = max(len(l) for l in lines)
    art_h  = len(lines)
    drops  = [random.randint(-art_h, 0) for _ in range(art_w + 4)]
    chars  = list("01アイウエオカキクケコﾊﾌﾍﾎ")
    for frame in range(art_h * 3):
        if frame > 0: up(art_h)
        canvas = [[" "] * (art_w + 4) for _ in range(art_h)]
        for ci, dp in enumerate(drops):
            for ri in range(art_h):
                dist = ri - dp
                if 0 <= dist < 5 and 0 <= ci < art_w + 4:
                    brightness = 4 - dist
                    r, g, b    = palette_color(palette, brightness, 5)
                    canvas[ri][ci] = fg(r,g,b) + random.choice(chars) + RESET
            drops[ci] += 1
            if drops[ci] > art_h + 5:
                drops[ci] = random.randint(-art_h, -2)
        for row in canvas:
            print("".join(row))
        time.sleep(delay)
    up(art_h)
    print_colored(lines, palette, "rows")

def animate_explosion(lines, palette="fire", frames=18, delay=0.05):
    total = len(lines)
    w     = max(len(l) for l in lines)
    for frame in range(frames):
        if frame > 0: up(total)
        scale = frame / (frames - 1)
        for i, line in enumerate(lines):
            r, g, b = palette_color(palette, i, total)
            pad     = int(scale * 3)
            spaces  = " " * pad
            exploded = ""
            for c in line:
                exploded += c
                if c.strip() and scale > 0.5:
                    exploded += " " * random.randint(0, 1)
            print(spaces + fg(r,g,b) + exploded + RESET)
        time.sleep(delay)

# ─────────────────────────────────────────────
#   SPLASH
# ─────────────────────────────────────────────

SPLASH_ART = [
    " █████╗  ███████╗ ██████╗██╗██╗     █████╗ ██████╗ ████████╗",
    "██╔══██╗ ██╔════╝██╔════╝██║██║    ██╔══██╗██╔══██╗╚══██╔══╝",
    "███████║ ███████╗██║     ██║██║    ███████║██████╔╝   ██║   ",
    "██╔══██║ ╚════██║██║     ██║██║    ██╔══██║██╔══██╗   ██║   ",
    "██║  ██║ ███████║╚██████╗██║██║    ██║  ██║██║  ██║   ██║   ",
    "╚═╝  ╚═╝ ╚══════╝ ╚═════╝╚═╝╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ",
    "",
    " ██████╗ ███████╗███╗  ██╗███████╗██████╗  █████╗ ████████╗ ██████╗ ██████╗",
    "██╔════╝ ██╔════╝████╗ ██║██╔════╝██╔══██╗██╔══██╗╚══██╔══╝██╔═══██╗██╔══██╗",
    "██║  ███╗█████╗  ██╔██╗██║█████╗  ██████╔╝███████║   ██║   ██║   ██║██████╔╝",
    "██║   ██║██╔══╝  ██║╚████║██╔══╝  ██╔══██╗██╔══██║   ██║   ██║   ██║██╔══██╗",
    "╚██████╔╝███████╗██║ ╚███║███████╗██║  ██║██║  ██║   ██║   ╚██████╔╝██║  ██║",
    " ╚═════╝ ╚══════╝╚═╝  ╚══╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝",
]

def print_splash():
    print(CLEAR, end="")
    print(HIDE,  end="")
    for i, line in enumerate(SPLASH_ART):
        r, g, b = palette_color("neon", i, len(SPLASH_ART))
        print(fg(r,g,b) + line + RESET)
        time.sleep(0.04)
    print()
    sub = "  ✦  Type any text  ✦  Pick a font & palette  ✦  Choose an animation  ✦"
    for j, c in enumerate(sub):
        r, g, b = palette_color("rainbow", j, len(sub))
        print(fg(r,g,b) + c + RESET, end="", flush=True)
        time.sleep(0.012)
    print("\n")
    print(SHOW, end="")

# ─────────────────────────────────────────────
#   MENU HELPERS
# ─────────────────────────────────────────────

def divider(w=65):
    r, g, b = palette_color("neon", 1, 5)
    print(fg(r,g,b) + "─" * w + RESET)

def header(text):
    r, g, b = palette_color("gold", 3, 5)
    pad = (65 - len(text) - 2) // 2
    print(fg(r,g,b) + "─"*pad + " " + text + " " + "─"*pad + RESET)

def ask(prompt_text):
    r, g, b = palette_color("gold", 4, 5)
    return input(fg(r,g,b) + "  " + prompt_text + RESET + " ")

def show_menu(title, options, pal="neon"):
    header(title)
    for i, (key, label) in enumerate(options):
        r, g, b = palette_color(pal, i, len(options))
        print(f"  {fg(r,g,b)}{key}{RESET}  {label}")
    print()

# ─────────────────────────────────────────────
#   EXPORT
# ─────────────────────────────────────────────

def export(lines, filename="ascii_art.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        for line in lines:
            clean, skip = "", False
            for c in line:
                if c == "\033":  skip = True
                elif skip and c == "m": skip = False
                elif not skip:   clean += c
            f.write(clean + "\n")
    r, g, b = palette_color("matrix", 4, 5)
    print(fg(r,g,b) + f"  ✔  Saved  →  {filename}" + RESET)

# ─────────────────────────────────────────────
#   MAIN
# ─────────────────────────────────────────────

def main():

    print_splash()

    ######  TEXT
    header("ENTER YOUR TEXT")
    text = ask("Text (max 12 chars) :").strip() or "HELLO"
    text = text[:12]
    print()

    ######  FONT
    show_menu("FONT STYLE", [
        ("1","block   — clean bold letters"),
        ("2","banner  — solid filled █ blocks"),
        ("3","doom    — textured shading ▓░"),
        ("4","3d      — depth effect ▄▀█"),
        ("5","digital — pixel dots ▮·"),
        ("6","star    — star glyphs ✦"),
        ("7","double  — double-width"),
        ("8","hollow  — outline only"),
    ], "ocean")
    font = {"1":"block","2":"banner","3":"doom","4":"3d",
            "5":"digital","6":"star","7":"double","8":"hollow"}.get(
        ask("Font [1-8] :").strip(), "block")
    print()

    ######  PALETTE
    show_menu("COLOR PALETTE", [
        ("1","neon    — electric purple/cyan"),
        ("2","fire    — blazing orange/red"),
        ("3","ocean   — deep blue/aqua"),
        ("4","gold    — rich golden tones"),
        ("5","matrix  — cyber green"),
        ("6","ice     — arctic blue/white"),
        ("7","lava    — volcanic red/orange"),
        ("8","rainbow — full spectrum"),
    ], "fire")
    palette = {"1":"neon","2":"fire","3":"ocean","4":"gold",
               "5":"matrix","6":"ice","7":"lava","8":"rainbow"}.get(
        ask("Palette [1-8] :").strip(), "neon")
    print()

    ######  EXTRAS
    header("EXTRAS")
    use_border = ask("Add border?  [y/n] :").strip().lower() == "y"
    use_shadow = ask("Drop shadow? [y/n] :").strip().lower() == "y"
    cmode = {"r":"rows","c":"chars","x":"random"}.get(
        ask("Color mode (r=rows  c=chars  x=random) [r/c/x] :").strip().lower(), "rows")
    print()

    ######  ANIMATION
    show_menu("ANIMATION", [
        ("1","typewriter — char by char reveal"),
        ("2","wave       — sweeping color wave"),
        ("3","reveal     — wipe left to right"),
        ("4","glitch     — scramble & fix"),
        ("5","matrix     — matrix rain drop"),
        ("6","explosion  — burst in from center"),
        ("7","none       — instant print"),
    ], "matrix")
    anim = ask("Animation [1-7] :").strip()
    print()

    ######  BUILD
    lines = render(text, font)
    if use_shadow: lines = add_shadow(lines)
    if use_border: lines = add_border(lines)

    ######  OUTPUT
    divider()
    print()

    if   anim == "1": animate_typewriter(lines, palette)
    elif anim == "2": animate_wave(lines, palette)
    elif anim == "3": animate_reveal(lines, palette)
    elif anim == "4": print_colored(lines, palette, cmode); time.sleep(0.2); animate_glitch(lines, palette)
    elif anim == "5": animate_matrix(lines, palette)
    elif anim == "6": animate_explosion(lines, palette)
    else:             print_colored(lines, palette, cmode)

    print()
    divider()
    print()

    ######  SAVE
    if ask("Save to file? [y/n] :").strip().lower() == "y":
        fname = ask("Filename [ascii_art.txt] :").strip() or "ascii_art.txt"
        export(lines, fname)

    print()
    r, g, b = palette_color("neon", 3, 5)
    print(fg(r,g,b) + "  ✦  Done! Run again for a new design." + RESET)
    print()


# ─────────────────────────────────────────────
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(SHOW)
        print(fg(255,80,80) + "\n  Cancelled." + RESET)
        sys.exit(0)
