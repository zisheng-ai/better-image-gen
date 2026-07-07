# Mac Dynamic Wallpaper — Generation & Packaging

2-frame HEIC with `apple_desktop:apr` metadata. macOS switches frames automatically when the user toggles Light/Dark mode in System Settings > Appearance.

**Tool stack (no Homebrew needed):**
- `pillow-heif` 1.1.1 — handles HEIC read/write + XMP
- `plistlib` + `base64` — standard library

---

## Setup Check

```bash
python3 -c "import pillow_heif; print('OK', pillow_heif.__version__)" || \
  pip3 install pillow-heif -q
```

---

## Frame Strategy

| Frame index | Mode | Lighting |
|-------------|------|----------|
| 0 | Light (白天) | Daytime, bright, vivid colors |
| 1 | Dark (夜间) | Night, moonlit, bioluminescent or dark atmosphere |

---

## Prompt Template

```bash
THEME="<user's wallpaper subject>"

PROMPT_LIGHT="${THEME}, bright daytime lighting, vivid colors, clear sky, no text, no watermark"
PROMPT_DARK="${THEME}, deep night, moonlit, dark atmosphere, bioluminescent glow, no text, no watermark"
```

---

## Generation — 2 Frames in Parallel

```bash
OUT_DIR="$HOME/Pictures/better-image-gen/dynamic-wallpaper"
mkdir -p "$OUT_DIR"

(
  export PROMPT="$PROMPT_LIGHT"
  OUTPUT_PATH="/tmp/dw_light.png"
  if   GEN_LOG=$(gen_image_apiyi "$MODEL_GPT" "3840x2160" "$OUTPUT_PATH"); then MODEL_USED="$MODEL_GPT"; SIZE="3840x2160"
  elif GEN_LOG=$(gen_image_apiyi "$MODEL_GPT" "3840x2160" "$OUTPUT_PATH"); then MODEL_USED="$MODEL_GPT"; SIZE="3840x2160"
  else echo "⚠ light — all failed"; exit 1; fi
  GENERATION_MS=$(printf '%s\n' "$GEN_LOG" | awk -F: '/^ELAPSED_MS:/{v=$2} END{print v+0}')
  RESPONSE_FORMAT=$(printf '%s\n' "$GEN_LOG" | awk -F: '/^RESPONSE_FORMAT:/{v=$2} END{print v}')
  write_image_metadata "$OUTPUT_PATH" "$OUT_DIR/light-frame.json" "$MODEL_USED" "$SIZE" "$GENERATION_MS" "$RESPONSE_FORMAT" "dynamic wallpaper light frame png"
  echo "✓ light — $MODEL_USED"
) > /tmp/dw_log_light.log 2>&1 &

(
  export PROMPT="$PROMPT_DARK"
  OUTPUT_PATH="/tmp/dw_dark.png"
  if   GEN_LOG=$(gen_image_apiyi "$MODEL_GPT" "3840x2160" "$OUTPUT_PATH"); then MODEL_USED="$MODEL_GPT"; SIZE="3840x2160"
  elif GEN_LOG=$(gen_image_apiyi "$MODEL_GPT" "3840x2160" "$OUTPUT_PATH"); then MODEL_USED="$MODEL_GPT"; SIZE="3840x2160"
  else echo "⚠ dark — all failed"; exit 1; fi
  GENERATION_MS=$(printf '%s\n' "$GEN_LOG" | awk -F: '/^ELAPSED_MS:/{v=$2} END{print v+0}')
  RESPONSE_FORMAT=$(printf '%s\n' "$GEN_LOG" | awk -F: '/^RESPONSE_FORMAT:/{v=$2} END{print v}')
  write_image_metadata "$OUTPUT_PATH" "$OUT_DIR/dark-frame.json" "$MODEL_USED" "$SIZE" "$GENERATION_MS" "$RESPONSE_FORMAT" "dynamic wallpaper dark frame png"
  echo "✓ dark — $MODEL_USED"
) > /tmp/dw_log_dark.log 2>&1 &

wait
cat /tmp/dw_log_light.log /tmp/dw_log_dark.log
rm -f /tmp/dw_log_*.log
[ -f /tmp/dw_light.png ] && [ -f /tmp/dw_dark.png ] || { echo "DYNAMIC_WALLPAPER_FRAME_MISSING"; exit 1; }
```

