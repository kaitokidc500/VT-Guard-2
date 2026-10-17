#!/usr/bin/env python3
"""VT-Guard Buoc 9 - chup anh man hinh dashboard -> reports/step9/screenshots/ (Playwright + Chrome/Chromium da cai).
Dashboard phai dang chay (mac dinh http://localhost:8501). Doi bang chinh cua trang hien du lieu roi moi chup.
Chay: python dashboard/screenshots.py [--url http://localhost:8501] [--channel chrome]
"""
import argparse, os
from pathlib import Path

# (ten file, duong dan, phan tu cho, chieu cao cua so): Streamlit cuon trong khung rieng nen full_page khong du -> dat chieu cao
_KPI, _DF = ".vtg-kpis", "[data-testid='stDataFrame']"
PAGES = [("01_tong_quan_van_hanh", "", _KPI, 1850), ("02_tong_quan_danh_gia", "?mode=danh-gia", _KPI, 2200),
         ("03_hang_doi_van_hanh", "queue", _DF, 1250), ("04_hang_doi_danh_gia", "queue?mode=danh-gia", _DF, 1250),
         ("05_chi_tiet_van_hanh", "detail", _DF, 1800), ("06_chi_tiet_danh_gia", "detail?mode=danh-gia", _DF, 1800),
         ("07_dong_thoi_gian_van_hanh", "timeline", _DF, 2050), ("08_dong_thoi_gian_danh_gia", "timeline?mode=danh-gia", _DF, 2100),
         ("09_luat_van_hanh", "rules", _DF, 1650), ("10_luat_danh_gia", "rules?mode=danh-gia", _DF, 1650),
         ("11_danh_gia_khoa_van_hanh", "evaluation", ".vtg-lock", 500), ("12_danh_gia", "evaluation?mode=danh-gia", _DF, 1150)]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--url", default="http://localhost:8501"); ap.add_argument("--channel", default="chrome")
    ap.add_argument("--only", default=""); a = ap.parse_args()
    from playwright.sync_api import sync_playwright
    home = Path(os.environ.get("VTGUARD_HOME") or Path(__file__).resolve().parent.parent)
    out = home / "reports" / "step9" / "screenshots"; out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(channel=a.channel or None)
        for name, path, sel, h in PAGES:
            if a.only and a.only not in name: continue
            pg = b.new_page(viewport={"width": 1440, "height": h})
            pg.goto(f"{a.url}/{path}"); pg.wait_for_selector(sel, timeout=60000)
            pg.wait_for_load_state("networkidle"); pg.wait_for_timeout(2500)        # de bieu do / bang ve xong
            pg.screenshot(path=str(out / f"{name}.png")); pg.close(); print("chup", name)
        b.close()

if __name__ == "__main__":
    main()
