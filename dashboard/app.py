"""VT-Guard Buoc 9 - dashboard Streamlit kieu SOC/SIEM (chi doc artefact). Chay tu goc repo:
    streamlit run dashboard/app.py          (giao dien: .streamlit/config.toml)
Duong dan du lieu: bien moi truong VTGUARD_HOME (mac dinh goc repo).
5 trang, HAI PHAN (docs/STEP9-BRIEF.md muc 1-3):
  Phan A - Giam sat SIEM thoi gian thuc (luong live / replay, khong nhan): Truc tiep + Hang doi (man hinh chinh), Chi tiet, Dong thoi gian.
  Phan B - Ket qua nghien cuu (tap test dong bang, co nhan): Ket qua & danh gia (3 yeu cau de tai), Luat Sigma tu sinh."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import streamlit as st                                                  # noqa: E402
from common import T, cached_checksum, cached_pipeline, esc, inject_css  # noqa: E402
import data as D                                                        # noqa: E402

st.set_page_config(page_title="VT-Guard SOC", page_icon=":material/shield:", layout="wide", initial_sidebar_state="expanded")
inject_css()

PAGES = Path(__file__).resolve().parent / "pages"
pg = lambda f, key, icon, **kw: st.Page(str(PAGES / f), title=T(key), icon=icon, **kw)   # noqa: E731
nav = st.navigation({T("navsec_siem"): [pg("live.py", "nav_live", ":material/sensors:", default=True),
                                        pg("detail.py", "nav_detail", ":material/policy:"),
                                        pg("timeline.py", "nav_timeline", ":material/timeline:")],
                     T("navsec_research"): [pg("evaluation.py", "nav_results", ":material/school:"),
                                            pg("rules.py", "nav_rules", ":material/rule:")]})

ASSETS = Path(__file__).resolve().parent / "assets"
st.logo(str(ASSETS / "logo.svg"), size="large", icon_image=str(ASSETS / "icon.svg"))
with st.sidebar:
    st.divider()
    cs = cached_checksum(); n_ok = sum(v is True for v in cs.values()); pi = cached_pipeline(); stt = D.live_status() or {}
    st.markdown(f'<div class="vtg-side">{esc(T("side_part_a"))}<br>{esc(T("side_part_b"))}</div>', unsafe_allow_html=True)
    st.divider()
    st.markdown(f'<div class="vtg-side"><b>{esc(T("side_status"))}</b> &middot; {esc(T("brand_tag"))}<br>'
                f'{esc(T("side_stream"))}: {esc(T("lv_mode_" + (stt.get("mode") or "none")))}'
                + (f' ({esc(T("lv_mode_done"))})' if stt.get("done") else "") + "<br>"
                f'{esc(T("side_model"))}: VT-Seq-ens (5 ONNX)<br>'
                f'{esc(T("side_rules"))}: {pi["n_rules"]} Sigma<br>'
                f'{esc(T("side_fusion"))}: {esc(pi["strategy"])}-{esc(pi["variant"])}, &beta; = {pi["beta"]}<br>'
                f'{esc(T("sidebar_checksum"))}: {n_ok}/{len(cs)} ' + esc(T("sidebar_checksum_ok") if n_ok == len(cs) else T("sidebar_checksum_bad")) +
                f'<br>{esc(T("sidebar_home"))}:<br><code>{esc(D.home().as_posix())}</code></div>', unsafe_allow_html=True)
nav.run()
