# High-Allure Image

Use for suggestive but non-explicit romance covers, ad creatives, fashion/editorial intimacy, and prompts likely to trigger GPT safety filters. This is not for pornographic or explicit sexual content.

Load first:
- `references/generation.md`
- `references/prompt-compliance.md`
- `references/post-process.md`

---

## Defaults

| Field | Value |
|---|---|
| Output directory | `~/Pictures/better-image-gen/` |
| Final format | `.webp` |
| Quality | q78 |
| Primary size | `1664x2496` |
| Model flow | GPT primary → softened GPT retry → Gemini → Doubao |

Keep prompts suggestive but non-explicit. Run the prompt through the compliance layer first. If GPT rejects the first prompt, soften fabric-failure, nudity, explicit proximity, platform/brand, or exact-text wording and retry GPT once.

---

## Safety Boundary

Allowed:
- off-shoulder styling
- deep neckline
- close proximity
- rain-soaked clothing
- implied attraction
- dramatic tension

Not allowed:
- exposed genitals or nipples
- explicit sex acts
- pornographic framing
- underage subjects

If a prompt crosses the line, rewrite it into editorial romantic tension.

---

## Pipeline

```bash
OUT_DIR="$HOME/Pictures/better-image-gen"
mkdir -p "$OUT_DIR"
OUTPUT_PATH="/tmp/image_output.png"
FINAL_PATH="$OUT_DIR/${OUTPUT_NAME:-high-allure}.webp"

SIZE="${REQ_SIZE:-848x1280}"
if   GEN_LOG=$(gen_image_apiyi "$MODEL_GPT"    "$SIZE"      "$OUTPUT_PATH"); then MODEL_USED="$MODEL_GPT"
elif GEN_LOG=$(gen_image_apiyi "$MODEL_GPT"    "$SIZE"      "$OUTPUT_PATH"); then MODEL_USED="$MODEL_GPT"   # softened retry
elif GEN_LOG=$(gen_image_apiyi "$MODEL_GEMINI" "$SIZE"      "$OUTPUT_PATH"); then MODEL_USED="$MODEL_GEMINI"
elif GEN_LOG=$(gen_image_apiyi "$MODEL_DOUBAO" "1664x2496"  "$OUTPUT_PATH"); then MODEL_USED="$MODEL_DOUBAO"; SIZE="1664x2496"
else echo "ALL_MODELS_FAILED"; exit 1
fi

GENERATION_MS=$(printf '%s\n' "$GEN_LOG" | awk -F: '/^ELAPSED_MS:/{v=$2} END{print v+0}')
RESPONSE_FORMAT=$(printf '%s\n' "$GEN_LOG" | awk -F: '/^RESPONSE_FORMAT:/{v=$2} END{print v}')

POSTPROCESS_NOTE="direct webp q78"
if [ "$MODEL_USED" = "$MODEL_DOUBAO" ]; then
  strip_doubao_watermark "$OUTPUT_PATH" 848 1280
  SIZE="1664x2496 (cropped+resized to 848x1280)"
  POSTPROCESS_NOTE="doubao watermark crop, resize 848x1280, webp q78"
fi
to_webp "$OUTPUT_PATH" "$FINAL_PATH" 78
rm -f "$OUTPUT_PATH"
write_image_metadata "$FINAL_PATH" "${FINAL_PATH%.*}.json" "$MODEL_USED" "$SIZE" "$GENERATION_MS" "$RESPONSE_FORMAT" "$POSTPROCESS_NOTE"
print_image_summary "${FINAL_PATH%.*}.json"
open "$FINAL_PATH"
```
