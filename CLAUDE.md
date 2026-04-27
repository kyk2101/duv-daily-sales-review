# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project purpose

Mobile-first single-page web app showing DUVETICA daily sales review. Phone-bookmarkable URL hosted on GitHub Pages, refreshed once a day. The repository's job is to keep `index.html` (committed at the repo root) up to date with the previous day's data.

Live URL: https://kyk2101.github.io/duv-daily-sales-review/

## How the build pipeline works

Three Python stages, run sequentially:

1. **`src/service/sales_review_app/fetch_data.py`** — Calls `dcs-ai-cli` via subprocess to download **8 datasets** into `%TEMP%/dcs-ai-cli/`. Each call writes a timestamped `<name>_<unix>.json`. The script does not delete old files — `build_app.py` later picks the most recent by glob.

   The 8 datasets fall into two groups:
   - **Inventory backdrop** (2 calls, no STAT_NM filter — for 입고/재고/판매율 metrics): `duv_25fw_inventory`, `duv_26ss_inventory` via `get_season_wear_style_order_stor_sale_stock_sale_rt`
   - **정상 sales** (6 calls, `filters_sale = [{system_code:"정상", system_field_name:"STAT_NM"}]`) via `get_channel_product_sale_type_normal_budget`: `duv_{25fw,26ss}_sales_normal` (style×color), `duv_{25fw,26ss}_shops_normal` (shop×style), `duv_daily_7d_normal`, `duv_yesterday_styles_normal`

2. **`src/service/sales_review_app/build_app.py`** — Loads the 8 latest temp JSONs, builds an inventory index (PRDT_CD → stor_qty/stock_qty), then merges sales data with inventory backdrop. Aggregates into a single tree (per-season top 20 BEST SELLER with per-color breakdown, top 15 stores with each store's top 5 styles, last 7 days daily trend split by SESN, yesterday's per-season top, per-season insights). Writes `data/duv_review_data.json` (committed to git) **and** `src/output/duv_review_data.json` (gitignored mirror).

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
- **STAT_NM = '정상' filter** applied to all sales queries (style ranking, shop ranking, daily trend, yesterday top). Reason: align with MILKY WAY default view. F&F treats `정상` and `리저브` as `정상` per skill rule.
  - 25FW currently shows no '이월' rows in the data (DUVETICA hasn't transitioned 25F to 이월 status yet in `DW_PRDT_SC_NML_BUDGET_STAT`). So 25FW 정상 ≈ 25FW 전체 매출. If '이월' rows ever appear for 25F, they will be excluded from this app's totals — that's intentional.
  - Inventory metrics (AC_STOR_QTY, STOCK_QTY) come from a separate tool that does not split by STAT_NM. So `sale_rt = (정상 sale_qty) / (전체 stor_qty)` — interpret as "정상 판매율" against full inventory.
- For ranking calls (style×color), `selectors_sale` must include `COLOR_CD` to preserve per-color breakdown for the cards. Adding `STAT_NM` selector is optional (filter alone is enough since we only request 정상).
- The fetch endpoints come from DCS knowledge graph intents:
  - `한국 상품 매출 분석 시즌 의류 스타일 랭킹` → `get_season_wear_style_order_stor_sale_stock_sale_rt` (used only for inventory backdrop)
  - `한국 정상/이월 상품/채널 매출 분석` → `get_channel_product_sale_type_normal_budget` (primary sales source, STAT_NM aware)
  - `한국 채널 상품 판매상세 분석` → `get_channel_product_sale_type` (legacy, no longer used in this pipeline)

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

If a season suddenly shows much smaller totals, check whether the `_normal` / `_carryover` STAT_NM filter is what's expected. To verify what STAT_NM values exist for a season, run a diagnostic query without `filters_sale` and with `selectors_sale: [{"system_field_name": "STAT_NM"}]` — it returns one row per (SESN, STAT_NM) so you can see whether 정상 / 이월 are populated.
