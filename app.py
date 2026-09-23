"""
Gia phả Vũ tộc — ứng dụng Streamlit
Xem cây phả hệ, thêm/sửa/xóa người với bước xác nhận trước khi lưu.
"""

import json
import itertools
from pathlib import Path

import streamlit as st

DATA_FILE = Path(__file__).parent / "gia_pha_tree.json"

CONF_LABEL = {
    "cao": "🟢 Đã xác nhận",
    "trungbinh": "🟡 Khá chắc",
    "thap": "⚪ Cần kiểm tra",
}
CONF_COLOR = {"cao": "#2f6b3e", "trungbinh": "#b8892b", "thap": "#9a9188"}


# ---------------------------------------------------------------------------
# Load / save
# ---------------------------------------------------------------------------

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def strip_internal(node):
    """Return a copy without the runtime-only _uid field, for saving/export."""
    clean = {k: v for k, v in node.items() if k != "_uid"}
    clean["con"] = [strip_internal(c) for c in node.get("con", [])]
    return clean


def data_to_json_bytes(data):
    export = dict(data)
    export["chi"] = [
        {**chi, "goc": strip_internal(chi["goc"])} for chi in data["chi"]
    ]
    if data.get("nhap_vu_toc") and "goc" in data["nhap_vu_toc"]:
        export["nhap_vu_toc"] = dict(data["nhap_vu_toc"])
        export["nhap_vu_toc"]["goc"] = strip_internal(data["nhap_vu_toc"]["goc"])
    return json.dumps(export, ensure_ascii=False, indent=2).encode("utf-8")


def save_data(data):
    """Write back to the local file. Works when run locally; on Streamlit
    Community Cloud the filesystem resets on every reboot/redeploy, so this
    is a convenience for local use only — always use the download button to
    keep a permanent copy."""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            f.write(data_to_json_bytes(data).decode("utf-8"))
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Tree helpers
# ---------------------------------------------------------------------------

def assign_uids(node, counter):
    node["_uid"] = next(counter)
    for c in node.get("con", []):
        assign_uids(c, counter)


def ensure_uids(data):
    counter = itertools.count(1)
    for chi in data["chi"]:
        assign_uids(chi["goc"], counter)
    if data.get("nhap_vu_toc") and "goc" in data["nhap_vu_toc"]:
        assign_uids(data["nhap_vu_toc"]["goc"], counter)


def build_registry(data):
    """uid -> (node, parent_node_or_None, root_label)"""
    registry = {}

    def walk(node, parent, root_label):
        registry[node["_uid"]] = {"node": node, "parent": parent, "root": root_label}
        for c in node.get("con", []):
            walk(c, node, root_label)

    for chi in data["chi"]:
        walk(chi["goc"], None, chi["ten"])
    if data.get("nhap_vu_toc") and "goc" in data["nhap_vu_toc"]:
        walk(data["nhap_vu_toc"]["goc"], None, data["nhap_vu_toc"].get("ten", "Nhập Vũ tộc"))
    return registry


def breadcrumb(uid, registry):
    parts = []
    cur = uid
    while cur is not None:
        entry = registry[cur]
        n = entry["node"]
        doi = f"đời {n['doi']}" if n.get("doi") is not None else "?"
        parts.append(f"{n['ten']} ({doi})")
        parent = entry["parent"]
        cur = parent["_uid"] if parent is not None else None
    return " → ".join(reversed(parts))


def count_descendants(node):
    return sum(1 + count_descendants(c) for c in node.get("con", []))


def all_options(registry):
    """List of (uid, display_label) sorted roughly by tree order for selectboxes."""
    opts = []
    for uid, entry in registry.items():
        opts.append((uid, f"[{entry['root']}] " + breadcrumb(uid, registry)))
    opts.sort(key=lambda x: x[1])
    return opts


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

