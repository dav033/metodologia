# REQ-002 research: embeddings for the balloon-decoration library RAG

Researched 2026-10-08. All prices USD. Facts carry a URL; judgment is marked "Judgment". Anything I could not verify is in section 9.

Scope: ~1,500 items; each has a Spanish "ficha" (80-250 words) and 1-2 images (source photo + 3D render). Needs: (a) text embeddings for hybrid search in Postgres/pgvector (Neon); (b) image embeddings so a user photo finds the closest items (photo<->photo, photo<->render), cross-modal text queries are a bonus.

## 1. Headline

- A new Google model changes the picture: **`gemini-embedding-2`** (GA 2026-04-22; preview 2026-03-10). It is natively multimodal (text, image, video, audio, PDF) in ONE vector space, 100+ languages, 128-3072 dims with Matryoshka (768 recommended), 8,192-token input. Price: $0.20/1M text tokens and about $0.00012 per image. It is the same API/SDK the project already uses for the product RAG.
  - https://ai.google.dev/gemini-api/docs/embeddings
  - https://ai.google.dev/gemini-api/docs/changelog (2026-03-10 preview, 2026-04-22 GA)
  - https://ai.google.dev/gemini-api/docs/pricing
- Vertex `multimodalembedding@001` is English-only text with a 32-token text limit: disqualified for Spanish fichas.
- Everything else is either a paid API with more cost/complexity for no clear gain (Cohere, Voyage), non-commercial for self-hosting (all Jina models), or text-only (OpenAI).
- Total cost of the recommended path is under $1 initial and under $0.10/month. Cost is not a differentiator; **quality of image<->image matching on balloon decoration is the only open risk**, hence the benchmark in section 7.

## 2. Comparison table

