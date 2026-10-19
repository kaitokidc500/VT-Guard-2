#!/usr/bin/env python3
"""VT-Guard Buoc 9 - chup anh man hinh dashboard -> reports/step9/screenshots/ (Playwright + Chrome/Chromium da cai).
Dashboard phai dang chay (mac dinh http://localhost:8501). Doi bang chinh cua trang hien du lieu roi moi chup.
Chay: python dashboard/screenshots.py [--url http://localhost:8501] [--channel chrome]
"""
import argparse, os
from pathlib import Path

# (ten file, duong dan, phan tu cho, chieu cao cua so): Streamlit cuon trong khung rieng nen full_page khong du -> dat chieu cao
_KPI, _DF = ".vtg-kpis", "[data-testid='stDataFrame']"
# Phan A can luong truc tiep da co canh bao (reports/step9/live/alerts.jsonl: chay replay truoc)
PAGES = [("A1_truc_tiep_hang_doi", "", _DF, 1500), ("A2_chi_tiet_truc_tiep", "detail", _DF, 2000),
         ("A3_dong_thoi_gian", "timeline", _DF, 1900), ("B1_ket_qua_nghien_cuu", "evaluation", ".vtg-reqs", 1500),
         ("B2_chi_tiet_tap_test", "detail?alert=VTG-0001", _DF, 2000), ("B3_luat_sigma", "rules", _DF, 1650)]

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
