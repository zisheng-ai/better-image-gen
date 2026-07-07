# High-Allure Image

Use for suggestive but non-explicit romance covers, ad creatives, fashion/editorial intimacy, and prompts likely to trigger GPT safety filters. This is not for pornographic or explicit sexual content.

Load first:
- `references/generation.md`
- `references/post-process.md`

---

## Defaults

| Field | Value |
|---|---|
| Output directory | `~/Pictures/better-image-gen/` |
| Final format | `.webp` |
| Quality | q78 |
| Primary size | `1664x2496` |
| Model flow | GPT primary → softened GPT retry |

Keep prompts suggestive but non-explicit. If GPT rejects the first prompt, soften fabric-failure, nudity, or explicit proximity wording and retry GPT once.

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

if   GEN_LOG=$(gen_image_apiyi "$MODEL_GPT" "${REQ_SIZE:-848x1280}" "$OUTPUT_PATH"); then MODEL_USED="$MODEL_GPT"; SIZE="${REQ_SIZE:-848x1280}"
elif GEN_LOG=$(gen_image_apiyi "$MODEL_GPT" "${REQ_SIZE:-848x1280}" "$OUTPUT_PATH"); then MODEL_USED="$MODEL_GPT"; SIZE="${REQ_SIZE:-848x1280}"
else echo "ALL_MODELS_FAILED"; exit 1
fi

GENERATION_MS=$(printf '%s\n' "$GEN_LOG" | awk -F: '/^ELAPSED_MS:/{v=$2} END{print v+0}')
RESPONSE_FORMAT=$(printf '%s\n' "$GEN_LOG" | awk -F: '/^RESPONSE_FORMAT:/{v=$2} END{print v}')

POSTPROCESS_NOTE="direct gpt webp q78"
to_webp "$OUTPUT_PATH" "$FINAL_PATH" 78
rm -f "$OUTPUT_PATH"
write_image_metadata "$FINAL_PATH" "${FINAL_PATH%.*}.json" "$MODEL_USED" "$SIZE" "$GENERATION_MS" "$RESPONSE_FORMAT" "$POSTPROCESS_NOTE"
print_image_summary "${FINAL_PATH%.*}.json"
open "$FINAL_PATH"
```
