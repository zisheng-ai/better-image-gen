#!/usr/bin/env python3
"""Remove a solid edge-connected background and fail unless alpha is real."""
from collections import deque
from pathlib import Path
import argparse
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument("input")
parser.add_argument("output")
parser.add_argument("--tolerance", type=int, default=42)
parser.add_argument("--edge-mode", choices=("pixel", "soft"), default="soft")
parser.add_argument("--softness", type=int, default=28)
args = parser.parse_args()

im = Image.open(args.input).convert("RGBA")
w, h = im.size
px = im.load()
corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
references = [(r, g, b) for r, g, b, _ in corners]

def is_background(value):
    r, g, b, a = value
    if a == 0:
        return True
    return min((r-r0)**2 + (g-g0)**2 + (b-b0)**2 for r0, g0, b0 in references) <= args.tolerance**2

queue = deque()
seen = set()
for x in range(w):
    queue.extend(((x, 0), (x, h - 1)))
for y in range(h):
    queue.extend(((0, y), (w - 1, y)))
while queue:
    x, y = queue.popleft()
    if (x, y) in seen or not is_background(px[x, y]):
        continue
    seen.add((x, y))
    px[x, y] = (0, 0, 0, 0)
    for nx, ny in ((x+1,y), (x-1,y), (x,y+1), (x,y-1)):
        if 0 <= nx < w and 0 <= ny < h:
            queue.append((nx, ny))

# Natural hair/fur needs a narrow fractional-alpha transition. Pixel art must
# retain exact hard edges, so callers opt into `pixel` mode for sprites/badges.
if args.edge_mode == "soft":
    alpha = im.getchannel("A")
    apx = alpha.load()
    original = Image.open(args.input).convert("RGBA")
    opx = original.load()
    for y in range(h):
        for x in range(w):
            if apx[x, y] == 0:
                continue
            if not any(0 <= nx < w and 0 <= ny < h and apx[nx, ny] == 0
                       for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1))):
                continue
            r, g, b, old_a = opx[x, y]
            distance = min(((r-r0)**2 + (g-g0)**2 + (b-b0)**2) ** 0.5 for r0, g0, b0 in references)
            lo, hi = args.tolerance, args.tolerance + args.softness
            if distance < hi:
                apx[x, y] = int(old_a * max(0.0, min(1.0, (distance-lo) / max(1, hi-lo))))

alpha = im.getchannel("A")
transparent = sum(1 for value in alpha.getdata() if value == 0)
ratio = transparent / (w * h)
if any(alpha.getpixel(point) != 0 for point in ((0,0),(w-1,0),(0,h-1),(w-1,h-1))):
    raise SystemExit("transparency validation failed: opaque corner remains")
if ratio < 0.08:
    raise SystemExit(f"transparency validation failed: only {ratio:.1%} transparent pixels")
bbox = alpha.getbbox()
if not bbox:
    raise SystemExit("transparency validation failed: subject was removed")
Path(args.output).parent.mkdir(parents=True, exist_ok=True)
im.save(args.output)
print(f"TRANSPARENCY_OK:{ratio:.1%}:{bbox}")
