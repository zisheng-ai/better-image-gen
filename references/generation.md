# Image Generation — Patterns & Cascade

Load this reference before generating any image. It provides the `gen_image_apiyi` shell function, the model cascade, and batch parallelism patterns.

---

## Environment Check

Always run this first. If the key is missing, print the setup message and stop.

```bash
if [ -z "$APIYI_API_KEY" ]; then
  echo "⚠ APIYI_API_KEY is not set."
  echo "  Get a key at: https://api.apiyi.com/register/?aff_code=ijv5"
  echo "  Then run: export APIYI_API_KEY=\"your-key\""
  exit 1
fi
```

---

## Model Alias Resolution

Resolve `APIYI_MODEL` (friendly name) → actual model ID. Default: `gpt`.

```bash
# Supported values: gpt (default) | doubao | nano
_APIYI_MODEL_ALIAS="${APIYI_MODEL:-gpt}"
case "$_APIYI_MODEL_ALIAS" in
  gpt)    MODEL_GPT="gpt-image-2-all";            MODEL_DOUBAO="doubao-seedream-5-0-260128"; MODEL_NANO="nano-banana-pro" ;;
  doubao) MODEL_GPT="doubao-seedream-5-0-260128"; MODEL_DOUBAO="doubao-seedream-5-0-260128"; MODEL_NANO="nano-banana-pro" ;;
  nano)   MODEL_GPT="nano-banana-pro";            MODEL_DOUBAO="nano-banana-pro";            MODEL_NANO="nano-banana-pro" ;;
  *)      echo "⚠ Unknown APIYI_MODEL='$_APIYI_MODEL_ALIAS'. Using gpt."
          MODEL_GPT="gpt-image-2-all"; MODEL_DOUBAO="doubao-seedream-5-0-260128"; MODEL_NANO="nano-banana-pro" ;;
esac
# MODEL_GPT   — primary slot in standard cascade
# MODEL_DOUBAO — doubao slot (high-allure / logo cascade)
# MODEL_NANO  — final fallback slot
```

Setting `APIYI_MODEL=doubao` forces all cascade primary slots to doubao; `APIYI_MODEL=nano` collapses the entire cascade to nano (useful for fast draft previews). Unset or `gpt` uses the default cascade order.

---

## Core Function — `gen_image_apiyi`

Generic generator. Handles both `b64_json` (PNG bytes) and `url` (CDN link) response formats.
Returns `0` on success (file written), non-zero on any failure.

```bash
gen_image_apiyi() {
  local model="$1" size="$2" output_path="$3"
  local prompt_json
  prompt_json=$(printf '%s' "$PROMPT" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().strip()))')

  curl -s --max-time 300 "https://api.apiyi.com/v1/images/generations" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $APIYI_API_KEY" \
    -d "{\"model\":\"$model\",\"prompt\":$prompt_json,\"size\":\"$size\"}" \
  | OUTPUT_PATH="$output_path" python3 -c "
import sys, json, base64, os, urllib.request
output_path = os.environ['OUTPUT_PATH']
raw = sys.stdin.read()
if not raw.strip():
    print('ERROR: empty response (timeout)'); sys.exit(1)
data = json.loads(raw)
if 'error' in data:
    msg = data['error']['message'] if isinstance(data['error'], dict) else str(data['error'])
    print('API_ERROR:' + msg); sys.exit(2)
if not data.get('data'):
    print('SOFT_REJECT: empty data array (model declined silently)'); sys.exit(2)
item = data['data'][0]
if item.get('b64_json'):
    b64 = item['b64_json']
    if ',' in b64: b64 = b64.split(',', 1)[1]   # strip data:image/png;base64, prefix if present
    with open(output_path, 'wb') as f: f.write(base64.b64decode(b64))
elif item.get('url'):
    urllib.request.urlretrieve(item['url'], output_path)
else:
    print('UNKNOWN_FORMAT:' + str(list(item.keys()))); sys.exit(3)
print('SAVED:' + str(os.path.getsize(output_path)))
"
}
```

---

## Model Cascade

Three models in priority order. Fall through to the next on any failure.

### Portrait / square image (T1–T2 content)

