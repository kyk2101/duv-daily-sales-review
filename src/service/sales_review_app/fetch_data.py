"""DCS API에서 DUVETICA 매출 리뷰 데이터셋 다운로드.

dcs-ai-cli를 subprocess로 호출 (이미 OAuth 인증된 환경 가정).
데이터는 %TEMP%/dcs-ai-cli/ 에 저장되며, build_app.py가 최신 파일을 자동 로드.

데이터 구성:
  매출 (정상 STAT_NM='정상' 필터): get_channel_product_sale_type_normal_budget
  입고/재고 backdrop (필터 없음): get_season_wear_style_order_stor_sale_stock_sale_rt
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import date, timedelta

DCS_CLI = shutil.which("dcs-ai-cli") or r"C:\Users\Admin\AppData\Local\Programs\dcs-ai-cli\dcs-ai-cli.exe"

ENDPOINT_SEASON = "/api/v1/hq/sales_analysis/product/season_wear_style_order_stor_sale_stock_sale_rt"
ENDPOINT_NORMAL_BUDGET = "/api/v1/hq/sales_analysis/sale_type/channel_product_sale_type_normal_budget"

STAT_FILTER_NORMAL = [{"system_code": "정상", "system_field_name": "STAT_NM"}]


def _yesterday() -> str:
    return (date.today() - timedelta(days=1)).isoformat()


def _last_7_start() -> str:
    return (date.today() - timedelta(days=7)).isoformat()


def fetch(name: str, endpoint: str, body: dict) -> None:
    print(f"[fetch] {name} ...", flush=True)
    cmd = [
        DCS_CLI, "fetch",
        "--endpoint", endpoint,
        "--method", "POST",
        "--name", name,
        "--body", json.dumps(body, ensure_ascii=False),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        print(f"[fetch] FAILED {name}\n  stdout: {res.stdout}\n  stderr: {res.stderr}", file=sys.stderr)
        raise RuntimeError(f"fetch failed: {name}")
    print(f"[fetch]   OK: {res.stdout.strip().splitlines()[-1] if res.stdout.strip() else 'done'}")


def main():
    end_dt = _yesterday()
    last_7 = _last_7_start()

    # 1-2. 시즌별 입고/재고 backdrop (정상+이월 합산, 입고/재고 메트릭 추출용)
    for sesn, name, start in [
        ("25F", "duv_25fw_inventory", "2025-07-01"),
        ("26S", "duv_26ss_inventory", "2026-01-01"),
    ]:
        fetch(
            name,
            ENDPOINT_SEASON,
            {
                "selectors_product": [
                    {"system_field_name": f} for f in
                    ["BRD_CD", "SESN", "ITEM_GROUP", "ITEM", "ITEM_NM",
                     "PRDT_CD", "PRDT_NM", "TAG_PRICE", "PRDT_IMG_URL"]
                ],
                "selectors_sku": [],  # PRDT_CD 단위만 (컬러는 매출 도구에서 가져옴)
                "metrics": [{"system_field_name": m} for m in
                    ["AC_STOR_QTY", "AC_STOR_TAG_AMT", "STOCK_QTY"]],
                "filters_product": [
                    {"system_code": "V", "system_field_name": "BRD_CD"},
                    {"system_code": sesn, "system_field_name": "SESN"},
                ],
                "order_by_clauses": [{"system_field_name": "AC_STOR_QTY", "direction": "DESC"}],
                "periods": {"start_dt": start, "end_dt": end_dt},
                "meta_info": {"data_size_only": False, "data_type": "list", "requested_record_rows": 50000},
            },
        )

    # 3-4. 시즌별 정상 매출 × 컬러 (랭킹 + 컬러 breakdown 소스)
    for sesn, name, start in [
        ("25F", "duv_25fw_sales_normal", "2025-07-01"),
        ("26S", "duv_26ss_sales_normal", "2026-01-01"),
    ]:
        fetch(
            name,
            ENDPOINT_NORMAL_BUDGET,
            {
                "selectors_product": [
                    {"system_field_name": f} for f in
                    ["PRDT_CD", "PRDT_NM", "ITEM_NM", "SESN", "ITEM_GROUP",
                     "TAG_PRICE", "PRDT_IMG_URL"]
                ],
                "selectors_channel": [],
                "selectors_sale": [{"system_field_name": "COLOR_CD"}],
                "metrics": [{"system_field_name": m} for m in ["SALE_AMT", "SALE_QTY"]],
                "filters_product": [
                    {"system_code": "V", "system_field_name": "BRD_CD"},
                    {"system_code": sesn, "system_field_name": "SESN"},
                ],
                "filters_channel": [],
                "filters_sale": STAT_FILTER_NORMAL,
                "order_by_clauses": [{"system_field_name": "SALE_AMT", "direction": "DESC"}],
                "periods": {"start_dt": start, "end_dt": end_dt, "time_unit": "day", "is_time_series": False},
                "meta_info": {"data_size_only": False, "data_type": "list", "requested_record_rows": 50000},
            },
        )

    # 5-6. 시즌별 정상 매출 × 매장 (매장별 BEST SELLER)
    for sesn, name, start in [
        ("25F", "duv_25fw_shops_normal", "2025-07-01"),
        ("26S", "duv_26ss_shops_normal", "2026-01-01"),
    ]:
        fetch(
            name,
            ENDPOINT_NORMAL_BUDGET,
            {
                "selectors_product": [{"system_field_name": f} for f in
                    ["PRDT_CD", "PRDT_NM", "ITEM_NM"]],
                "selectors_channel": [{"system_field_name": f} for f in
                    ["SHOP_NM", "ANLYS_AREA_NM", "CHANNEL_TYPE", "ANLYS_ON_OFF_CLS_NM"]],
                "selectors_sale": [],
                "metrics": [{"system_field_name": m} for m in ["SALE_AMT", "SALE_QTY"]],
                "filters_product": [
                    {"system_code": "V", "system_field_name": "BRD_CD"},
                    {"system_code": sesn, "system_field_name": "SESN"},
                ],
                "filters_channel": [],
                "filters_sale": STAT_FILTER_NORMAL,
                "order_by_clauses": [{"system_field_name": "SALE_AMT", "direction": "DESC"}],
                "periods": {"start_dt": start, "end_dt": end_dt, "time_unit": "day", "is_time_series": False},
                "meta_info": {"data_size_only": False, "data_type": "list", "requested_record_rows": 50000},
            },
        )

    # 7. 최근 7일 일별 정상 매출 (시즌별 분리)
    fetch(
        "duv_daily_7d_normal",
        ENDPOINT_NORMAL_BUDGET,
        {
            "selectors_product": [{"system_field_name": "SESN"}],
            "selectors_channel": [],
            "selectors_sale": [],
            "metrics": [{"system_field_name": m} for m in ["SALE_AMT", "SALE_QTY"]],
            "filters_product": [{"system_code": "V", "system_field_name": "BRD_CD"}],
            "filters_channel": [],
            "filters_sale": STAT_FILTER_NORMAL,
            "order_by_clauses": [{"system_field_name": "SALE_AMT", "direction": "DESC"}],
            "periods": {"start_dt": last_7, "end_dt": end_dt, "time_unit": "day", "is_time_series": True},
            "meta_info": {"data_size_only": False, "data_type": "list", "requested_record_rows": 20000},
        },
    )

    # 8. 전일 정상 매출 × 스타일 (시즌별 분리)
    fetch(
        "duv_yesterday_styles_normal",
        ENDPOINT_NORMAL_BUDGET,
        {
            "selectors_product": [{"system_field_name": f} for f in
                ["SESN", "ITEM_NM", "PRDT_CD", "PRDT_NM"]],
            "selectors_channel": [],
            "selectors_sale": [],
            "metrics": [{"system_field_name": m} for m in ["SALE_AMT", "SALE_QTY"]],
            "filters_product": [{"system_code": "V", "system_field_name": "BRD_CD"}],
            "filters_channel": [],
            "filters_sale": STAT_FILTER_NORMAL,
            "order_by_clauses": [{"system_field_name": "SALE_AMT", "direction": "DESC"}],
            "periods": {"start_dt": end_dt, "end_dt": end_dt, "time_unit": "day", "is_time_series": False},
            "meta_info": {"data_size_only": False, "data_type": "list", "requested_record_rows": 20000},
        },
    )

    print(f"\n[fetch] all 8 datasets done. base_dt={end_dt}")


if __name__ == "__main__":
    main()
