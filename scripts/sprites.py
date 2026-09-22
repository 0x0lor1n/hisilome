#!/usr/bin/env python3
"""Pixel avatars for the dialogue shortcode -> static/img/{kriton,olorin}.png

SIZE x SIZE (48), hand-placed pixels, one letter per palette entry, space = transparent.
Edit the grids here or open the PNGs in Piskel/Aseprite and re-save; the PNG
in static/img is the source of truth for the site, this script is just a
comfortable way to draft. Run from the repo root:

    nix-shell -p python3Packages.pillow --run 'python3 scripts/sprites.py'

Writes a 4x preview to /tmp/sprites-preview.png as well.
"""
from pathlib import Path
from PIL import Image

BG = (0x1F, 0x1F, 0x28)  # site background, preview only
SIZE = 48

# Kriton: Zeus profile, pixel map lifted 1:1 from an SVG of 1x1 rects
# (~/Downloads/zeus-the-greek-god-db19.svg, 64x64, 16 colours), nearest-
# neighbour downscaled to 41x44 so he sits level with Olorin. Cream hair
# and beard, dark-red skin, no outline.
KRITON_PAL = {
    "A": (0x90, 0x76, 0x58),
    "B": (0x77, 0x5F, 0x43),
    "C": (0xDC, 0xD3, 0xBD),
    "D": (0xD1, 0xC6, 0xAF),
    "E": (0xF6, 0xEF, 0xDC),
    "F": (0xB4, 0x9B, 0x7F),
    "H": (0xC6, 0xB3, 0x99),
    "I": (0x62, 0x4E, 0x36),
    "J": (0x4F, 0x3E, 0x2A),
    "M": (0x09, 0x05, 0x04),
    "N": (0x30, 0x0C, 0x0D),
    "O": (0x75, 0x27, 0x26),
    "P": (0x93, 0x46, 0x3E),
    "Q": (0x4A, 0x11, 0x16),
    "R": (0xA6, 0x5D, 0x52),
    "S": (0xC0, 0x80, 0x74),
}
KRITON = [
    "                                                ",
    "                                                ",
    "                        AAAAAAAAA               ",
    "                    AAABCCDDEEEECFF             ",
    "                  BAACCCEEEEHHCCCEEECA          ",
    "                 IFCCCEEEEEECCEEEDDDECFF        ",
    "                IADCEEEEEEEEEEECCDDDFEEEF       ",
    "               IFHHCCECEECCCCEEEEEDDDHEEDF      ",
    "               IFFDDECEECEEEEECCCCFFDCFDDD      ",
    "              JBFFDDDDCCEECCDDDCCCFMNNMIAA      ",
    "              BBAFFDFFCCHHHHDFFFAAMOPOQMMI      ",
    "              BBAFFDDCCDDDDDAAACEEOORSPONM      ",
    "             JBBBFFDDDDDDFDDDEEEAMORRSSRPN      ",
    "             JBBBFDFDDDDFFAAAAADEMRSSRRROO      ",
    "            JBBBBFFDDDDDFCCCHDDDFJRSSRROOO      ",
    "            JBBBFFFDDDHAJBBFFFAANNOPOEEPQO      ",
    "            JBBFFFAEDFHAMMMIIIIHBNOQFFEEHO      ",
    "           JJJJIIHCEEFIRMMNSMQJNNOOOQQMMFFM     ",
    "          JJJJBCCEEEFAMRQMMSJQQOOOMMMMMMMM      ",
    "          NNJJFEEECDAJQRQNMSAQOOPPQMM MMNN      ",
    "          IJJICCCCCBBJQRMNMQCAOOPSPPNMMNNO      ",
    "          JIDCCCCCHBJJQRNMMMEEQOOSSSOMNOOP      ",
    "        BHDCCCDDDFAJJJMOMMJJEEMNOOOOOOOPOOQ     ",
    "       JFFDEEEEDFFJBBJMQPMMJDEDNNNNNNOOOORQ     ",
    "      IAAACCCDDDDBMABJMMOPQJEEDINNQNNONOSSRM    ",
    "     JAAFFFFFFFFIMBHBMMMOQMAECDDBQQQOONOMMQM    ",
    "     JBBBBHHHHIMBDDFAMMMMJJHFDEDDQQQOODDAI      ",
    "     JBBAAAAAIMAADDFJMNNMJBHDDEEDAQQOHEEEF      ",
    "     JBBBBJJJNBHECDBMNNNMJIADDDDEDJJNEEDAA      ",
    "     JJBIJINNIFEHDFBMQQNJJAADDACCEAJAEFIJJ      ",
    "    NJJJJJNIBFHFCFAMMQQNJJBJDACCCEAJCFIMMM      ",
    "    NJNNNBBBIFFABJJMNQONJJJBFDCDCEMIFMINM       ",
    "    NJNJJBBAAAAAJBJNNQONMJJBDDDDCDMIIBBIM       ",
    "     NJJBBBBBBBJJJMNOPPNMJJJDDFEHFIMMAHFBI      ",
    "     JJJBBJJBBBBBMQNOSPNMMJJDFHHHFIIBHCCFI      ",
    "    MJJJJJJJJJMMQQQOPPPONMMJBNHAFFADCCEEED      ",
    "   NJJJJJJMMMM   QQOOOOONNMMJBHAAFACCCCCEE      ",
    "   MJJJJMM         NNOOONNNMJJIAAFADHCCDDD      ",
    "   MJJMM            MOQONMNNJJJAAIAFHHHHHH      ",
    "    M                  NNQQNMMJJBIABHHABAA      ",
    "                        QQQNNMJJJIAAHDAJAI      ",
    "                         QQNNMMJJBIABAAJJJ      ",
    "                          QNNMMMNJBJBABJJ       ",
    "                            NM  MJJJJAJJN       ",
    "                             M    NNJN          ",
    "                                    J           ",
    "                                                ",
    "                                                ",
]

