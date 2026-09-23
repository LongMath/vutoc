"""
Gia phả Vũ tộc — ứng dụng Streamlit (bản xem cây)
Phần Thêm/Sửa/Xóa sẽ làm riêng sau cho khu vực quản trị.
"""

import json
from pathlib import Path

import streamlit as st

DATA_FILE = Path(__file__).parent / "gia_pha_tree.json"

CONF_COLOR = {"cao": "#2f6b3e", "trungbinh": "#b8892b", "thap": "#9a9188"}


def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


TREE_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif:wght@400;600;700&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"] { font-family: "Noto Serif", Georgia, serif; }
.block-container { padding-top: 1rem; max-width: 1100px; }
.tree-wrap {
    overflow-x: auto;
    padding: 12px 4px 24px;
    background: #f1e7cf;
    border-radius: 8px;
}
ul.tree-children {
    list-style: none;
    margin: 0;
    padding-left: 26px;
    position: relative;
}
ul.tree-children.top-level { padding-left: 0; }
ul.tree-children li {
    position: relative;
    padding: 7px 0 0 20px;
}
ul.tree-children.top-level > li { padding-left: 0; }
ul.tree-children li::before {
    content: "";
    position: absolute;
    left: 0; top: 0;
    width: 20px; height: 20px;
    border-left: 1.5px solid #a98a55;
    border-bottom: 1.5px solid #a98a55;
}
ul.tree-children.top-level > li::before { display: none; }
ul.tree-children li::after {
    content: "";
    position: absolute;
    left: 0; top: 20px; bottom: 0; width: 0;
    border-left: 1.5px solid #a98a55;
}
ul.tree-children li:last-child::after { display: none; }
.node-card {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: #fbf5e6;
    border: 1px solid #4a2f1f;
    border-radius: 4px;
    padding: 4px 10px;
    white-space: nowrap;
    font-size: 0.88rem;
    color: #2b2016;
}
.node-card.hl { background: #fff3b0; border-color: #b8892b; }
.doi-badge {
    font-size: 0.62rem;
    color: #b8892b;
    border: 1px solid #b8892b;
    border-radius: 3px;
    padding: 0 4px;
}
.conf-dot { font-size: 0.7rem; }
.ghi-chu-inline { color: #8a7a5c; font-size: 0.78rem; }
</style>
"""


def node_to_html(node, search=""):
    conf = node.get("do_tin_cay", "thap")
    color = CONF_COLOR.get(conf, "#9a9188")
    doi = node.get("doi")
    doi_html = f"<span class='doi-badge'>Đời {doi}</span>" if doi is not None else ""
    name = node["ten"]
    hl = " hl" if (search and search.lower() in name.lower()) else ""
    ghi_chu = node.get("ghi_chu") or node.get("ghi_chu_diadanh")
    ghi_chu_html = f"<span class='ghi-chu-inline'>— {ghi_chu}</span>" if ghi_chu else ""
    card = (
        f"<div class='node-card{hl}'>{doi_html} <b>{name}</b> "
        f"<span class='conf-dot' style='color:{color};'>●</span> {ghi_chu_html}</div>"
    )
    children = node.get("con", [])
    children_html = ""
    if children:
        items = "".join(f"<li>{node_to_html(c, search)}</li>" for c in children)
        children_html = f"<ul class='tree-children'>{items}</ul>"
    return card + children_html


def render_node(node, search=""):
    html = (
        "<div class='tree-wrap'><ul class='tree-children top-level'><li>"
        + node_to_html(node, search)
        + "</li></ul></div>"
    )
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Gia phả Vũ tộc", page_icon="🌳", layout="wide")
st.markdown(TREE_CSS, unsafe_allow_html=True)
st.markdown(
    """
    <style>
    section.main > div.block-container,
    div[data-testid="stAppViewContainer"] .block-container {
        padding-top: 2rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

data = load_data()
thuy_to = data.get("thuy_to", "")
ho = data.get("ho", "Vũ tộc")

st.markdown(
    f"""
    <div style="
        background: radial-gradient(ellipse at top, #3a2417 0%, #2e1b10 60%);
        margin: 0 0 24px 0;
        padding: 40px 20px 32px;
        text-align: center;
        border-bottom: 4px solid #b8892b;
        border-radius: 8px;
    ">
        <div style="width:64px;height:3px;background:#d9a544;margin:0 auto 18px;"></div>
        <div style="letter-spacing:0.18em;font-size:0.78rem;color:#d9a544;margin-bottom:8px;">THỦY TỔ</div>
        <h1 style="color:#f1e7cf;font-size:2.4rem;margin:0;font-weight:700;">Gia phả {ho}</h1>
        <div style="margin-top:8px;font-size:1.1rem;color:#e9d9b0;">{thuy_to}</div>
        <div style="margin-top:20px;font-size:0.85rem;color:#e9d9b0;display:flex;justify-content:center;gap:20px;flex-wrap:wrap;align-items:center;">
            <span><span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#2f6b3e;margin-right:6px;"></span>Đã đối chiếu ảnh gốc</span>
            <span><span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#b8892b;margin-right:6px;"></span>Khá chắc chắn</span>
            <span><span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#9a9188;margin-right:6px;"></span>Suy luận theo cột — cần đối chiếu</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption(data.get("ghi_chu_chung", ""))

search = st.text_input("🔍 Tìm tên", "")
st.divider()

for chi in data["chi"]:
    st.markdown(
        f"<h2 style='color:#7d2828;border-bottom:2px solid #b8892b;"
        f"padding-bottom:6px;'>{chi['ten']}</h2>",
        unsafe_allow_html=True,
    )
    render_node(chi["goc"], search=search)

if data.get("nhap_vu_toc"):
    nhap = data["nhap_vu_toc"]
    st.markdown(
        f"<h2 style='color:#7d2828;border-bottom:2px solid #b8892b;"
        f"padding-bottom:6px;margin-top:32px;'>{nhap.get('ten', 'Nhập Vũ tộc')}</h2>",
        unsafe_allow_html=True,
    )
    if nhap.get("ghi_chu"):
        st.caption(nhap["ghi_chu"])
    if "goc" in nhap:
        render_node(nhap["goc"], search=search)

st.divider()
with open(DATA_FILE, "rb") as f:
    st.download_button(
        "⬇️ Tải xuống gia_pha_tree.json hiện tại",
        data=f.read(),
        file_name="gia_pha_tree.json",
        mime="application/json",
    )
