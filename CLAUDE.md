# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project purpose

Mobile-first single-page web app showing DUVETICA daily sales review. Phone-bookmarkable URL hosted on GitHub Pages, refreshed once a day. The repository's job is to keep `index.html` (committed at the repo root) up to date with the previous day's data.

Live URL: https://kyk2101.github.io/duv-daily-sales-review/

## How the build pipeline works

Three Python stages, run sequentially:

1. **`src/service/sales_review_app/fetch_data.py`** — Calls `dcs-ai-cli` via subprocess to download 6 datasets into `%TEMP%/dcs-ai-cli/`. Each call writes a timestamped `<name>_<unix>.json`. The script does not delete old files — `build_app.py` later picks the most recent by glob.
2. **`src/service/sales_review_app/build_app.py`** — Loads the 6 latest temp JSONs, aggregates them into a single tree (per-season top 20 BEST SELLER with per-color breakdown, top 15 stores with each store's top 5 styles, last 7 days daily trend split by SESN, yesterday's per-season top, per-season insights). Writes `data/duv_review_data.json` (committed to git) **and** `src/output/duv_review_data.json` (gitignored mirror).
3. **`src/service/sales_review_app/build_html.py`** — Reads the committed JSON and embeds it into a single self-contained HTML via `__DATA_PLACEHOLDER__`. Writes both `index.html` (repo root, what GitHub Pages serves) and `src/output/duvetica_sales_review.html` (gitignored mirror).

`run_daily.bat` orchestrates all three plus `git add/commit/push`.

`BASE_DT` and `TODAY` in `build_app.py` are computed at runtime from `date.today()`. The whole system assumes the build runs once a day; if you build twice in one day you'll see no JSON change.

## Common commands

All Python commands run from the repo root with `PYTHONPATH=.` and the project venv at `C:\Users\Admin\Desktop\DCSAI\.venv`:

```bash
# Full daily cycle (what the scheduler runs)
scripts/run_daily.bat

# Individual stages (for debugging)
PYTHONPATH=. ../../.venv/Scripts/python src/service/sales_review_app/fetch_data.py
PYTHONPATH=. ../../.venv/Scripts/python src/service/sales_review_app/build_app.py
PYTHONPATH=. ../../.venv/Scripts/python src/service/sales_review_app/build_html.py

# Skip fetch, rebuild from existing temp data (fastest iteration on UI)
PYTHONPATH=. ../../.venv/Scripts/python src/service/sales_review_app/build_app.py && \
PYTHONPATH=. ../../.venv/Scripts/python src/service/sales_review_app/build_html.py

# Local preview
start "" index.html
```

There are no tests or linters configured.

## UI architecture

Single HTML file, ~97 KB, no external dependencies (no CDN, no fonts loaded). The data tree is embedded inside a `<script type="application/json" id="appdata">` tag. All rendering happens client-side in a single IIFE inside `build_html.py`'s `HTML_TEMPLATE`.

UI invariant: **season is the top-level dimension**. The season tab at the top of the page (`26SS` / `25FW`) drives every section below it via `state.season` — insights, 7-day trend, yesterday's top, BEST SELLER cards, store list. When changing UI behavior, treat the season selector as global state and re-render all sections together via `renderAll()`.

Color codes (`COLOR_CD`) are F&F's internal codes and are displayed verbatim. Treat them as opaque strings — do not try to translate.

## Data conventions

- DUVETICA = `BRD_CD = 'V'`
- Season codes in API: `'25F'` for 25FW, `'26S'` for 26SS (one letter, not `25FW`/`26SS`)
- Period anchors: 25FW = `2025-07-01` ~ yesterday; 26SS = `2026-01-01` ~ yesterday
- All season ranking calls must include `selectors_sku: [{"system_field_name": "COLOR_CD"}]` so the per-color breakdown stays available in the cards
- `SALE_RET_YN = 'N'` filter is applied to channel queries to exclude returns
- The fetch endpoints come from DCS knowledge graph intents:
  - `한국 상품 매출 분석 시즌 의류 스타일 랭킹` → `get_season_wear_style_order_stor_sale_stock_sale_rt`
  - `한국 채널 상품 판매상세 분석` → `get_channel_product_sale_type`

## Auth constraint (the big gotcha)

DCS API auth is browser-based PKCE OAuth with a localhost callback. **It cannot run unattended in GitHub Actions or any cloud CI.** The current automation works because `dcs-ai-cli` is invoked from a logged-in user session on the local PC.

`.github/workflows/daily.yml` is intentionally guarded with `if: false` — it's a Phase 2 scaffold for the day F&F DCS team issues a long-lived service token. Don't enable it without that token in `secrets.DCSAI_TOKEN` and rewriting `fetch_data.py` to use the token over HTTPS instead of `dcs-ai-cli`.

If `git push` fails inside `run_daily.bat`, the most likely cause is a stale Windows credential cached for a different GitHub account. The repo `kyk2101/duv-daily-sales-review` lists `ykkimfnf` as a collaborator so the work-account credential cache works for push.

## Folder layout caveats

- Folder name contains Korean and a space (`매출리뷰용 어플`). Quote paths in shell commands.
- `index.html` and `data/duv_review_data.json` are **build outputs that are committed**. GitHub Pages serves the root `index.html`, so each daily push must include both files together — that's how the published page actually changes.
- `src/output/` is gitignored. It's a build mirror used for manual local preview without polluting commits.
- The DCS AI parent project at `C:\Users\Admin\Desktop\DCSAI\` has its own `CLAUDE.md` and `.claude/rules/` enforcing the `src/{util,service,core,output,download}` layout and `dcs-ai-cli` usage rules. Those still apply here.

## When data looks wrong

`build_app.py` prints two cross-checks at the end of each run (`Top15 stores amt <= season total`). If either prints `False`, suspect either: a stale temp file from a prior failed fetch (delete `%TEMP%/dcs-ai-cli/duv_*` and re-run), or that the SESN filter changed (the API uses `25F` not `25FW`).
