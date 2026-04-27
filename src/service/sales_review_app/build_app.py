"""DUVETICA 매출 리뷰 모바일 앱 생성기."""
from __future__ import annotations

import glob
import json
import os
import tempfile
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "src" / "output"
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TMPDIR = Path(tempfile.gettempdir()) / "dcs-ai-cli"

# 빌드 시점에 자동 결정 — 매일 갱신되는 자동화 환경 가정
TODAY = date.today().isoformat()
BASE_DT = (date.today() - timedelta(days=1)).isoformat()

WEEKDAY_KO = ["월", "화", "수", "목", "금", "토", "일"]


def load_latest(prefix: str) -> list[dict]:
    files = sorted(glob.glob(str(TMPDIR / f"{prefix}_*.json")))
    if not files:
        raise FileNotFoundError(prefix)
    with open(files[-1], "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    return payload.get("data", [])


def fmt_won(amt: float) -> str:
    """3,440만원 / 1.45억원 / 18.1억원 형태로 포맷."""
    if amt is None:
        return "-"
    amt = float(amt)
    if amt >= 1e8:
        return f"{amt/1e8:.2f}억"
    if amt >= 1e4:
        return f"{amt/1e4:.0f}만"
    return f"{amt:,.0f}"


def topn(rows: list[dict], key: str, n: int = 20) -> list[dict]:
    return sorted(rows, key=lambda r: r.get(key) or 0, reverse=True)[:n]


def build_season_top(color_rows: list[dict], season_label: str, sesn_code: str) -> dict:
    """color_rows: 각 행이 (PRDT_CD × COLOR_CD) 단위. PRDT_CD로 집계하면서 컬러 리스트 보존."""
    rows = [r for r in color_rows if r.get("SESN") == sesn_code]

    by_style: dict[str, dict] = {}
    for r in rows:
        pc = r.get("PRDT_CD")
        if not pc:
            continue
        s = by_style.get(pc)
        if s is None:
            s = {
                "prdt_cd": pc,
                "prdt_nm": r.get("PRDT_NM"),
                "item_nm": r.get("ITEM_NM"),
                "item_group": r.get("ITEM_GROUP"),
                "tag_price": r.get("TAG_PRICE"),
                "img": r.get("PRDT_IMG_URL"),
                "sale_amt": 0,
                "sale_qty": 0,
                "stor_qty": 0,
                "stock_qty": 0,
                "colors": [],
            }
            by_style[pc] = s
        amt = r.get("AC_SALE_AMT") or 0
        qty = r.get("AC_SALE_QTY") or 0
        stor = r.get("AC_STOR_QTY") or 0
        stk = r.get("STOCK_QTY") or 0
        s["sale_amt"] += amt
        s["sale_qty"] += qty
        s["stor_qty"] += stor
        s["stock_qty"] += stk
        s["colors"].append({
            "color_cd": r.get("COLOR_CD") or "-",
            "amt": amt,
            "qty": qty,
            "stor": stor,
            "stock": stk,
        })

    styles = list(by_style.values())
    for s in styles:
        s["sale_rt"] = (s["sale_qty"] / s["stor_qty"]) if s["stor_qty"] > 0 else 0
        s["colors"].sort(key=lambda c: c["qty"], reverse=True)

    season_total_amt = sum(s["sale_amt"] for s in styles)
    season_total_qty = sum(s["sale_qty"] for s in styles)

    top_amt = sorted(styles, key=lambda s: s["sale_amt"], reverse=True)[:20]
    top_qty = sorted(styles, key=lambda s: s["sale_qty"], reverse=True)[:20]

    def with_rank(items: list[dict]) -> list[dict]:
        return [{**s, "rank": i + 1} for i, s in enumerate(items)]

    return {
        "label": season_label,
        "sesn": sesn_code,
        "total_amt": season_total_amt,
        "total_qty": season_total_qty,
        "style_count": len(styles),
        "top_amt": with_rank(top_amt),
        "top_qty": with_rank(top_qty),
    }


def build_shop_top(shop_rows: list[dict]) -> dict:
    """Top 15 stores → top 5 styles per store."""
    shop_totals: dict[str, dict] = defaultdict(
        lambda: {"shop_nm": None, "area": None, "channel": None, "online": None,
                 "amt": 0, "qty": 0, "styles": []}
    )
    for r in shop_rows:
        shop = r.get("SHOP_NM")
        if not shop:
            continue
        s = shop_totals[shop]
        s["shop_nm"] = shop
        s["area"] = r.get("ANLYS_AREA_NM")
        s["channel"] = r.get("CHANNEL_TYPE")
        s["online"] = r.get("ANLYS_ON_OFF_CLS_NM")
        s["amt"] += r.get("SALE_AMT") or 0
        s["qty"] += r.get("SALE_QTY") or 0
        s["styles"].append({
            "prdt_cd": r.get("PRDT_CD"),
            "prdt_nm": r.get("PRDT_NM"),
            "item_nm": r.get("ITEM_NM"),
            "amt": r.get("SALE_AMT") or 0,
            "qty": r.get("SALE_QTY") or 0,
        })
    shops_sorted = sorted(shop_totals.values(), key=lambda s: s["amt"], reverse=True)[:15]
    for s in shops_sorted:
        s["styles"] = sorted(s["styles"], key=lambda x: x["amt"], reverse=True)[:5]
    return {"shops": shops_sorted}


def build_daily_trend(daily_rows: list[dict]) -> dict:
    """7일치 일별 매출 (시즌별 색구분 가능)."""
    by_dt: dict[str, dict] = defaultdict(lambda: {"amt": 0, "qty": 0, "by_sesn": {}})
    for r in daily_rows:
        d = r.get("SALE_DT")
        if not d:
            continue
        b = by_dt[d]
        b["amt"] += r.get("SALE_AMT") or 0
        b["qty"] += r.get("SALE_QTY") or 0
        sesn = r.get("SESN") or "기타"
        b["by_sesn"].setdefault(sesn, {"amt": 0, "qty": 0})
        b["by_sesn"][sesn]["amt"] += r.get("SALE_AMT") or 0
        b["by_sesn"][sesn]["qty"] += r.get("SALE_QTY") or 0
    items = []
    for d in sorted(by_dt.keys()):
        y, m, day = d.split("-")
        wd = WEEKDAY_KO[date(int(y), int(m), int(day)).weekday()]
        items.append({
            "dt": d,
            "label": f"{int(m)}/{int(day)}({wd})",
            "amt": by_dt[d]["amt"],
            "qty": by_dt[d]["qty"],
            "by_sesn": by_dt[d]["by_sesn"],
        })
    return {"days": items}


def build_yesterday(yesterday_rows: list[dict]) -> dict:
    total_amt = sum((r.get("SALE_AMT") or 0) for r in yesterday_rows)
    total_qty = sum((r.get("SALE_QTY") or 0) for r in yesterday_rows)

    by_sesn: dict[str, dict] = defaultdict(lambda: {"amt": 0, "qty": 0})
    for r in yesterday_rows:
        s = r.get("SESN") or "기타"
        by_sesn[s]["amt"] += r.get("SALE_AMT") or 0
        by_sesn[s]["qty"] += r.get("SALE_QTY") or 0

    sesn_breakdown = sorted(
        ({"sesn": k, **v} for k, v in by_sesn.items()),
        key=lambda x: x["amt"], reverse=True
    )

    def project(r: dict, rank: int) -> dict:
        return {
            "rank": rank,
            "prdt_cd": r.get("PRDT_CD"),
            "prdt_nm": r.get("PRDT_NM"),
            "item_nm": r.get("ITEM_NM"),
            "sesn": r.get("SESN"),
            "amt": r.get("SALE_AMT") or 0,
            "qty": r.get("SALE_QTY") or 0,
        }

    # 시즌 무관 전체 TOP 10
    top_styles = sorted(yesterday_rows, key=lambda r: r.get("SALE_AMT") or 0, reverse=True)[:10]
    top_styles_proj = [project(r, i + 1) for i, r in enumerate(top_styles)]

    # 시즌별 TOP 10
    top_by_sesn: dict[str, list[dict]] = {}
    for sesn_code in ("25F", "26S"):
        rs = [r for r in yesterday_rows if r.get("SESN") == sesn_code]
        rs = sorted(rs, key=lambda r: r.get("SALE_AMT") or 0, reverse=True)[:10]
        top_by_sesn[sesn_code] = [project(r, i + 1) for i, r in enumerate(rs)]

    return {
        "base_dt": BASE_DT,
        "total_amt": total_amt,
        "total_qty": total_qty,
        "by_sesn": sesn_breakdown,
        "top_styles": top_styles_proj,
        "top_by_sesn": top_by_sesn,
    }


def build_season_insights(season: dict, sesn_code: str, yesterday: dict, daily: dict,
                          period_label: str) -> list[dict]:
    """선택 시즌 기준 인사이트. 카드 4장."""
    insights = []
    days = daily["days"]

    # 1. 시즌 전일 매출 vs 직전 6일 시즌 평균
    if days:
        last = days[-1]
        prev = days[:-1]
        y_amt = (last["by_sesn"].get(sesn_code) or {}).get("amt", 0)
        prev_amts = [(d["by_sesn"].get(sesn_code) or {}).get("amt", 0) for d in prev]
        avg_prev = (sum(prev_amts) / len(prev_amts)) if prev_amts else 0
        if avg_prev > 0:
            dp = (y_amt - avg_prev) / avg_prev * 100
            insights.append({
                "title": f"전일 {sesn_code} 매출 vs 직전 6일 평균",
                "value": f"{fmt_won(y_amt)}원",
                "delta": f"{'+' if dp >= 0 else ''}{dp:.1f}%",
                "tone": "up" if dp >= 0 else "down",
                "desc": f"직전 6일 시즌 평균 {fmt_won(avg_prev)}원",
            })
        elif y_amt > 0:
            insights.append({
                "title": f"전일 {sesn_code} 매출",
                "value": f"{fmt_won(y_amt)}원",
                "delta": "",
                "tone": "neutral",
                "desc": "직전 6일 매출 없음",
            })

    # 2. 시즌 누적 매출
    insights.append({
        "title": f"{season['label']} 누적 매출",
        "value": f"{fmt_won(season['total_amt'])}원",
        "delta": f"{season['style_count']} 스타일",
        "tone": "neutral",
        "desc": f"{period_label} 누계",
    })

    # 3. 시즌 누적 판매수량 + TOP20 평균 판매율
    top20_qty = sum(s["sale_qty"] for s in season["top_amt"])
    top20_stor = sum(s["stor_qty"] for s in season["top_amt"])
    avg_rt = (top20_qty / top20_stor * 100) if top20_stor > 0 else 0
    insights.append({
        "title": f"{season['label']} 누적 수량",
        "value": f"{int(season['total_qty']):,}수량",
        "delta": f"TOP20 평균 판매율 {avg_rt:.0f}%",
        "tone": "neutral",
        "desc": f"TOP20 누적 판매 {top20_qty:,}수량",
    })

    # 4. 시즌 BEST 1
    if season["top_amt"]:
        t = season["top_amt"][0]
        insights.append({
            "title": f"{season['label']} BEST 1",
            "value": t["prdt_nm"] or "-",
            "delta": f"{fmt_won(t['sale_amt'])}원",
            "tone": "up",
            "desc": f"{t['item_nm']} · {int(t['sale_qty']):,}수량 · 판매율 {(t['sale_rt']*100):.0f}%",
        })

    return insights


def main():
    color_data = load_latest("duv_25fw_styles_color") + load_latest("duv_26ss_styles_color")
    shop_25fw = load_latest("duv_25fw_shop_styles")
    shop_26ss = load_latest("duv_26ss_shop_styles")
    daily_rows = load_latest("duv_daily_7d")
    yesterday_rows = load_latest("duv_yesterday_styles")

    s_25fw = build_season_top(color_data, "25FW", "25F")
    s_26ss = build_season_top(color_data, "26SS", "26S")

    shops_25fw = build_shop_top(shop_25fw)
    shops_26ss = build_shop_top(shop_26ss)

    daily = build_daily_trend(daily_rows)
    yesterday = build_yesterday(yesterday_rows)

    insights_25fw = build_season_insights(s_25fw, "25F", yesterday, daily, "7/1~4/26")
    insights_26ss = build_season_insights(s_26ss, "26S", yesterday, daily, "1/1~4/26")

    payload = {
        "meta": {
            "brand": "DUVETICA",
            "brand_cd": "V",
            "base_dt": BASE_DT,
            "today": TODAY,
            "generated_at": TODAY,
        },
        "yesterday": yesterday,
        "daily": daily,
        "seasons": {
            "26SS": {
                **s_26ss,
                "insights": insights_26ss,
                "yesterday_top": yesterday["top_by_sesn"].get("26S", []),
                "shops": shops_26ss["shops"],
                "period_label": "1/1~4/26",
            },
            "25FW": {
                **s_25fw,
                "insights": insights_25fw,
                "yesterday_top": yesterday["top_by_sesn"].get("25F", []),
                "shops": shops_25fw["shops"],
                "period_label": "7/1~4/26",
            },
        },
    }

    # JSON은 두 곳에 저장: 빌드 산출물(src/output) + 리포 공개(data/)
    out_json_a = OUTPUT_DIR / "duv_review_data.json"
    out_json_b = DATA_DIR / "duv_review_data.json"
    payload_text = json.dumps(payload, ensure_ascii=False, indent=2)
    out_json_a.write_text(payload_text, encoding="utf-8")
    out_json_b.write_text(payload_text, encoding="utf-8")
    json_path = out_json_b

    # 교차검증
    sum_check_25fw_amt = sum(s["amt"] for s in shops_25fw["shops"]) <= s_25fw["total_amt"] * 1.01
    sum_check_26ss_amt = sum(s["amt"] for s in shops_26ss["shops"]) <= s_26ss["total_amt"] * 1.01
    print(f"[check] 25FW Top15 stores amt <= season total ({sum_check_25fw_amt})")
    print(f"[check] 26SS Top15 stores amt <= season total ({sum_check_26ss_amt})")
    print(f"25FW total: {fmt_won(s_25fw['total_amt'])}원, styles={s_25fw['style_count']}, top1={s_25fw['top_amt'][0]['prdt_nm']}")
    print(f"26SS total: {fmt_won(s_26ss['total_amt'])}원, styles={s_26ss['style_count']}, top1={s_26ss['top_amt'][0]['prdt_nm']}")
    print(f"yesterday total: {fmt_won(yesterday['total_amt'])}원, qty={yesterday['total_qty']}")
    print(f"days in trend: {len(daily['days'])}")
    print(f"saved JSON to {json_path}")
    return payload


if __name__ == "__main__":
    main()
