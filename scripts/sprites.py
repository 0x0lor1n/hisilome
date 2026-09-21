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

# 0x0lor1n: pixel map lifted 1:1 from the green-hacker reference (44x41, centred
# on the 48x48 canvas). Black hooded silhouette, green hatching on hood and
# shoulders, empty black face, lilac laptop lid with a pale screen glow.
OLORIN_PAL = {
    "K": (0x0E, 0x0E, 0x0E),  # silhouette
    "G": (0x3C, 0xD6, 0x3A),  # green bright
    "g": (0x1F, 0x8F, 0x28),  # green dim
    "l": (0x6B, 0x5C, 0x80),  # laptop lid
    "L": (0x9A, 0x8B, 0xB0),  # laptop edge highlight
    "W": (0xCF, 0xE6, 0xF3),  # screen glow
}
OLORIN = [
    "                                            ",
    "                                            ",
    "                  KKgKKgKG                  ",
    "                 KgKKKgKgKG                 ",
    "                gKKKKKKKKgKG                ",
    "               gKKGKKGKKgKGKG               ",
    "               gKKKKKKKgKgKGG               ",
    "               gKKKKKKKKKKgKg               ",
    "              GKKKKKKgKKKKKKKG              ",
    "             GKKKKKKKKKKKKKKKK              ",
    "             GgKKKKKKKKKKKKKKG              ",
    "             GKKKgGGGGGGGGKKKK              ",
    "             GKKKKKKKKKKKKGKKK              ",
    "             GKKgKKKKKKKKKKGKK              ",
    "             GKgKKKKKKKKKKGKGK              ",
    "             GKKKKKKKKKKKKGKgg              ",
    "              GKKgKKKKKKKgKKKG              ",
    "              GKKgKKKKKKKgKKKG              ",
    "               gKKGKKKKKgKKKG               ",
    "              GKgKKGKKKKKKKGKG              ",
    "           GggKggKKKgGGgKKKggKgg            ",
    "         GgKgKgKKgKKKKKKKKgKKggKgGg         ",
    "        gKKgKgKKKgKKKKKKKgKKgKgKKgKg        ",
    "      GKgKKKKKKKKKKKKKKKgKKKKKgKgKKggG      ",
    "      KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKg      ",
    "     GKGKKLllllllllllllLlllLLlllLKKKKK      ",
    "    GKKKKKllllllllllllllllllllllllKKKKg     ",
    "    GKKKKKllllllllllllllllllllllllKKKKg     ",
    "   lKKKKKKlllllllllllllllllllllllLKKKKKg    ",
    "    KKKKKKllllllllllllllllllllllllKKKKKK    ",
    "   KKKKKKKlllllllllllllllllllllllLKKKKKKK   ",
    "  KKKKKKKKllllllllllWWWlllllllllllKKKKKKKK  ",
    "  KKKKKKKKllllllllllWWWlllllllllllKKKKKKKK  ",
    " KKKKKKKKKllllllllllWWWlllllllllllKKKKKKKKK ",
    " KKgGGKKKKllllllllllllllllllllllllKKKKGGKKK ",
    " KKKgKgGgKllllllllllllllllllllllllKgGggKgKK ",
    "KKKKKgKgKKlllllllllllllllllllllllLKKgKKKKKKK",
    "KKKKKKKKKKllllllllllllllllllllllllKKKKKKKKKK",
    "KKKKKKKKKKllllllllllllllllllllllllKKKKKKKKKK",
    " KKKKKKKKKllllllllllllllllllllllllKKKKKKKKK ",
    "   KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK   ",
    "      KKKKlllllllllllllllllllllllKKKKl      ",
    "           lllllllllllllllllllllll          ",
    "                                            ",
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
