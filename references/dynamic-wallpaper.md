# Mac Dynamic Wallpaper — Generation & Packaging

Two supported modes:

| Mode | Frames | Trigger | macOS support |
|------|--------|---------|---------------|
| **apr** (推荐) | 2 | 系统亮/暗模式切换 | ✅ Sonoma 完全支持 |
| h24 | 8 | 时间（每3小时切换）| ⚠️ Sonoma 上不生效，已知问题 |

**默认用 apr。** h24 在 macOS Sonoma 上已失效（Apple 把时间型动态壁纸迁移到私有 `.madesktop` 格式），不再支持用户自制。

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

## Mode 1 — apr (Light / Dark，推荐)

Generate **2 frames**: one for light mode, one for dark mode.

### Frame Strategy

| Frame index | Mode | Lighting |
|-------------|------|----------|
| 0 | Light (白天) | Daytime, bright, vivid colors |
| 1 | Dark (夜间) | Night, moonlit, bioluminescent or dark atmosphere |

### Prompt Template

```bash
THEME="<user's wallpaper subject>"

PROMPT_LIGHT="${THEME}, bright daytime lighting, vivid colors, clear sky, no text, no watermark"
PROMPT_DARK="${THEME}, deep night, moonlit, dark atmosphere, bioluminescent glow, no text, no watermark"
```

### Generation — 2 Frames in Parallel

```bash
OUT_DIR="$HOME/.zisheng-ai/dynamic-wallpaper"
mkdir -p "$OUT_DIR"

(
  export PROMPT="$PROMPT_LIGHT"
  OUTPUT_PATH="/tmp/dw_light.png"
  if   gen_image_apiyi "$MODEL_GPT"    "3840x2160" "$OUTPUT_PATH"; then echo "✓ light (gpt)"
  elif gen_image_apiyi "$MODEL_DOUBAO" "2560x1600" "$OUTPUT_PATH"; then echo "✓ light (doubao)"
  elif gen_image_apiyi "$MODEL_NANO"   "1280x720"  "$OUTPUT_PATH"; then sips -z 1600 2560 "$OUTPUT_PATH" >/dev/null; echo "✓ light (nano)"
  else echo "⚠ light — all failed"; fi
) > /tmp/dw_log_light.log 2>&1 &

(
  export PROMPT="$PROMPT_DARK"
  OUTPUT_PATH="/tmp/dw_dark.png"
  if   gen_image_apiyi "$MODEL_GPT"    "3840x2160" "$OUTPUT_PATH"; then echo "✓ dark (gpt)"
  elif gen_image_apiyi "$MODEL_DOUBAO" "2560x1600" "$OUTPUT_PATH"; then echo "✓ dark (doubao)"
  elif gen_image_apiyi "$MODEL_NANO"   "1280x720"  "$OUTPUT_PATH"; then sips -z 1600 2560 "$OUTPUT_PATH" >/dev/null; echo "✓ dark (nano)"
  else echo "⚠ dark — all failed"; fi
) > /tmp/dw_log_dark.log 2>&1 &

wait
cat /tmp/dw_log_light.log /tmp/dw_log_dark.log
rm -f /tmp/dw_log_*.log
```

**Special case — user provides an existing image as one frame:**
Convert it to PNG and skip that API call:
```bash
python3 -c "from PIL import Image; Image.open('/path/to/existing.webp').convert('RGB').save('/tmp/dw_light.png')"
# then only generate the missing frame
```

### Packaging — 2 PNG → HEIC with apr Metadata

```python
#!/usr/bin/env python3
import plistlib, base64, os
from PIL import Image
import pillow_heif

pillow_heif.register_heif_opener()

light_path = "/tmp/dw_light.png"
dark_path  = "/tmp/dw_dark.png"
output = os.path.expanduser("~/.zisheng-ai/dynamic-wallpaper/wallpaper-apr.heic")
os.makedirs(os.path.dirname(output), exist_ok=True)

# Unify size (resize dark to match light)
light = Image.open(light_path).convert("RGB")
dark  = Image.open(dark_path).convert("RGB")
if dark.size != light.size:
    dark = dark.resize(light.size, Image.LANCZOS)

# apr plist: frame 0 = light, frame 1 = dark
plist_data = plistlib.dumps({"ap": {"l": 0, "d": 1}}, fmt=plistlib.FMT_BINARY)
apr_b64 = base64.b64encode(plist_data).decode()

# XMP — attribute form (matches Apple's format exactly)
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
kb = os.path.getsize(output) // 1024
print(f"✓ {output}  (2 frames, {kb} KB)")
```

