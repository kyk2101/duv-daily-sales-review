"""DCS API에서 DUVETICA 매출 리뷰 앱 데이터셋 6종 다운로드.

dcs-ai-cli를 subprocess로 호출 (이미 OAuth 인증된 환경 가정).
데이터는 %TEMP%/dcs-ai-cli/ 에 저장되며, build_app.py가 최신 파일을 자동 로드.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import date, timedelta

DCS_CLI = shutil.which("dcs-ai-cli") or r"C:\Users\Admin\AppData\Local\Programs\dcs-ai-cli\dcs-ai-cli.exe"

ENDPOINT_SEASON = "/api/v1/hq/sales_analysis/product/season_wear_style_order_stor_sale_stock_sale_rt"
ENDPOINT_CHANNEL = "/api/v1/hq/sales_analysis/sale_type/channel_product_sale_type"


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

    # 1. 25FW 시즌 스타일×컬러
    fetch(
        "duv_25fw_styles_color",
        ENDPOINT_SEASON,
        {
            "selectors_product": [
                {"system_field_name": f} for f in
                ["BRD_CD", "SESN", "ITEM_GROUP", "ITEM", "ITEM_NM",
                 "PRDT_CD", "PRDT_NM", "TAG_PRICE", "PRDT_IMG_URL"]
            ],
            "selectors_sku": [{"system_field_name": "COLOR_CD"}],
            "metrics": [{"system_field_name": m} for m in
                ["AC_SALE_AMT", "AC_SALE_QTY", "AC_STOR_QTY", "STOCK_QTY"]],
            "filters_product": [
                {"system_code": "V", "system_field_name": "BRD_CD"},
                {"system_code": "25F", "system_field_name": "SESN"},
            ],
            "order_by_clauses": [{"system_field_name": "AC_SALE_AMT", "direction": "DESC"}],
            "periods": {"start_dt": "2025-07-01", "end_dt": end_dt},
            "meta_info": {"data_size_only": False, "data_type": "list", "requested_record_rows": 50000},
        },
    )

    # 2. 26SS 시즌 스타일×컬러
    fetch(
        "duv_26ss_styles_color",
        ENDPOINT_SEASON,
        {
            "selectors_product": [
                {"system_field_name": f} for f in
                ["BRD_CD", "SESN", "ITEM_GROUP", "ITEM", "ITEM_NM",
                 "PRDT_CD", "PRDT_NM", "TAG_PRICE", "PRDT_IMG_URL"]
            ],
            "selectors_sku": [{"system_field_name": "COLOR_CD"}],
            "metrics": [{"system_field_name": m} for m in
                ["AC_SALE_AMT", "AC_SALE_QTY", "AC_STOR_QTY", "STOCK_QTY"]],
            "filters_product": [
                {"system_code": "V", "system_field_name": "BRD_CD"},
                {"system_code": "26S", "system_field_name": "SESN"},
            ],
            "order_by_clauses": [{"system_field_name": "AC_SALE_AMT", "direction": "DESC"}],
            "periods": {"start_dt": "2026-01-01", "end_dt": end_dt},
            "meta_info": {"data_size_only": False, "data_type": "list", "requested_record_rows": 50000},
        },
    )

    # 3. 25FW 매장×스타일
    fetch(
        "duv_25fw_shop_styles",
        ENDPOINT_CHANNEL,
        {
            "selectors_product": [{"system_field_name": f} for f in ["PRDT_CD", "PRDT_NM", "ITEM_NM"]],
            "selectors_channel": [{"system_field_name": f} for f in
                ["SHOP_NM", "ANLYS_AREA_NM", "CHANNEL_TYPE", "ANLYS_ON_OFF_CLS_NM"]],
            "selectors_sale": [],
            "metrics": [{"system_field_name": m} for m in ["SALE_AMT", "SALE_QTY"]],
            "filters_product": [
                {"system_code": "V", "system_field_name": "BRD_CD"},
                {"system_code": "25F", "system_field_name": "SESN"},
            ],
            "filters_channel": [],
            "filters_sale": [{"system_code": "N", "system_field_name": "SALE_RET_YN"}],
            "order_by_clauses": [{"system_field_name": "SALE_AMT", "direction": "DESC"}],
            "periods": {"start_dt": "2025-07-01", "end_dt": end_dt, "time_unit": "day", "is_time_series": False},
            "meta_info": {"data_size_only": False, "data_type": "list", "requested_record_rows": 50000},
        },
    )

    # 4. 26SS 매장×스타일
    fetch(
        "duv_26ss_shop_styles",
        ENDPOINT_CHANNEL,
        {
            "selectors_product": [{"system_field_name": f} for f in ["PRDT_CD", "PRDT_NM", "ITEM_NM"]],
            "selectors_channel": [{"system_field_name": f} for f in
                ["SHOP_NM", "ANLYS_AREA_NM", "CHANNEL_TYPE", "ANLYS_ON_OFF_CLS_NM"]],
            "selectors_sale": [],
            "metrics": [{"system_field_name": m} for m in ["SALE_AMT", "SALE_QTY"]],
            "filters_product": [
                {"system_code": "V", "system_field_name": "BRD_CD"},
                {"system_code": "26S", "system_field_name": "SESN"},
            ],
            "filters_channel": [],
            "filters_sale": [{"system_code": "N", "system_field_name": "SALE_RET_YN"}],
            "order_by_clauses": [{"system_field_name": "SALE_AMT", "direction": "DESC"}],
            "periods": {"start_dt": "2026-01-01", "end_dt": end_dt, "time_unit": "day", "is_time_series": False},
            "meta_info": {"data_size_only": False, "data_type": "list", "requested_record_rows": 50000},
        },
    )

    # 5. 최근 7일 일별×시즌
    fetch(
        "duv_daily_7d",
        ENDPOINT_CHANNEL,
        {
            "selectors_product": [{"system_field_name": "SESN"}],
            "selectors_channel": [],
            "selectors_sale": [],
            "metrics": [{"system_field_name": m} for m in ["SALE_AMT", "SALE_QTY"]],
            "filters_product": [{"system_code": "V", "system_field_name": "BRD_CD"}],
            "filters_channel": [],
            "filters_sale": [{"system_code": "N", "system_field_name": "SALE_RET_YN"}],
            "order_by_clauses": [{"system_field_name": "SALE_AMT", "direction": "DESC"}],
            "periods": {"start_dt": last_7, "end_dt": end_dt, "time_unit": "day", "is_time_series": True},
            "meta_info": {"data_size_only": False, "data_type": "list", "requested_record_rows": 20000},
        },
    )

    # 6. 전일 스타일별
    fetch(
        "duv_yesterday_styles",
        ENDPOINT_CHANNEL,
        {
            "selectors_product": [{"system_field_name": f} for f in
                ["SESN", "ITEM_NM", "PRDT_CD", "PRDT_NM"]],
            "selectors_channel": [],
            "selectors_sale": [],
            "metrics": [{"system_field_name": m} for m in ["SALE_AMT", "SALE_QTY"]],
            "filters_product": [{"system_code": "V", "system_field_name": "BRD_CD"}],
            "filters_channel": [],
            "filters_sale": [{"system_code": "N", "system_field_name": "SALE_RET_YN"}],
            "order_by_clauses": [{"system_field_name": "SALE_AMT", "direction": "DESC"}],
            "periods": {"start_dt": end_dt, "end_dt": end_dt, "time_unit": "day", "is_time_series": False},
            "meta_info": {"data_size_only": False, "data_type": "list", "requested_record_rows": 20000},
        },
    )

    print(f"\n[fetch] all 6 datasets done. base_dt={end_dt}")


if __name__ == "__main__":
    main()