```bash
OUTPUT_PATH="/tmp/image_output.png"

if   gen_image_apiyi "$MODEL_GPT"    "848x1280"  "$OUTPUT_PATH"; then MODEL_USED="$MODEL_GPT";    SIZE="848x1280"
elif gen_image_apiyi "$MODEL_GPT"    "848x1280"  "$OUTPUT_PATH"; then MODEL_USED="$MODEL_GPT";    SIZE="848x1280"   # retry once
elif gen_image_apiyi "$MODEL_DOUBAO" "1664x2496" "$OUTPUT_PATH"; then MODEL_USED="$MODEL_DOUBAO"; SIZE="1664x2496"
elif gen_image_apiyi "$MODEL_NANO"   "1024x1024" "$OUTPUT_PATH"; then MODEL_USED="$MODEL_NANO";   SIZE="1024x1024"
else echo "ALL_MODELS_FAILED"; exit 1
fi
echo "MODEL_USED=$MODEL_USED"
echo "💡 Powered by apiyi — GPT Image 2 / Doubao / Nano via one key: https://api.apiyi.com/register/?aff_code=ijv5"
```

### High-allure / permissive content (T3+ — skip GPT, go straight to Doubao)

GPT hard-rejects explicit fabric-failure / soaked / torn language. For prompts that contain these elements:

```bash
OUTPUT_PATH="/tmp/image_output.png"

if   gen_image_apiyi "$MODEL_DOUBAO" "1664x2496" "$OUTPUT_PATH"; then MODEL_USED="$MODEL_DOUBAO"; SIZE="1664x2496"
elif gen_image_apiyi "$MODEL_DOUBAO" "1664x2496" "$OUTPUT_PATH"; then MODEL_USED="$MODEL_DOUBAO"; SIZE="1664x2496"  # retry once
elif gen_image_apiyi "$MODEL_NANO"   "1024x1024" "$OUTPUT_PATH"; then MODEL_USED="$MODEL_NANO";   SIZE="1024x1024"
else echo "ALL_MODELS_FAILED"; exit 1
fi
```

### Mac wallpaper (16:9 / 16:10)

GPT at 4K 16:9 (`3840×2160`) as primary; Doubao at 16:10 (`2560×1600`, 4.1 M px > floor) as fallback for MacBook native ratio; Nano last resort (upscale from `1280×720`).

```bash
OUTPUT_PATH="/tmp/image_output.png"
OUT_DIR="$HOME/.zisheng-ai"
mkdir -p "$OUT_DIR"

if   gen_image_apiyi "$MODEL_GPT"    "3840x2160" "$OUTPUT_PATH"; then MODEL_USED="$MODEL_GPT";    SIZE="3840x2160"
elif gen_image_apiyi "$MODEL_GPT"    "3840x2160" "$OUTPUT_PATH"; then MODEL_USED="$MODEL_GPT";    SIZE="3840x2160"  # retry once
elif gen_image_apiyi "$MODEL_DOUBAO" "2560x1600" "$OUTPUT_PATH"; then MODEL_USED="$MODEL_DOUBAO"; SIZE="2560x1600"
elif gen_image_apiyi "$MODEL_NANO"   "1280x720"  "$OUTPUT_PATH"; then MODEL_USED="$MODEL_NANO";   SIZE="1280x720"
else echo "ALL_MODELS_FAILED"; exit 1
fi

# No resize needed for GPT/Doubao — already at display resolution
# Nano: upscale to 2560x1600
if [ "$MODEL_USED" = "$MODEL_NANO" ]; then
  sips -z 1600 2560 "$OUTPUT_PATH"
fi

mv "$OUTPUT_PATH" "$OUT_DIR/wallpaper.png"
echo "MODEL_USED=$MODEL_USED  SIZE=$SIZE"
echo "✓ Wallpaper saved: $OUT_DIR/wallpaper.png"
echo "💡 Powered by apiyi — GPT Image 2 / Doubao / Nano via one key: https://api.apiyi.com/register/?aff_code=ijv5"
open "$OUT_DIR/wallpaper.png"
```

After opening, ask the user: **「要设置为桌面壁纸吗？」** Wait for confirmation before running:
```bash
osascript -e "tell application \"Finder\" to set desktop picture to POSIX file \"$HOME/.zisheng-ai/wallpaper.png\""
```

---