**Special case — user provides an existing image as one frame:**
```bash
python3 -c "from PIL import Image; Image.open('/path/to/existing.webp').convert('RGB').save('/tmp/dw_light.png')"
# then only generate the missing frame
```

---

## Packaging — 2 PNG → HEIC with apr Metadata

```python
#!/usr/bin/env python3
import plistlib, base64, os
from PIL import Image
import pillow_heif

pillow_heif.register_heif_opener()

light_path = "/tmp/dw_light.png"
dark_path  = "/tmp/dw_dark.png"
output = os.path.expanduser("~/Pictures/better-image-gen/dynamic-wallpaper/wallpaper-apr.heic")
os.makedirs(os.path.dirname(output), exist_ok=True)

light = Image.open(light_path).convert("RGB")
dark  = Image.open(dark_path).convert("RGB")
if dark.size != light.size:
    dark = dark.resize(light.size, Image.LANCZOS)

# apr plist: root-level {l, d} — confirmed by reverse-engineering Sonoma.heic
plist_data = plistlib.dumps({"l": 0, "d": 1}, fmt=plistlib.FMT_BINARY)
apr_b64 = base64.b64encode(plist_data).decode()

# XMP in attribute form — matches Apple's format exactly
xmp = (
    '<?xpacket begin="\xef\xbb\xbf" id="W5M0MpCehiHzreSzNTczkc9d"?>'
    ' <x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="XMP Core 6.0.0">'
    ' <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
    ' <rdf:Description rdf:about=""'
    ' xmlns:apple_desktop="http://ns.apple.com/namespace/1.0/"'
    f' apple_desktop:apr="{apr_b64}">'
    ' </rdf:Description>'
    ' </rdf:RDF>'
    ' </x:xmpmeta>'
    ' <?xpacket end="w"?>'
)

light.save(output, format="HEIF", save_all=True, append_images=[dark], xmp=xmp.encode())
print(f"✓ {output}  ({os.path.getsize(output)//1024} KB)")
```

Write packaging metadata:
```bash
PROMPT="$THEME"
write_image_metadata "$OUT_DIR/wallpaper-apr.heic" "$OUT_DIR/wallpaper-apr.json" "packaged-heic" "2-frame-apr" 0 "local-packaging" "2-frame HEIC with apple_desktop:apr metadata"
print_image_summary "$OUT_DIR/light-frame.json" "$OUT_DIR/dark-frame.json" "$OUT_DIR/wallpaper-apr.json"
```

Clean up:
```bash
rm -f /tmp/dw_light.png /tmp/dw_dark.png
```

---

## Set as Wallpaper

```bash
osascript -e "tell application \"Finder\" to set desktop picture to POSIX file \"$HOME/Pictures/better-image-gen/dynamic-wallpaper/wallpaper-apr.heic\""
```

Wallpaper switches automatically with Light/Dark mode. No further action needed.

---

## Full Pipeline Summary

```
1. Load generation.md → model alias resolution
2. Build THEME → PROMPT_LIGHT + PROMPT_DARK
3. gen_image_apiyi × 2 in parallel → /tmp/dw_light.png + /tmp/dw_dark.png
   (if user provides an image, convert it and skip that API call)
4. Run Python packaging script → ~/Pictures/better-image-gen/dynamic-wallpaper/wallpaper-apr.heic
5. osascript to set as wallpaper
6. Tell user: switches with Light/Dark mode toggle in System Settings > Appearance
```

**Cost:** 2 × GPT Image 2 API calls.

---

## Output Convention

- **Format:** `.heic` (2-frame HEIF)
- **No WebP conversion**
- **Location:** `~/Pictures/better-image-gen/dynamic-wallpaper/wallpaper-apr.heic`