# 0x0lor1n: hand-placed, 3/4 view facing the text, no face. Same rules the
# good hacker sprites share: 1px near-black outline, three tones of navy on
# the hoodie (back / mid / lit front) so the silhouette holds on the dark
# site background, and the terminal green as screen-light on the lower front
# of the hood rather than a rim around the outside. Lid of the laptop faces
# the reader, one pale logo.
OLORIN_PAL = {
    "O": (0x0A, 0x0A, 0x10),  # outline
    "1": (0x23, 0x25, 0x3C),  # hoodie, back / shadow
    "d": (0x17, 0x18, 0x28),  # fold in the hood
    "2": (0x34, 0x38, 0x56),  # hoodie, mid
    "3": (0x48, 0x4E, 0x74),  # hoodie, lit front
    "K": (0x06, 0x06, 0x0A),  # inside the hood
    "g": (0x1F, 0x8F, 0x28),  # screen-light, dim
    "G": (0x3C, 0xD6, 0x3A),  # screen-light, bright
    "l": (0x6B, 0x5C, 0x80),  # laptop lid
    "L": (0x9A, 0x8B, 0xB0),  # laptop edge highlight
    "W": (0xCF, 0xE6, 0xF3),  # logo
}
OLORIN = [
    "                                                ",
    "                                                ",
    "                   OOOO                         ",
    "                 OO1111OO                       ",
    "                O1d111111O                      ",
    "               O1d11111112O                     ",
    "              O1d1111111222O                    ",
    "             O1d111111122222O                   ",
    "            O1d11111112OOOO22O                  ",
    "            O1d1111112OKKKKKO2O                 ",
    "           O11d11111OKKKKKKKO22O                ",
    "           O1d11111OKKKKKKKKKO2O                ",
    "           O1d1111OKKKKKKKKKKO22O               ",
    "           O111111OKKKKKKKKKKKO2O               ",
    "           O111111OKKKKKKKKKKKO23O              ",
    "           O111111OKKKKKKKKKKKKO3O              ",
    "           O111111OKKKKKKKKKKKKO3O              ",
    "           O111112OKKKKKKKKKKKKO3O              ",
    "           O111112OKKKKKKKKKKKgO3O              ",
    "            O11122OKKKKKKKKKKgGOgO              ",
    "            O11122OKKKKKKKKKgGGOgO              ",
    "             O1122OKKKKKKKKgGGGOgO              ",
    "             O1122OKKKKKKKgGGGOgO               ",
    "              O122OKKKKKKgGGGOgO                ",
    "               O22OOOOOOOOOOO3gO                ",
    "          OO111222222222222333333OO             ",
    "        OO11112222222222222233333333OO          ",
    "      OO111112222222222222222333333333OO        ",
    "     O1111112222222222222222233333333333O       ",
    "    O11111122222222222222222233333333333O       ",
    "   O11111122222222222222222223333333333322O     ",
    "  O111111222222222222222222233333333333222O     ",
    "  O11111122222OOOOOOOOOOOOOOOOOOOO333333222O    ",
    "  O11111122222OLLLLLLLLLLLLLLLLLLO333333222O    ",
    "  O11111122222OLlllllllllllllllllO333333222O    ",
    "  O11111122222OLlllllllllllllllllO333333222O    ",
    "  O11111122222OLlllllllllllllllllO333333222O    ",
    "  O11111122222OLlllllllWWWlllllllO333333222O    ",
    "  O11111122222OLlllllllWWWlllllllO333333222O    ",
    "  O11111122222OLlllllllWWWlllllllO333333222O    ",
    "  O11111122222OLlllllllllllllllllO333333222O    ",
    "  O11111122222OLlllllllllllllllllO333333222O    ",
    "  O11111122222OLlllllllllllllllllO333333222O    ",
    "  O11111122222OLlllllllllllllllllO333333222O    ",
    "  O11111122222OOOOOOOOOOOOOOOOOOOO333333222O    ",
    "  O111111222LLLLLLLLLLLLLLLLLLLLLLL33333222O    ",
    "   OOOOOOOOOlllllllllllllllllllllllOOOOOOOOO    ",
    "                                                ",
]

