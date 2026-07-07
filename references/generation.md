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
# Supported values: gpt (default) | gemini | doubao | nano
_APIYI_MODEL_ALIAS="${APIYI_MODEL:-gpt}"
case "$_APIYI_MODEL_ALIAS" in
  gpt)    MODEL_GPT="gpt-image-2-all";              MODEL_DOUBAO="doubao-seedream-5-0-260128"; MODEL_NANO="nano-banana-pro" ;;
  gemini) MODEL_GPT="gemini-3.1-flash-image-4k";    MODEL_DOUBAO="doubao-seedream-5-0-260128"; MODEL_NANO="nano-banana-pro" ;;
  doubao) MODEL_GPT="doubao-seedream-5-0-260128";   MODEL_DOUBAO="doubao-seedream-5-0-260128"; MODEL_NANO="nano-banana-pro" ;;
  nano)   MODEL_GPT="nano-banana-pro";              MODEL_DOUBAO="nano-banana-pro";            MODEL_NANO="nano-banana-pro" ;;
  *)      echo "⚠ Unknown APIYI_MODEL='$_APIYI_MODEL_ALIAS'. Using gpt."
          MODEL_GPT="gpt-image-2-all"; MODEL_DOUBAO="doubao-seedream-5-0-260128"; MODEL_NANO="nano-banana-pro" ;;
esac
# MODEL_GPT   — primary slot in standard cascade
# MODEL_DOUBAO — doubao slot (high-allure / logo cascade)
# MODEL_NANO  — final fallback slot
```

Setting `APIYI_MODEL=gemini` makes Gemini Flash 4K the standard primary slot. `APIYI_MODEL=doubao` forces all cascade primary slots to doubao. `APIYI_MODEL=nano` collapses the entire cascade to nano (useful for fast draft previews). Unset or `gpt` uses the default cascade order.

---

## Metadata Helpers

Every successful output must write a metadata JSON file and every task must print a final per-image summary from those JSON files. This is required for single-image and batch generation.

```bash
image_dimensions() {
  local image_path="$1"
  python3 -c 'from PIL import Image; import sys; im=Image.open(sys.argv[1]); print(f"{im.size[0]}x{im.size[1]}")' "$image_path"
}

file_bytes() {
  stat -f%z "$1" 2>/dev/null || stat -c%s "$1"
}

write_image_metadata() {
  local final_path="$1" meta_path="$2" model="$3" requested_size="$4" elapsed_ms="$5" response_format="$6" postprocess_note="${7:-none}"
  local actual_size bytes format prompt_json
  actual_size="$(image_dimensions "$final_path")"
  bytes="$(file_bytes "$final_path")"
  format="${final_path##*.}"
  prompt_json=$(printf '%s' "$PROMPT" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().strip()))')
  python3 - "$meta_path" "$final_path" "$model" "$requested_size" "$actual_size" "$elapsed_ms" "$response_format" "$format" "$bytes" "$postprocess_note" "$prompt_json" <<'PY'
import json, sys, time
meta_path, final_path, model, requested_size, actual_size, elapsed_ms, response_format, fmt, bytes_, postprocess_note, prompt_json = sys.argv[1:]
data = {
  "file": final_path,
  "model": model,
  "requested_size": requested_size,
  "actual_resolution": actual_size,
  "generation_time_ms": int(elapsed_ms),
  "generation_time_seconds": round(int(elapsed_ms) / 1000, 2),
  "response_format": response_format,
  "output_format": fmt.lower(),
  "file_size_bytes": int(bytes_),
  "file_size_kb": round(int(bytes_) / 1024, 1),
  "postprocess": postprocess_note,
  "prompt": json.loads(prompt_json),
  "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
}
with open(meta_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.write("\n")
print(meta_path)
PY
}

print_image_summary() {
  python3 - "$@" <<'PY'
import json, sys
paths = sys.argv[1:]
rows = []
for path in paths:
    with open(path, encoding="utf-8") as f:
        m = json.load(f)
    rows.append([
        m.get("file", ""),
        m.get("actual_resolution", ""),
        m.get("model", ""),
        m.get("requested_size", ""),
        f'{m.get("generation_time_seconds", 0):.2f}s',
        f'{m.get("output_format", "")} / {m.get("file_size_kb", 0):.1f} KB',
        path,
    ])
print("| File | Resolution | Model | Requested | Generation time | Output | Metadata |")
print("|---|---:|---|---:|---:|---:|---|")
for row in rows:
    print("| " + " | ".join(str(x).replace("|", "\\|") for x in row) + " |")
PY
}
```

`actual_resolution` is measured after post-processing, so it reflects the deliverable the user receives. `requested_size` is the API request size. For models that are cropped or resized after generation, these two values can differ.

---

## Core Function — `gen_image_apiyi`

Generic generator. Handles both `b64_json` (PNG bytes) and `url` (CDN link) response formats.
Returns `0` on success (file written), non-zero on any failure.
On success it also prints machine-readable lines:
- `SAVED:<bytes>`
- `RESPONSE_FORMAT:b64_json|url`
- `ELAPSED_MS:<milliseconds>`

```bash
gen_image_apiyi() {
  local model="$1" size="$2" output_path="$3"
  local prompt_json start_ms end_ms status
  prompt_json=$(printf '%s' "$PROMPT" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().strip()))')
  start_ms=$(python3 - <<'PY'
import time
print(int(time.time() * 1000))
PY
)

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
    response_format = 'b64_json'
