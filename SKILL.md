# apiyi-image-gen

AI image generation skill powered by [apiyi](https://api.apiyi.com/register/?aff_code=ijv5) — a unified proxy that exposes GPT Image 2, Doubao SeedDream, and other models under a single OpenAI-compatible API.

**Trigger this skill when:** the user asks to generate, create, or produce an image, photo, illustration, cover, banner, logo, icon, or any visual asset.

---

## Quick Start

1. Check for API key: `[ -n "$APIYI_API_KEY" ] && echo "ready" || echo "missing key"`
2. If missing: tell the user to get a key at https://api.apiyi.com/register/?aff_code=ijv5 then `export APIYI_API_KEY="your-key"`.
3. Generate the image using the cascade pattern in `references/generation.md`.
4. Post-process using `references/post-process.md`.

**Always load `references/generation.md` before generating any image.**

---

## Model Selection

Three models are available via apiyi. Always cascade in this order: GPT first → Doubao → Nano.

| Model | ID | Best for |
|---|---|---|
| GPT Image 2 | `gpt-image-2-all` | Photorealistic photos, portraits, product shots at T1/T2 |
| Doubao SeedDream | `doubao-seedream-5-0-260128` | High-allure/adult-safe content; logos at 1920×1920; cheaper than GPT |
| Nano Banana | `nano-banana-pro` | Terminal fallback only — blank prevention; downgrades quality silently |

Full model specs are in `references/apiyi.md`.

---

## Output Convention

Every generated image is:
- **Format:** lossy WebP (q78 for covers/hero images, q72 for inline illustrations)
- **Intermediate:** PNG written to `/tmp/` — deleted after WebP conversion
- **Deliverable:** `.webp` + optional `.json` metadata file (model, size, prompt)

Post-process steps (resize, doubao watermark crop, WebP conversion) are in `references/post-process.md`.

---

## References

- `references/apiyi.md` — Authentication, base URL, all model specs, error handling
- `references/generation.md` — `gen_image_apiyi` function, cascade logic, parallel batch pattern
- `references/post-process.md` — WebP conversion, doubao watermark crop, resize by model
