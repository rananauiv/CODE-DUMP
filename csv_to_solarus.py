#!/usr/bin/env python3
"""Convert Tiled CSV layer exports into a Solarus map .dat file.

Edit the SETTINGS block below, then just run:  python csv_to_solarus.py
(Command-line arguments still work and override the settings if you give them.)
"""
import argparse
import csv
import json

# =====================================================================
# SETTINGS - EDIT THESE
# =====================================================================

# INPUT: Tiled CSV files, one per tile layer, bottom layer first.
# First file = Solarus layer 0, second = layer 1, and so on.
INPUT_CSV_FILES = [
    r"C:\path\to\ground.csv",
    # r"C:\path\to\decor.csv",
]

# OUTPUT: where the Solarus map .dat file gets written.
OUTPUT_DAT_FILE = r"C:\path\to\data\maps\0001.dat"

# Solarus tileset id this map uses (name of your tileset in data/tilesets/).
TILESET_ID = "forest"

# Pixel size of one tile.
TILE_SIZE = 16

# Optional: JSON file mapping Tiled tile id -> Solarus pattern id,
# e.g. {"0": "grass", "1": "water"}. Set to None to skip.
MAPPING_JSON_FILE = None  # e.g. r"C:\path\to\mapping.json"

# Unmapped tile ids become PATTERN_PREFIX + id (e.g. "tile_5").
PATTERN_PREFIX = "tile_"

# =====================================================================
# END OF SETTINGS
# =====================================================================

FLIP_MASK = 0x1FFFFFFF  # Tiled stores flips in the top bits of the id


def read_grid(path):
    with open(path, newline="") as f:
        return [[int(c) for c in row if c.strip() != ""] for row in csv.reader(f) if row]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv", nargs="*", help="CSV files (overrides INPUT_CSV_FILES)")
    ap.add_argument("-o", "--out", default=OUTPUT_DAT_FILE, help="output .dat path")
    ap.add_argument("--tileset", default=TILESET_ID)
    ap.add_argument("--tile-size", type=int, default=TILE_SIZE)
    ap.add_argument("--mapping", default=MAPPING_JSON_FILE)
    ap.add_argument("--prefix", default=PATTERN_PREFIX)
    args = ap.parse_args()
    csv_files = args.csv or INPUT_CSV_FILES

    mapping = {}
    if args.mapping:
        with open(args.mapping) as f:
            mapping = {str(k): v for k, v in json.load(f).items()}

    ts = args.tile_size
    grids = [read_grid(p) for p in csv_files]
    rows = max(len(g) for g in grids)
    cols = max(len(r) for g in grids for r in g)

    out = [
        "properties{",
        "  x = 0,",
        "  y = 0,",
        f"  width = {cols * ts},",
        f"  height = {rows * ts},",
        f'  tileset = "{args.tileset}",',
        "}",
        "",
    ]

    flipped = 0
    for layer, grid in enumerate(grids):
        for y, row in enumerate(grid):
            x = 0
            while x < len(row):
                raw = row[x]
                if raw < 0:
                    x += 1
                    continue
                tid = raw & FLIP_MASK
                if raw != tid:
                    flipped += 1
                run = 1
                while x + run < len(row) and row[x + run] >= 0 and (row[x + run] & FLIP_MASK) == tid:
                    run += 1
                pattern = mapping.get(str(tid), f"{args.prefix}{tid}")
                out.append(
                    f'tile{{ layer = {layer}, x = {x * ts}, y = {y * ts}, '
                    f'width = {run * ts}, height = {ts}, pattern = "{pattern}" }}'
                )
                x += run

    with open(args.out, "w") as f:
        f.write("\n".join(out) + "\n")

    tile_count = sum(1 for line in out if line.startswith("tile{"))
    print("INPUT")
    for i, path in enumerate(csv_files):
        g = grids[i]
        print(f"  CSV {i + 1} -> layer {i}: {path} ({len(g[0]) if g else 0}x{len(g)} cells)")
    print(f"  tileset:    {args.tileset}")
    print(f"  tile size:  {ts}px")
    print(f"  mapping:    {args.mapping or '(none, using prefix ' + repr(args.prefix) + ')'}")
    print("OUTPUT")
    print(f"  file:       {args.out}")
    print(f"  map size:   {cols * ts}x{rows * ts}px ({cols}x{rows} tiles)")
    print(f"  layers:     {len(grids)}")
    print(f"  tile{{}} entries written: {tile_count}")
    if flipped:
        print(f"Warning: {flipped} flipped/rotated tile(s) had their flips dropped.")


if __name__ == "__main__":
    main()