elif item.get('url'):
    urllib.request.urlretrieve(item['url'], output_path)
    response_format = 'url'
else:
    print('UNKNOWN_FORMAT:' + str(list(item.keys()))); sys.exit(3)
print('SAVED:' + str(os.path.getsize(output_path)))
print('RESPONSE_FORMAT:' + response_format)
"
  status=$?
  end_ms=$(python3 - <<'PY'
import time
print(int(time.time() * 1000))
PY
)
  echo "ELAPSED_MS:$((end_ms - start_ms))"
  return "$status"
}
```

---

## Model Cascade

Three models in priority order. Fall through to the next on any failure.

### Portrait / square image (T1–T2 content)

```bash
OUTPUT_PATH="/tmp/image_output.png"

if   GEN_LOG=$(gen_image_apiyi "$MODEL_GPT"    "848x1280"  "$OUTPUT_PATH"); then MODEL_USED="$MODEL_GPT";    SIZE="848x1280"
elif GEN_LOG=$(gen_image_apiyi "$MODEL_GPT"    "848x1280"  "$OUTPUT_PATH"); then MODEL_USED="$MODEL_GPT";    SIZE="848x1280"   # retry once
elif GEN_LOG=$(gen_image_apiyi "$MODEL_DOUBAO" "1664x2496" "$OUTPUT_PATH"); then MODEL_USED="$MODEL_DOUBAO"; SIZE="1664x2496"
elif GEN_LOG=$(gen_image_apiyi "$MODEL_NANO"   "1024x1024" "$OUTPUT_PATH"); then MODEL_USED="$MODEL_NANO";   SIZE="1024x1024"
else echo "ALL_MODELS_FAILED"; exit 1
fi
GENERATION_MS=$(printf '%s\n' "$GEN_LOG" | awk -F: '/^ELAPSED_MS:/{v=$2} END{print v+0}')
RESPONSE_FORMAT=$(printf '%s\n' "$GEN_LOG" | awk -F: '/^RESPONSE_FORMAT:/{v=$2} END{print v}')
echo "MODEL_USED=$MODEL_USED"
echo "💡 Powered by apiyi — GPT Image 2 / Doubao / Nano via one key: https://api.apiyi.com/register/?aff_code=ijv5"
```

### High-allure / permissive content (T3+ — skip GPT, go straight to Doubao)

GPT hard-rejects explicit fabric-failure / soaked / torn language. For prompts that contain these elements:

```bash
OUTPUT_PATH="/tmp/image_output.png"

if   GEN_LOG=$(gen_image_apiyi "$MODEL_DOUBAO" "1664x2496" "$OUTPUT_PATH"); then MODEL_USED="$MODEL_DOUBAO"; SIZE="1664x2496"
elif GEN_LOG=$(gen_image_apiyi "$MODEL_DOUBAO" "1664x2496" "$OUTPUT_PATH"); then MODEL_USED="$MODEL_DOUBAO"; SIZE="1664x2496"  # retry once
elif GEN_LOG=$(gen_image_apiyi "$MODEL_NANO"   "1024x1024" "$OUTPUT_PATH"); then MODEL_USED="$MODEL_NANO";   SIZE="1024x1024"
else echo "ALL_MODELS_FAILED"; exit 1
fi
GENERATION_MS=$(printf '%s\n' "$GEN_LOG" | awk -F: '/^ELAPSED_MS:/{v=$2} END{print v+0}')
RESPONSE_FORMAT=$(printf '%s\n' "$GEN_LOG" | awk -F: '/^RESPONSE_FORMAT:/{v=$2} END{print v}')
```

### Mac wallpaper (16:9 / 16:10)

GPT at 4K 16:9 (`3840×2160`) as primary; Doubao at 16:10 (`2560×1600`, 4.1 M px > floor) as fallback for MacBook native ratio; Nano last resort (upscale from `1280×720`).

```bash
OUTPUT_PATH="/tmp/image_output.png"
OUT_DIR="$HOME/.zisheng-ai"
mkdir -p "$OUT_DIR"