Clean up:
```bash
rm -f /tmp/dw_light.png /tmp/dw_dark.png
```

### Set as Wallpaper

```bash
osascript -e "tell application \"Finder\" to set desktop picture to POSIX file \"$HOME/.zisheng-ai/dynamic-wallpaper/wallpaper-apr.heic\""
```

After setting, the wallpaper switches automatically when the user toggles Light/Dark mode in System Settings > Appearance.

---

## Mode 2 — h24 (Time-based，Sonoma 上不生效)

> ⚠️ **macOS Sonoma 已不支持用户自制 h24 HEIC 动态壁纸。** Apple 从 Ventura 起将时间型动态壁纸迁移至私有 `.madesktop` 格式，h24 HEIC 在 Sonoma 上只显示第一帧（静态），不会按时切换。保留此文档供参考，不要在 Sonoma 上使用。

### Frame Strategy (8 frames, 24 hours)

| Frame | Time  | t value | Light condition |
|-------|-------|---------|-----------------|
| 0     | 00:00 | 0.0     | Deep night, moonlit, stars |
| 1     | 03:00 | 0.125   | Pre-dawn blue-black |
| 2     | 06:00 | 0.25    | Sunrise, warm gold horizon |
| 3     | 09:00 | 0.375   | Bright morning, soft shadows |
| 4     | 12:00 | 0.5     | Midday, harsh overhead light |
| 5     | 15:00 | 0.625   | Warm afternoon, long shadows |
| 6     | 18:00 | 0.75    | Golden hour, sunset |
| 7     | 21:00 | 0.875   | Blue hour, twilight |

### Packaging (h24)

```python
import plistlib, base64, os
from PIL import Image
import pillow_heif

pillow_heif.register_heif_opener()

frame_paths = [f"/tmp/dw_frame_{i}.png" for i in range(8)]
output = os.path.expanduser("~/.zisheng-ai/dynamic-wallpaper/wallpaper-h24.heic")

n = len(frame_paths)
si = [{"i": i, "t": round(i / n, 8)} for i in range(n)]
plist_data = plistlib.dumps({"ap": {"l": 4, "d": 0}, "si": si}, fmt=plistlib.FMT_BINARY)
h24_b64 = base64.b64encode(plist_data).decode()

xmp = (
    '<?xpacket begin="\xef\xbb\xbf" id="W5M0MpCehiHzreSzNTczkc9d"?>'
    ' <x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="XMP Core 6.0.0">'
    ' <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
    ' <rdf:Description rdf:about=""'
    ' xmlns:apple_desktop="http://ns.apple.com/namespace/1.0/"'
    f' apple_desktop:h24="{h24_b64}">'
    ' </rdf:Description>'
    ' </rdf:RDF>'
    ' </x:xmpmeta>'
    ' <?xpacket end="w"?>'
)

images = [Image.open(p).convert("RGB") for p in frame_paths]
images[0].save(output, format="HEIF", save_all=True, append_images=images[1:], xmp=xmp.encode())
print(f"✓ {output}  ({n} frames)")
```

---

## Full Pipeline Summary (apr)

```
1. Load generation.md → model alias resolution
2. Build THEME → PROMPT_LIGHT + PROMPT_DARK
3. gen_image_apiyi × 2 in parallel → /tmp/dw_light.png + /tmp/dw_dark.png
   (if user provides an existing image, convert it and skip that API call)
4. Run Python packaging script → ~/.zisheng-ai/dynamic-wallpaper/wallpaper-apr.heic
5. osascript to set as wallpaper
6. Tell user: switches automatically with Light/Dark mode toggle
```

**Cost estimate:** 2 × GPT Image 2 ≈ 2 API calls.

---

## Output Convention

- **Format:** `.heic` (HEIF multi-image)
- **No WebP conversion** — HEIC is the deliverable
- **Location:** `~/.zisheng-ai/dynamic-wallpaper/wallpaper-apr.heic`