"Dims" = native / Matryoshka (MRL) options. pgvector fit assumes pgvector 0.8.x: `vector` HNSW max 2,000 dims, `halfvec` HNSW max 4,000 dims, plain `vector` storage up to 16,000 (https://github.com/pgvector/pgvector, README read 2026-10-08, latest version shown 0.8.7).

| Model | Modality | Dims (MRL) | Max input | Spanish | Price | API from Python | Self-host license | pgvector fit |
|---|---|---|---|---|---|---|---|---|
| **gemini-embedding-2** (GA) | text, image (max 6/request), video, audio, PDF; unified space | 128-3072 (MRL; 768/1536/3072 recommended; truncated output is auto-normalized) | 8,192 tokens text | 100+ languages; MMTEB multilingual 69.9 (paper) | text $0.20/1M (batch $0.10); image $0.45/1M tokens, about $0.00012/image (batch $0.225, about $0.00006/image); free tier exists | `google-genai`: `client.models.embed_content(model="gemini-embedding-2", ...)` | n/a (API only) | 768 and 1536 are plain `vector` + HNSW; 3072 needs `halfvec` for HNSW |
| gemini-embedding-001 | text only | 128-3072 (MRL; must normalize manually when not 3072) | 2,048 tokens | 100+ languages | $0.15/1M (per tokencost.app, secondary source) | same SDK | n/a | same; shutdown no earlier than 2028-05-14; incompatible vector space with embedding-2 |
| Vertex multimodalembedding@001 | text + image + video, shared space | 128/256/512/1408 | text 32 tokens; image 20 MB, resized to 512x512 | **English only** for text | about $0.0001/image, $0.80/1M text tokens (aggregator, secondary) | `vertexai` SDK, needs GCP project | n/a | 1408 fits `vector` HNSW |
| Cohere embed-v4.0 | text, image, mixed | 256/512/1024/1536 (MRL) | 128k tokens; image <= 5 MB, tokens about pixels/784, up to 96 images/request | 100+ languages | $0.12/1M text; images about $0.47/1M tokens (aggregators, secondary) | `cohere` SDK | proprietary | fits |
| **Cohere embed-v5.0-pro / -fast** (released 2026-09-30, 8 days old) | text, image, mixed | 256-2048 (default 2048) | 128k | 100+ languages | Pro $0.12 text, Fast $0.08 text, both $0.40/1M image tokens (secondary source) | `cohere` SDK | proprietary (also Model Vault at $2-3.25k/month) | 2048 fits HNSW only as `halfvec` or truncate to 1536; Pro and Fast share one space |
| Voyage voyage-multimodal-3.5 | text, image, video, interleaved | 256/512/1024 (default)/2048 (MRL) | 32k tokens; image <= 16 MP and 20 MB; 560 px = 1 token | not stated in docs | $0.12/1M text; $0.60 per 1B pixels (cap $0.0012/image); free 200M tokens + 150B pixels | `voyageai.Client.multimodal_embed()` | proprietary | fits |
| Voyage text voyage-4 / -4-large / -4-lite | text | up to 2048 (MRL) | 32k (assumed) | multilingual (not verified for Spanish) | $0.06 / $0.12 / $0.02 per 1M; first 200M tokens free | `voyageai` | proprietary | fits |
| Jina embeddings-v5-omni (small 1024d / nano 768d), v5-text, v4, CLIP v2 | text+image (v4, v5-omni, CLIP v2); text only (v5-text) | v4: 128-2048; CLIP v2: 64-1024 | v4: 32k; CLIP v2: 8,192 text, 512x512 image | CLIP v2: 89 languages; v4: 30+ | API about $0.05/1M tokens, 10M free (secondary) | `requests` / HF transformers | **CC BY-NC 4.0 (v5, CLIP v2) or Qwen Research License (v4): not usable for commercial self-hosting** | fits |
| OpenAI text-embedding-3-small / -large | text only | 1536 / 3072 (MRL via `dimensions`) | 8,192 tokens | decent, not a leader | $0.02 / $0.13 per 1M (page gives pages per dollar 62,500 / 9,615 which matches) | `openai` | n/a | small fits; large must be shortened to <= 2000 or use `halfvec` |
| SigLIP 2 (B/16 86M vision, L 303M, So400m 400M, g 1B) | image + text | B 768 / L 1024 / So400m 1152 (typical projection sizes, not verified on the cards) | **text capped at 64 tokens**; image 224-384 px (NaFlex variants flexible) | multilingual Gemma tokenizer (256k vocab), but 90% English / 10% non-English training data | $0 (CPU) | `transformers` | **Apache 2.0** | fits |
| DINOv2 (base 86.6M, 768d) | image only | 768 (small 384, large 1024, giant 1536; not verified) | image patches | n/a | $0 (CPU) | `transformers` | **Apache 2.0** (HF card) | fits |
| DINOv3 | image only | varies | image | n/a | $0 | `transformers` | custom DINOv3 license, commercial use allowed, redistribution needs the license text | fits |
| OpenCLIP (e.g. ViT-B/32 xlm-roberta-base laion5b, 63.4% COCO / 86.2% Flickr30k) | image + text | 512 (B/32), 768 (L/14) | 77-token text | multilingual only with XLM-R variants | $0 | `open_clip_torch` | code MIT; weights vary per checkpoint (not verified) | fits |
| Qwen3-VL-Embedding-2B | text+image | 2048 (MRL 64-2048) | 32k | multilingual | $0 but 2.1B params: slow on CPU | `transformers` | Apache 2.0 | 2048 needs halfvec/truncation |

Sources for the table rows:
- Gemini: https://ai.google.dev/gemini-api/docs/embeddings , https://ai.google.dev/gemini-api/docs/pricing , https://ai.google.dev/gemini-api/docs/models/gemini-embedding-2 , paper https://arxiv.org/abs/2605.27295 (2026-05-26), deprecations https://ai.google.dev/gemini-api/docs/deprecations (gemini-embedding-001 shutdown 2028-05-14 earliest; gemini-embedding-2-preview 2026-08-10, already past, so use the GA name `gemini-embedding-2`).
- Gemini 001 vs 2 price and incompatibility: https://tokencost.app/blog/gemini-embedding-2-pricing (secondary).
- Vertex multimodalembedding@001: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/embeddings/get-multimodal-embeddings ("Maximum text length is 32 tokens", "English only", dims 128/256/512/1408, image 20 MB resized to 512x512, quota 120-600 req/min/project). Price from aggregator https://www.getmaxim.ai/bifrost/llm-cost-calculator/provider/vertex_ai/model/multimodalembedding-001 (secondary).
- Cohere: https://docs.cohere.com/docs/cohere-embed (model table incl. embed-v5.0-pro/fast, embed-v4.0), https://docs.cohere.com/docs/rate-limits (Embed images: trial 5 inputs/min, production 400 inputs/min), v5 release and pricing https://datanorth.ai/news/cohere-releases-embed-5-pro-and-embed-5-fast (secondary), image token rule from AWS Bedrock doc https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-embed-v4.html (via search snippet). Cohere's own pricing page (https://cohere.com/pricing) lists only Model Vault prices for Embed 5; per-token API prices not confirmed there.
- Voyage: https://docs.voyageai.com/docs/multimodal-embeddings , https://docs.voyageai.com/docs/pricing , https://docs.voyageai.com/docs/rate-limits (multimodal Tier 1: 2M TPM).
- Jina: https://jina.ai/embeddings/ (licenses), https://huggingface.co/jinaai/jina-clip-v2 , https://huggingface.co/jinaai/jina-embeddings-v4 , Elastic acquired Jina 2025-10-09 (https://www.businesswire.com/news/home/20251009619654/en/Elastic-Completes-Acquisition-of-Jina-AI-a-Leader-in-Frontier-Models-for-Multimodal-and-Multilingual-Search), pricing https://markaicode.com/pricing/jina-ai-pricing/ (secondary).
- OpenAI: https://developers.openai.com/api/docs/guides/embeddings (text-embedding-3-small 1536d, -large 3072d, 8192 tokens, MRL via `dimensions`; no image support).
- SigLIP 2: https://huggingface.co/google/siglip2-base-patch16-224 (Apache 2.0), https://arxiv.org/html/2502.14786 (64-token text, Gemma tokenizer, 90/10 English/non-English), https://huggingface.co/google/siglip2-so400m-patch14-384 .
- DINOv2: https://huggingface.co/facebook/dinov2-base (768d, 86.6M, Apache 2.0). DINOv3 license: https://ai.meta.com/blog/dinov3-self-supervised-vision-model/ (via search summary).
- OpenCLIP multilingual: https://huggingface.co/laion/CLIP-ViT-B-32-xlm-roberta-base-laion5B-s13B-b90k
- Qwen3-VL-Embedding: https://arxiv.org/pdf/2601.04720 and aggregator cards (search summary).

## 3. What the evidence says about image<->image

- Gemini Embedding 2 paper: 79.4 Recall@1 on the Google Universal Image Embedding Challenge (instance-level retrieval over a 200k-image index), vs 69.5 for the legacy multimodalembedding and 68.6 for Amazon Nova MME. https://arxiv.org/html/2605.27295 . This is Google's own benchmark; treat as indicative, not proof for balloon decor.
- Independent comparison of SigLIP/SigLIP2/DINO for image-to-image retrieval: SigLIP2 only about +1.2 mAP over SigLIP; DINO wins on landmark retrieval (ROxford/RParis), SigLIP wins on fine-grained object sets (Stanford Cars). Result is dataset dependent. https://arxiv.org/pdf/2603.16100 (via search summary; I did not read the paper itself).
- Judgment: photo vs 3D render is a domain gap (real lighting/background/clutter vs clean synthetic). Semantic models (Gemini 2, SigLIP2) tend to bridge domain gaps better than DINOv2, which encodes more low-level layout/texture. DINOv2 is a good complement for "same structure/shape" and a good fallback for photo<->photo. Colour is critical in balloon decor and none of these guarantee colour fidelity, so test (and consider a cheap colour-palette feature as a rerank signal).

## 4. Spanish quality

- Gemini Embedding 2: 100+ languages, MMTEB (multilingual) mean 69.9 (paper above). Good for Spanish fichas, and queries can be in Spanish against Spanish text AND against images (same space).
- OpenAI 3: works for Spanish, text-only, no image path; no reason to add a second vendor.
- Cohere/Voyage: claim multilingual (Cohere 100+; Voyage docs do not state languages for multimodal 3.5).
- SigLIP2/CLIP/Jina CLIP: only useful for SHORT Spanish text queries (64 tokens for SigLIP2, 77 for OpenCLIP, 8k for Jina CLIP v2). They cannot embed a whole ficha, so they are not a text-search model here. Judgment: use them only for image vectors.
- Vertex multimodalembedding@001: English-only. Rejected.

## 5. Costs (estimates)

Assumptions: 1,500 fichas x ~300 tokens = 0.45M tokens (Spanish may tokenize to 350-400; use 0.6M as the upper bound). 3,000 images. Monthly: 2,000 text queries x ~30 tokens = 0.06M tokens; 300 image queries.
Image token count for Gemini: the price page implies about 267 tokens/image ($0.00012 / $0.45 per 1M); Gemini images are generally 258 tokens per tile (https://ai.google.dev/gemini-api/docs/tokens), which is consistent.

| Option | Initial indexing (text + 3,000 images) | Monthly (2,000 text + 300 image queries) |
|---|---|---|
| gemini-embedding-2 (standard) | text $0.09-0.12 + images $0.36 = about **$0.45-0.50** | text $0.012 + images $0.036 = about **$0.05** |
| gemini-embedding-2 (batch, -50%) | about $0.23-0.25 | n/a (queries need real-time) |
| gemini-embedding-001 text only | $0.07-0.09 | $0.01 |
| OpenAI text-embedding-3-small / -large | $0.009 / $0.06 (text only) | < $0.01 |
| Cohere embed-v5 Pro | text $0.054-0.07 + images 3,000 x 1,300-3,100 tokens x $0.40/M = $1.6-3.8; total about **$1.7-3.9** | about $0.1-0.4 |
| Voyage voyage-multimodal-3.5 | text $0.05-0.07 + images 3,000 x ~1 MP = 3B px x $0.60/B = $1.8 (cap $3.6) = about $2; **covered by the free 200M tokens + 150B pixels, so $0** | $0 (free allowance) |
| Vertex multimodalembedding@001 | images $0.30 (English-only text, so not usable for fichas) | about $0.03 |
| Self-hosted SigLIP2 / DINOv2 on CPU | $0 marginal; Judgment: about 0.1-0.5 s per image on a few CPU cores, so 3,000 images take roughly 5-25 min once (I did not measure) | $0 but RAM about 1-2 GB resident for the model and CPU spikes per query |

Free-tier note: Gemini free tier is free of charge but unpaid-service content may be used by Google to improve products and read by human reviewers; "Do not submit sensitive, confidential, or personal information" ( https://ai.google.dev/gemini-api/terms ). Customer-uploaded photos should go through the **paid tier** (prompts/responses not used to improve products). Library fichas/photos are less sensitive, but use the paid key anyway; cost is cents.

Rate limits:
- Gemini: the docs do not publish per-model embedding RPM; they point to the AI Studio dashboard (https://ai.google.dev/gemini-api/docs/rate-limits). Batch API enqueued-token cap for the embedding model: 500k (Free/Tier 1), 5M (Tier 2), 10M (Tier 3). Judgment: 450k text tokens just fits one batch; submit text and images in separate chunks, or just use the real-time endpoint (4,500 calls is trivial).
- Cohere images: trial 5/min (too slow for 3,000 images, needs production key), production 400/min.
- Voyage multimodal: Tier 1 2M TPM; Tier 2 = 2x, Tier 3 = 3x.
- Vertex: 120-600 requests/min/project.

## 6. Recommendation

**One multimodal model for everything: `gemini-embedding-2` at 768 dims** (Matryoshka truncation, auto-normalized), stored as `vector(768)` (or `halfvec(768)`), cosine distance.

Why:
1. One vector space for ficha text, source photo, render and the user's photo, and for Spanish text queries. Cross-modal comes for free.
2. Same vendor, SDK, key and 768-dim convention as the existing product RAG (but see the compatibility warning below).
3. Cheapest realistic option overall (about $0.50 once, about $0.05/month) and no new infra; GA since 2026-04-22; 001 shutdown is not before 2028.
4. 768 dims keeps Neon storage trivial: 1,500 items x (1 text + 2 images) x 768 x 4 B is about 14 MB. At this scale a plain exact scan (no index) is fast enough; an HNSW index is optional. If you want to add one, `vector(768)` is far below the 2,000-dim HNSW limit. 1536 would also fit; 3072 would need `halfvec`.

Compatibility warning: embedding-2 vectors are not comparable with gemini-embedding-001 vectors (https://tokencost.app/blog/gemini-embedding-2-pricing, secondary). Keep the library in its own table/column with a `model` column; never mix with the product RAG vectors.

Implementation gotchas (from the docs):
- Retrieval prompt format for embedding-2: query `"task: search result | query: {content}"`, documents `"title: {title} | text: {content}"` (https://ai.google.dev/gemini-api/docs/embeddings). Embedding 2 uses these prompt prefixes instead of `task_type`.
- Passing several inputs in one `contents` list can AGGREGATE them into ONE embedding; to get one vector per image/ficha, send separate `Content` objects or one call per item. Max 6 images per request. (same page)
- Use model id `gemini-embedding-2`, not `-preview` (preview scheduled for shutdown 2026-08-10).
- Store per item: `text_vec` (ficha), `photo_vec`, `render_vec`; optionally a combined image+text vector. Query by `max(similarity)` over the item's vectors, then RRF fusion with Postgres full-text (tsvector, `spanish` config) for hybrid search (pgvector README documents RRF).

Fallback/complement (only if the benchmark fails the image criterion): **SigLIP2 (B/16 or So400m, Apache 2.0, CPU) or DINOv2-base (Apache 2.0, 768d) as a second, image-only vector** computed on the VPS, fused by RRF with the Gemini image score. Judgment: choose DINOv2 if photo<->photo is the weak point, SigLIP2 if photo<->render is. Avoid Jina models (non-commercial licenses). Do not choose Cohere v5 now: 8 days old, no cost advantage, image rate limits on trial keys. Voyage multimodal 3.5 is a reasonable optional paid challenger in the benchmark because its free allowance makes it $0.

## 7. Benchmark protocol (13 owner photos)

Goal: decide between (A) Gemini only, (A+) Gemini + a CPU image model, in under half a day and under $5.

Data prep (free):
1. Embed the whole library once per candidate (about 3,000 images + 1,500 fichas). Candidates: A = `gemini-embedding-2` at 768 (also run 1536 as a sanity check on MRL loss); B = SigLIP2 (try B/16-224 and So400m-384) image tower on CPU; C = DINOv2-base on CPU; D (optional challenger) = voyage-multimodal-3.5 at 1024 (free allowance).
2. For the 13 owner photos, identify the ground truth: the library item (reference/template) each photo corresponds to; mark whether the item has a source photo, a render, or both.

Queries and metrics (per candidate):
- Q1 photo -> all library images (photos and renders). Hit@1, Hit@3, Hit@5, MRR of the correct item (an item counts as found if ANY of its vectors is in the top-k, deduplicated by item).
- Q2 photo -> render vectors only (tests photo<->3D render).
- Q3 photo -> source-photo vectors only (tests photo<->photo).
- Q4 photo -> ficha text vectors (A only; cross-modal).
- Q5 Spanish text description of each photo (write 13 short descriptions, e.g. "arco orgánico rosa y dorado con globos de confeti") -> items (A only).
- Fusion runs: A image score + B or C by RRF (k=60); A image + full-text.
Success criteria (Judgment, adjust with the owner): Q1 Hit@3 >= 11/13 (85%) and Q2 Hit@3 >= 9/13 in the chosen setup; if A meets it, ship A alone.

Extra free signal to avoid deciding on 13 samples (13 is statistically thin; one photo = 7.7 points):
- Self-supervised set: use every library item that has both photo and render as a query-target pair (up to 1,500 pairs): query = photo, target = its render, and vice versa. Compute Hit@1/3/10 and MRR. Add degradations to imitate phone photos (random crop 60-90%, JPEG quality 50, brightness/contrast jitter, slight rotation) on the query side.
- Report colour confusion: among failures, how many returned an item with the right shape but wrong dominant colour (balloon decor is colour-driven).

Cost cap: **$5 total** for API calls (expected < $1: Gemini about $0.50 for full library x 2 dims = about $0.85 at most; Voyage $0 inside free allowance; Cohere not tested). The 13 photos plus the 1,500 degraded self-queries add about $0.20 of Gemini image calls. Self-hosted candidates: $0; check RAM first (the project notes the PC has 15.7 GB and heavy runs should be measured) and run SigLIP2/DINOv2 one at a time on the VPS or locally in batches of 32.

Output: a small table (candidate x Q1..Q5 x Hit@1/3/5, MRR) plus the list of failed photos with the returned top-3, written into the REQ-002 folder.

## 8. Judgment notes

- The existing stack already depends on Google embeddings, so adding Gemini Embedding 2 minimizes new moving parts. The main reason to leave Google would be poor fine-grained image matching, which the benchmark tests.
- If the owner later wants only image search with no cloud dependency, SigLIP2-B/16 on CPU is cheap enough to host, but would not cover Spanish ficha text; a text model would still be required.
- Never mix vectors from different models/dimensions in one column; keep `model` and `dims` columns and a re-index script.

## 9. Unverified / caveats

- Gemini embedding rate limits (RPM) for Tier 1/free: not published in docs I could read; check https://aistudio.google.com/rate-limit. Exact image token count for embedding-2 is inferred from price ($0.00012/image) and the generic 258 tokens/tile rule.
- gemini-embedding-001 price ($0.15/1M), Cohere v4/v5 per-token prices, Vertex multimodalembedding@001 price and Jina price are from secondary aggregators/news, not vendor pricing pages (Cohere's pricing page shows only Model Vault prices). Cohere v5 launch date (2026-09-30) is from a news summary; the Cohere docs table does list `embed-v5.0-pro/fast`.
- Cohere v5 image token formula assumed same as v4 (pixels/784).
- SigLIP2 and DINOv2 non-base embedding dims and CPU latency are from general knowledge/estimates, not measured here. OpenCLIP checkpoint licenses vary and were not checked.
- Independent image-to-image numbers (arXiv 2603.16100) were read only via a search summary.
- No benchmark of any model on balloon-decoration imagery exists in the sources; the protocol in section 7 is the only way to know.
- Gemini Embedding 2 free-tier details and whether the Neon plan has pgvector 0.8.x (HNSW iterative scan) were not checked here; Neon supports pgvector, but confirm the installed version (`select extversion from pg_extension where extname='vector'`).