SPRITES = {"kriton": (KRITON, KRITON_PAL), "olorin": (OLORIN, OLORIN_PAL)}


def to_image(grid, pal):
    """Smaller grids are centred on the SIZE canvas."""
    assert len(grid) <= SIZE, len(grid)
    w = max(len(r) for r in grid)
    ox, oy = (SIZE - w) // 2, (SIZE - len(grid)) // 2
    im = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = im.load()
    for y, row in enumerate(grid):
        row = row.ljust(w)
        assert len(row) <= SIZE, (y, len(row))
        for x, ch in enumerate(row):
            if ch != " ":
                px[ox + x, oy + y] = pal[ch] + (255,)
    return im


def main():
    root = Path(__file__).resolve().parent.parent
    out = root / "static" / "img"
    out.mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGBA", (SIZE * 4 * 2 + 48, SIZE * 4 + SIZE + 40), BG + (255,))
    for i, (name, (grid, pal)) in enumerate(SPRITES.items()):
        im = to_image(grid, pal)
        im.save(out / f"{name}.png", optimize=True)
        big = im.resize((SIZE * 4, SIZE * 4), Image.NEAREST)
        x = 16 + i * (SIZE * 4 + 16)
        sheet.alpha_composite(big, (x, 16))
        sheet.alpha_composite(im, (x, 16 + SIZE * 4 + 8))
        print(name, (out / f"{name}.png").stat().st_size, "bytes")
    sheet.save("/tmp/sprites-preview.png")


if __name__ == "__main__":
    main()