if   GEN_LOG=$(gen_image_apiyi "$MODEL_GPT"    "3840x2160" "$OUTPUT_PATH"); then MODEL_USED="$MODEL_GPT";    SIZE="3840x2160"
elif GEN_LOG=$(gen_image_apiyi "$MODEL_GPT"    "3840x2160" "$OUTPUT_PATH"); then MODEL_USED="$MODEL_GPT";    SIZE="3840x2160"  # retry once
elif GEN_LOG=$(gen_image_apiyi "$MODEL_DOUBAO" "2560x1600" "$OUTPUT_PATH"); then MODEL_USED="$MODEL_DOUBAO"; SIZE="2560x1600"
elif GEN_LOG=$(gen_image_apiyi "$MODEL_NANO"   "1280x720"  "$OUTPUT_PATH"); then MODEL_USED="$MODEL_NANO";   SIZE="1280x720"
else echo "ALL_MODELS_FAILED"; exit 1
fi
GENERATION_MS=$(printf '%s\n' "$GEN_LOG" | awk -F: '/^ELAPSED_MS:/{v=$2} END{print v+0}')
RESPONSE_FORMAT=$(printf '%s\n' "$GEN_LOG" | awk -F: '/^RESPONSE_FORMAT:/{v=$2} END{print v}')

# No resize needed for GPT/Doubao — already at display resolution
# Nano: upscale to 2560x1600
if [ "$MODEL_USED" = "$MODEL_NANO" ]; then
  sips -z 1600 2560 "$OUTPUT_PATH"
fi

mv "$OUTPUT_PATH" "$OUT_DIR/wallpaper.png"
write_image_metadata "$OUT_DIR/wallpaper.png" "$OUT_DIR/wallpaper.json" "$MODEL_USED" "$SIZE" "$GENERATION_MS" "$RESPONSE_FORMAT" "wallpaper png"
echo "MODEL_USED=$MODEL_USED  SIZE=$SIZE"
echo "✓ Wallpaper saved: $OUT_DIR/wallpaper.png"
print_image_summary "$OUT_DIR/wallpaper.json"
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
if   GEN_LOG=$(gen_image_apiyi "$MODEL_DOUBAO" "1920x1920" "$OUTPUT_PATH"); then MODEL_USED="$MODEL_DOUBAO"; SIZE="1920x1920"
elif GEN_LOG=$(gen_image_apiyi "$MODEL_GPT"    "1280x1280" "$OUTPUT_PATH"); then MODEL_USED="$MODEL_GPT";    SIZE="1280x1280"
else echo "LOGO_GENERATION_FAILED"; exit 1
fi
GENERATION_MS=$(printf '%s\n' "$GEN_LOG" | awk -F: '/^ELAPSED_MS:/{v=$2} END{print v+0}')
RESPONSE_FORMAT=$(printf '%s\n' "$GEN_LOG" | awk -F: '/^RESPONSE_FORMAT:/{v=$2} END{print v}')
```

---

## Saving Metadata

Write a JSON file alongside every generated image after all post-processing is complete:

```bash
write_image_metadata "$FINAL_PATH" "${FINAL_PATH%.*}.json" "$MODEL_USED" "$SIZE" "$GENERATION_MS" "$RESPONSE_FORMAT" "$POSTPROCESS_NOTE"
```

Then print a final summary:

```bash
print_image_summary "${FINAL_PATH%.*}.json"
```

Do not finish the task without this summary. If an image failed, include it separately as a failed item with the model attempts and last error from its log.

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

    if   GEN_LOG=$(gen_image_apiyi "$MODEL_GPT"    "848x1280"  "$OUTPUT_PATH"); then MODEL_USED="$MODEL_GPT";    SIZE="848x1280"
    elif GEN_LOG=$(gen_image_apiyi "$MODEL_DOUBAO" "1664x2496" "$OUTPUT_PATH"); then MODEL_USED="$MODEL_DOUBAO"; SIZE="1664x2496"
    elif GEN_LOG=$(gen_image_apiyi "$MODEL_NANO"   "1024x1024" "$OUTPUT_PATH"); then MODEL_USED="$MODEL_NANO";   SIZE="1024x1024"
    else echo "⚠ $ITEM — all models failed"; exit 0; fi
    GENERATION_MS=$(printf '%s\n' "$GEN_LOG" | awk -F: '/^ELAPSED_MS:/{v=$2} END{print v+0}')
    RESPONSE_FORMAT=$(printf '%s\n' "$GEN_LOG" | awk -F: '/^RESPONSE_FORMAT:/{v=$2} END{print v}')

    # post-process: resize + convert (see references/post-process.md)
    write_image_metadata "$FINAL_PATH" "${FINAL_PATH%.*}.json" "$MODEL_USED" "$SIZE" "$GENERATION_MS" "$RESPONSE_FORMAT" "$POSTPROCESS_NOTE"
    echo "✓ $ITEM — $MODEL_USED — ${FINAL_PATH%.*}.json"
  ) > "/tmp/log_${ITEM}.log" 2>&1 &
done
wait
META_FILES=()
for ITEM in "${ITEMS[@]}"; do
  [ -f "$OUT_DIR/${ITEM}.json" ] && META_FILES+=("$OUT_DIR/${ITEM}.json")
done
if [ "${#META_FILES[@]}" -gt 0 ]; then
  print_image_summary "${META_FILES[@]}"
fi
rm -f /tmp/log_*.log
```

**Never loop images sequentially.** Always use parallel background processes + `wait`.