TREE_CSS = """
<style>
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
    html = TREE_CSS + (
        "<div class='tree-wrap'><ul class='tree-children top-level'><li>"
        + node_to_html(node, search)
        + "</li></ul></div>"
    )
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Gia phả Vũ tộc", page_icon="🌳", layout="wide")

st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Noto+Serif:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
    html, body, [class*="css"] { font-family: "Noto Serif", Georgia, serif; }
    .block-container { padding-top: 1rem; max-width: 1100px; }
    div[data-testid="stTabs"] button[aria-selected="true"] { color: #7d2828; font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)

if "data" not in st.session_state:
    st.session_state.data = load_data()
    ensure_uids(st.session_state.data)

if "pending" not in st.session_state:
    st.session_state.pending = None  # holds a staged add/edit/delete action

data = st.session_state.data
registry = build_registry(data)

thuy_to = data.get("thuy_to", "")
ho = data.get("ho", "Vũ tộc")

st.markdown(
    f"""
    <div style="
        background: radial-gradient(ellipse at top, #3a2417 0%, #2e1b10 60%);
        margin: -1rem -1rem 24px -1rem;
        padding: 40px 20px 32px;
        text-align: center;
        border-bottom: 4px solid #b8892b;
        border-radius: 0 0 8px 8px;
    ">
        <div style="width:64px;height:3px;background:#d9a544;margin:0 auto 18px;"></div>
        <div style="letter-spacing:0.18em;font-size:0.78rem;color:#d9a544;margin-bottom:8px;">THỦY TỔ</div>
        <h1 style="color:#f1e7cf;font-size:2.4rem;margin:0;font-weight:700;">Gia phả {ho}</h1>
        <div style="margin-top:8px;font-size:1.1rem;color:#e9d9b0;">{thuy_to}</div>
        <div style="margin-top:20px;font-size:0.85rem;color:#e9d9b0;display:flex;justify-content:center;gap:20px;flex-wrap:wrap;">
            <span>🟢 Đã đối chiếu ảnh gốc</span>
            <span>🟡 Khá chắc chắn</span>
            <span>⚪ Suy luận theo cột — cần đối chiếu</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption(data.get("ghi_chu_chung", ""))

tab_view, tab_manage = st.tabs(["📖 Xem cây", "✏️ Thêm / Sửa / Xóa"])

# ---------------- VIEW TAB ----------------
with tab_view:
    search = st.text_input("🔍 Tìm tên", "")
    st.divider()

    chi_titles = [c["ten"] for c in data["chi"]]
    if data.get("nhap_vu_toc"):
        chi_titles.append(data["nhap_vu_toc"].get("ten", "Nhập Vũ tộc"))
    view_tabs = st.tabs(chi_titles)

    for i, chi in enumerate(data["chi"]):
        with view_tabs[i]:
            st.markdown(
                f"<h2 style='color:#7d2828;border-bottom:2px solid #b8892b;"
                f"padding-bottom:6px;'>{chi['ten']}</h2>",
                unsafe_allow_html=True,
            )
            render_node(chi["goc"], search=search)

    if data.get("nhap_vu_toc"):
        with view_tabs[-1]:
            nhap = data["nhap_vu_toc"]
            if nhap.get("ghi_chu"):
                st.caption(nhap["ghi_chu"])
            if "goc" in nhap:
                render_node(nhap["goc"], search=search)

    st.divider()
    st.download_button(
        "⬇️ Tải xuống gia_pha_tree.json hiện tại",
        data=data_to_json_bytes(data),
        file_name="gia_pha_tree.json",
        mime="application/json",
    )

# ---------------- MANAGE TAB ----------------
with tab_manage:
    st.info(
        "Mọi thao tác Thêm / Sửa / Xóa đều phải qua bước **Xem trước** rồi bấm "
        "**Xác nhận** mới thực sự lưu thay đổi."
    )

    action = st.radio("Chọn thao tác", ["Thêm người mới", "Sửa thông tin", "Xóa người"], horizontal=True)
    options = all_options(registry)
    option_labels = [o[1] for o in options]
    uid_by_label = {label: uid for uid, label in options}

    # ---------- ADD ----------
    if action == "Thêm người mới":
        st.subheader("Thêm người mới")
        parent_label = st.selectbox("Là con của ai?", option_labels, key="add_parent")
        parent_uid = uid_by_label[parent_label]
        parent_node = registry[parent_uid]["node"]

        new_name = st.text_input("Tên người mới", key="add_name")
        default_doi = (parent_node["doi"] + 1) if parent_node.get("doi") is not None else None
        new_doi = st.number_input(
            "Đời thứ mấy", value=default_doi or 0, min_value=0, step=1, key="add_doi"
        )
        new_conf = st.selectbox(
            "Độ tin cậy", ["cao", "trungbinh", "thap"],
            format_func=lambda x: CONF_LABEL[x], key="add_conf"
        )
        new_note = st.text_input("Ghi chú (tuỳ chọn)", key="add_note")

        if st.button("👀 Xem trước", key="add_preview"):
            if not new_name.strip():
                st.error("Vui lòng nhập tên.")
            else:
                st.session_state.pending = {
                    "type": "add",
                    "parent_uid": parent_uid,
                    "node": {
                        "ten": new_name.strip(),
                        "doi": int(new_doi) if new_doi else None,
                        "do_tin_cay": new_conf,
                        "con": [],
                        **({"ghi_chu": new_note.strip()} if new_note.strip() else {}),
                    },
                }

        p = st.session_state.pending
        if p and p["type"] == "add":
            st.warning(
                f"Sẽ thêm **{p['node']['ten']}** (đời {p['node']['doi']}) "
                f"làm con của **{breadcrumb(p['parent_uid'], registry)}**."
            )
            c1, c2 = st.columns(2)
            if c1.button("✅ Xác nhận thêm"):
                new_node = dict(p["node"])
                counter = itertools.count(max(registry.keys(), default=0) + 1)
                assign_uids(new_node, counter)
                registry[p["parent_uid"]]["node"].setdefault("con", []).append(new_node)
                save_data(data)
                st.session_state.pending = None
                st.success("Đã thêm thành công.")
                st.rerun()
            if c2.button("❌ Hủy"):
                st.session_state.pending = None
                st.rerun()

    # ---------- EDIT ----------
    elif action == "Sửa thông tin":
        st.subheader("Sửa thông tin một người")
        target_label = st.selectbox("Chọn người cần sửa", option_labels, key="edit_target")
        target_uid = uid_by_label[target_label]
        target_node = registry[target_uid]["node"]

        edit_name = st.text_input("Tên", value=target_node["ten"], key="edit_name")
        edit_doi = st.number_input(
            "Đời thứ mấy", value=target_node.get("doi") or 0, min_value=0, step=1, key="edit_doi"
        )
        edit_conf = st.selectbox(
            "Độ tin cậy", ["cao", "trungbinh", "thap"],
            index=["cao", "trungbinh", "thap"].index(target_node.get("do_tin_cay", "thap")),
            format_func=lambda x: CONF_LABEL[x], key="edit_conf"
        )
        edit_note = st.text_input("Ghi chú", value=target_node.get("ghi_chu", ""), key="edit_note")

        if st.button("👀 Xem trước", key="edit_preview"):
            st.session_state.pending = {
                "type": "edit",
                "uid": target_uid,
                "old": {
                    "ten": target_node["ten"], "doi": target_node.get("doi"),
                    "do_tin_cay": target_node.get("do_tin_cay"), "ghi_chu": target_node.get("ghi_chu", ""),
                },
                "new": {
                    "ten": edit_name.strip(), "doi": int(edit_doi) if edit_doi else None,
                    "do_tin_cay": edit_conf, "ghi_chu": edit_note.strip(),
                },
            }

        p = st.session_state.pending
        if p and p["type"] == "edit":
            st.warning("Xác nhận thay đổi:")
            colA, colB = st.columns(2)
            with colA:
                st.markdown("**Trước:**")
                st.json(p["old"])
            with colB:
                st.markdown("**Sau:**")
                st.json(p["new"])
            c1, c2 = st.columns(2)
            if c1.button("✅ Xác nhận sửa"):
                node = registry[p["uid"]]["node"]
                node["ten"] = p["new"]["ten"]
                node["doi"] = p["new"]["doi"]
                node["do_tin_cay"] = p["new"]["do_tin_cay"]
                if p["new"]["ghi_chu"]:
                    node["ghi_chu"] = p["new"]["ghi_chu"]
                else:
                    node.pop("ghi_chu", None)
                save_data(data)
                st.session_state.pending = None
                st.success("Đã lưu thay đổi.")
                st.rerun()
            if c2.button("❌ Hủy"):
                st.session_state.pending = None
                st.rerun()

    # ---------- DELETE ----------
    elif action == "Xóa người":
        st.subheader("Xóa một người")
        target_label = st.selectbox("Chọn người cần xóa", option_labels, key="del_target")
        target_uid = uid_by_label[target_label]
        target_node = registry[target_uid]["node"]
        n_desc = count_descendants(target_node)

        if n_desc > 0:
            st.error(
                f"⚠️ Người này có **{n_desc} hậu duệ bên dưới**. Xóa sẽ xóa "
                f"luôn TẤT CẢ hậu duệ này khỏi cây."
            )
        confirm_check = st.checkbox("Tôi hiểu và muốn tiếp tục", key="del_check")

        if st.button("👀 Xem trước", key="del_preview", disabled=not confirm_check):
            st.session_state.pending = {
                "type": "delete",
                "uid": target_uid,
                "label": breadcrumb(target_uid, registry),
                "n_desc": n_desc,
            }

        p = st.session_state.pending
        if p and p["type"] == "delete":
            st.warning(f"Sẽ xóa **{p['label']}** và {p['n_desc']} hậu duệ của người này.")
            c1, c2 = st.columns(2)
            if c1.button("✅ Xác nhận xóa"):
                parent = registry[p["uid"]]["parent"]
                if parent is None:
                    st.error("Không thể xóa gốc của một Chi từ đây.")
                else:
                    parent["con"] = [c for c in parent["con"] if c["_uid"] != p["uid"]]
                    save_data(data)
                    st.success("Đã xóa.")
                st.session_state.pending = None
                st.rerun()
            if c2.button("❌ Hủy"):
                st.session_state.pending = None
                st.rerun()