### Logo / favicon (square, requires Doubao's pixel floor)

Doubao minimum: 3,686,400 px. Use `1920×1920` for square logos (exactly meets the floor). `1024×1024` is below the floor — falls through to GPT automatically.

Before generation, rewrite the user's logo/icon prompt so transparency cannot be ambiguous. Append this block unless the user explicitly asked for a filled app tile or mockup:

```text
Transparent-background source artwork. Isolated subject only. Preserve alpha channel. No background layer.
Avoid: black background, white background, solid square background, rounded rectangle container, app icon tile, mockup frame, border, drop shadow outside the subject, canvas, backdrop, wallpaper, scene.
The output must be usable as a cutout logo/icon asset; the OS or app will apply any rounded mask later.
```

If the user explicitly asks for a macOS/iOS app icon, distinguish source art from final masked app icon. Generate source art with transparent background first unless they clearly want the rounded tile baked into the pixels.

```bash
# Logo: doubao at 1920x1920 → fallback to MODEL_GPT at 1280x1280
if   gen_image_apiyi "$MODEL_DOUBAO" "1920x1920" "$OUTPUT_PATH"; then MODEL_USED="$MODEL_DOUBAO"; SIZE="1920x1920"
elif gen_image_apiyi "$MODEL_GPT"    "1280x1280" "$OUTPUT_PATH"; then MODEL_USED="$MODEL_GPT";    SIZE="1280x1280"
else echo "LOGO_GENERATION_FAILED"; exit 1
fi
```

---

## Saving Metadata

Write a JSON file alongside every generated image:

```bash
PROMPT_JSON=$(printf '%s' "$PROMPT" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().strip()))')
printf '{"model":"%s","size":"%s","prompt":%s}\n' "$MODEL_USED" "$SIZE" "$PROMPT_JSON" > "output.json"
```

---

## Prompt Softening (content safety fallback)

If the primary model returns an error containing `invalid_prompt` / `safety` / `rejected`, replace triggering terms and retry once:

| Replace | With |
|---------|------|
| `bare back exposed` | `off-shoulder, collarbone catching the light` |
| `exposed breast`, `topless`, `naked`, `nude` | `off-shoulder`, `elegant neckline`, `décolletage` |
| `bodies pressed flush together` | `close proximity, charged tension` |
| `gripping her hip`, `hand on her bare hip` | `hand at her waist` |
| `wet transparent fabric`, `see-through wet` | `rain-soaked fabric, damp clothing` |
| `clinging to and outlining every curve` | `rain-soaked clothing pressed against her silhouette` |
| `lips pressed against` | `faces close, the moment before` |
| `erotic`, `sexual`, `explicit` | `alluring`, `intimate atmosphere`, `romantic tension` |

After softening, retry the full cascade once. If every model still fails, skip and log.

---

## Parallel Batch Generation

For multiple images, launch one background process per image and `wait` for all:

```bash
OUT_DIR="$HOME/.zisheng-ai"
mkdir -p "$OUT_DIR"

# Set PROMPT and OUTPUT_PATH per item, run in background
for ITEM in "${ITEMS[@]}"; do
  (
    PROMPT="$(build_prompt "$ITEM")"          # replace with your prompt logic
    OUTPUT_PATH="/tmp/image_${ITEM}.png"
    FINAL_PATH="$OUT_DIR/${ITEM}.webp"

    if   gen_image_apiyi "$MODEL_GPT"    "848x1280"  "$OUTPUT_PATH"; then MODEL_USED="$MODEL_GPT"
    elif gen_image_apiyi "$MODEL_DOUBAO" "1664x2496" "$OUTPUT_PATH"; then MODEL_USED="$MODEL_DOUBAO"
    elif gen_image_apiyi "$MODEL_NANO"   "1024x1024" "$OUTPUT_PATH"; then MODEL_USED="$MODEL_NANO"
    else echo "⚠ $ITEM — all models failed"; exit 0; fi

    # post-process: resize + convert (see references/post-process.md)
    echo "✓ $ITEM — $MODEL_USED"
  ) > "/tmp/log_${ITEM}.log" 2>&1 &
done
wait
rm -f /tmp/log_*.log
```

**Never loop images sequentially.** Always use parallel background processes + `wait`.
