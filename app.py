"""
Gia phả Vũ tộc — ứng dụng Streamlit (bản xem cây)

Dùng ĐÚNG cùng một bộ code sinh HTML như file vu_gia_pha_cay.html độc lập,
rồi nhúng thẳng vào trang Streamlit bằng iframe — đảm bảo giao diện luôn
y hệt nhau, không lệch màu/lệch CSS giữa 2 bản.
"""

import html
import json
import unicodedata
from pathlib import Path

import streamlit as st

DATA_FILE = Path(__file__).parent / "gia_pha_tree.json"


def esc(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    return html.escape(s, quote=True)


CONF_LABEL = {
    "cao": "đã đối chiếu ảnh gốc",
    "trungbinh": "khá chắc chắn",
    "thap": "suy luận theo cột — cần đối chiếu",
}


def build_node(node: dict) -> str:
    name = esc(node["ten"])
    doi = node.get("doi")
    conf = node.get("do_tin_cay", "thap")
    conf_label = CONF_LABEL.get(conf, "")
    children = node.get("con", [])

    doi_badge = f'<span class="doi-badge">Đời {doi}</span>' if doi is not None else ""

    children_html = ""
    if children:
        items = "".join(f"<li>{build_node(c)}</li>" for c in children)
        children_html = f'<ul class="tree-children">{items}</ul>'

    return f'''<div class="tree-node conf-{conf}" data-name="{name}">
        <div class="node-card" onclick="toggleNode(this)">
            {doi_badge}
            <span class="node-name">{name}</span>
            <span class="conf-dot" title="{esc(conf_label)}"></span>
        </div>
        {children_html}
    </div>'''


def build_chi_block(chi: dict) -> str:
    return f'''
    <section class="chi-block">
        <h2 class="chi-title">{esc(chi["ten"])}</h2>
        <div class="tree-root">
            <ul class="tree-children top-level">
                <li>{build_node(chi["goc"])}</li>
            </ul>
        </div>
    </section>
    '''


def build_nhap(section: dict) -> str:
    if not section:
        return ""
    ghi_chu = section.get("ghi_chu", "")
    if "goc" in section:
        body = f'<ul class="tree-children top-level"><li>{build_node(section["goc"])}</li></ul>'
    else:
        items = "".join(
            f'<button class="chip" data-name="{esc(p)}" onclick="focusChip(this)">{esc(p)}</button>'
            for p in section.get("nguoi", [])
        )
        body = f'<div class="chip-row">{items}</div>'
    return f'''
    <section class="nhap-section">
        <h2 class="chi-title">{esc(section.get("ten", "Nhập Vũ tộc"))}</h2>
        {f'<p class="ghi-chu">{esc(ghi_chu)}</p>' if ghi_chu else ''}
        {body}
    </section>
    '''


TEMPLATE = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Gia phả {ho} — Thủy tổ {thuy_to}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  :root {{
    --paper: #f1e7cf;
    --paper-dark: #e4d5ae;
    --ink: #2b2016;
    --wood: #4a2f1f;
    --wood-dark: #2e1b10;
    --gold: #b8892b;
    --gold-bright: #d9a544;
    --seal: #7d2828;
    --seal-dark: #5c1c1c;
    --line: #a98a55;
    --conf-cao: #2f6b3e;
    --conf-trungbinh: #b8892b;
    --conf-thap: #9a9188;
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; }}
  body {{
    font-family: "Noto Serif", Georgia, "Times New Roman", serif;
    color: var(--ink);
    background: radial-gradient(ellipse at top, #3a2417 0%, var(--wood-dark) 60%);
  }}
  header.hero {{
    text-align: center;
    padding: 48px 20px 30px;
    color: var(--paper);
  }}
  header.hero::before {{
    content: "";
    display: block;
    width: 64px;
    height: 3px;
    background: var(--gold-bright);
    margin: 0 auto 20px;
  }}
  .thuy-to-label {{
    letter-spacing: 0.18em;
    font-size: 0.78rem;
    color: var(--gold-bright);
    margin-bottom: 8px;
  }}
  h1.ho-title {{
    font-size: clamp(2rem, 6vw, 3.4rem);
    margin: 0;
    font-weight: 700;
  }}
  .thuy-to-name {{
    margin-top: 8px;
    font-size: 1.1rem;
    color: #e9d9b0;
  }}
  .legend {{
    display: flex;
    justify-content: center;
    gap: 18px;
    flex-wrap: wrap;
    margin-top: 22px;
    font-size: 0.78rem;
    color: #e9d9b0;
  }}
  .legend span {{ display: inline-flex; align-items: center; gap: 6px; }}
  .legend .dot {{ width: 9px; height: 9px; border-radius: 50%; display: inline-block; }}
  .search-bar {{
    max-width: 420px;
    margin: 22px auto 0;
    display: flex;
    gap: 8px;
  }}
  .search-bar input {{
    flex: 1;
    padding: 10px 14px;
    border-radius: 4px;
    border: 1px solid var(--gold);
    background: #fbf5e6;
    font-family: inherit;
    font-size: 0.95rem;
  }}
  .search-bar button {{
    padding: 10px 16px;
    border-radius: 4px;
    border: 1px solid var(--gold-bright);
    background: var(--seal);
    color: #f6e9c9;
    cursor: pointer;
    font-family: inherit;
  }}
  #search-status {{
    text-align: center;
    color: #e9d9b0;
    font-size: 0.85rem;
    min-height: 1.2em;
    margin-top: 10px;
  }}
  main {{
    background: var(--paper);
    padding: 44px 4vw 80px;
    border-top: 4px solid var(--gold);
    border-bottom: 4px solid var(--gold);
  }}
  .ghi-chu-chung {{
    max-width: 720px;
    margin: 0 auto 40px;
    background: #fbf5e6;
    border: 1px solid var(--gold);
    border-radius: 6px;
    padding: 14px 18px;
    font-size: 0.85rem;
    color: #4a3a24;
    line-height: 1.5;
  }}
  .chi-block {{
    margin-bottom: 52px;
    overflow-x: auto;
    padding-bottom: 10px;
  }}
  .chi-title {{
    font-size: 1.35rem;
    color: var(--seal);
    letter-spacing: 0.04em;
    margin: 0 0 18px;
    padding-bottom: 8px;
    border-bottom: 2px solid var(--gold);
  }}
  .tree-root {{ min-width: max-content; }}
  ul.tree-children {{
    list-style: none;
    margin: 0;
    padding-left: 28px;
    position: relative;
  }}
  ul.tree-children.top-level {{ padding-left: 0; }}
  ul.tree-children li {{
    position: relative;
    padding: 8px 0 0 20px;
  }}
  ul.tree-children.top-level > li {{ padding-left: 0; }}
  ul.tree-children li::before {{
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    width: 20px;
    height: 22px;
    border-left: 1.5px solid var(--line);
    border-bottom: 1.5px solid var(--line);
  }}
  ul.tree-children.top-level > li::before {{ display: none; }}
  ul.tree-children li:last-child {{ border-left: none; }}
  ul.tree-children li::after {{
    content: "";
    position: absolute;
    left: 0;
    top: 22px;
    bottom: 0;
    width: 0;
    border-left: 1.5px solid var(--line);
  }}
  ul.tree-children li:last-child::after {{ display: none; }}
  .node-card {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #fbf5e6;
    border: 1px solid var(--wood);
    border-radius: 4px;
    padding: 6px 12px;
    cursor: pointer;
    white-space: nowrap;
    transition: box-shadow 0.15s, transform 0.1s;
  }}
  .node-card:hover {{ box-shadow: 0 2px 8px rgba(0,0,0,0.2); transform: translateY(-1px); }}
  .tree-node.highlight > .node-card {{
    background: var(--seal);
    border-color: var(--seal-dark);
    color: #f8ecd0;
  }}
  .doi-badge {{
    font-size: 0.62rem;
    letter-spacing: 0.06em;
    color: var(--gold);
    border: 1px solid var(--gold);
    border-radius: 3px;
    padding: 1px 5px;
  }}
  .tree-node.highlight .doi-badge {{ color: var(--gold-bright); border-color: var(--gold-bright); }}
  .node-name {{ font-size: 0.9rem; }}
  .conf-dot {{ width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }}
  .conf-cao .conf-dot {{ background: var(--conf-cao); }}
  .conf-trungbinh .conf-dot {{ background: var(--conf-trungbinh); }}
  .conf-thap .conf-dot {{ background: var(--conf-thap); }}
  .tree-node.collapsed > ul.tree-children {{ display: none; }}
  .nhap-section {{
    margin: 40px auto 0;
    max-width: 900px;
    text-align: center;
    padding-top: 24px;
    border-top: 2px dashed var(--line);
  }}
  .ghi-chu {{ font-size: 0.85rem; color: #5a4632; max-width: 560px; margin: 0 auto 14px; }}
  .chip-row {{ display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }}
  .chip {{
    font-family: inherit;
    background: #fbf5e6;
    border: 1px solid var(--gold);
    color: var(--ink);
    padding: 6px 12px;
    font-size: 0.85rem;
    border-radius: 20px;
    cursor: pointer;
  }}
  .chip.highlight {{ background: var(--seal); color: #f8ecd0; }}
  footer {{ text-align: center; color: #e9d9b0; font-size: 0.78rem; padding: 22px 20px 40px; }}
</style>
</head>
<body>

<header class="hero">
  <div class="thuy-to-label">THỦY TỔ</div>
  <h1 class="ho-title">Gia phả {ho}</h1>
  <div class="thuy-to-name">{thuy_to}</div>
  <div class="legend">
    <span><span class="dot" style="background:var(--conf-cao)"></span> Đã đối chiếu ảnh gốc</span>
    <span><span class="dot" style="background:var(--conf-trungbinh)"></span> Khá chắc chắn</span>
    <span><span class="dot" style="background:var(--conf-thap)"></span> Suy luận theo cột — cần đối chiếu</span>
  </div>
  <div class="search-bar">
    <input type="text" id="search-input" placeholder="Tìm tên trong gia phả…" onkeydown="if(event.key==='Enter') searchName()">
    <button onclick="searchName()">Tìm</button>
  </div>
  <div id="search-status"></div>
</header>

<main>
  <div class="ghi-chu-chung">{ghi_chu_chung}</div>
  {chi_blocks}
  {nhap_vu_toc}
</main>

<footer>
  Bấm vào một ô tên để thu gọn / mở rộng nhánh con. Chấm màu bên phải mỗi tên thể hiện độ tin cậy của quan hệ cha-con.
</footer>

<script>
  function toggleNode(cardEl) {{
    const node = cardEl.closest('.tree-node');
    const hasChildren = node.querySelector(':scope > ul.tree-children');
    if (hasChildren) {{ node.classList.toggle('collapsed'); }}
    document.querySelectorAll('.tree-node.highlight, .chip.highlight').forEach(n => n.classList.remove('highlight'));
    node.classList.add('highlight');
  }}
  function focusChip(el) {{
    document.querySelectorAll('.tree-node.highlight, .chip.highlight').forEach(n => n.classList.remove('highlight'));
    el.classList.add('highlight');
  }}
  function searchName() {{
    const q = document.getElementById('search-input').value.trim().toLowerCase();
    const status = document.getElementById('search-status');
    document.querySelectorAll('.tree-node.highlight, .chip.highlight').forEach(n => n.classList.remove('highlight'));
    if (!q) {{ status.textContent = ''; return; }}
    const nodeMatches = Array.from(document.querySelectorAll('.tree-node')).filter(
      n => n.dataset.name.toLowerCase().includes(q)
    );
    const chipMatches = Array.from(document.querySelectorAll('.chip')).filter(
      n => n.dataset.name.toLowerCase().includes(q)
    );
    const all = [...nodeMatches, ...chipMatches];
    if (all.length === 0) {{ status.textContent = 'Không tìm thấy "' + q + '"'; return; }}
    all.forEach(n => n.classList.add('highlight'));
    nodeMatches.forEach(n => {{
      let p = n.parentElement;
      while (p) {{
        if (p.classList && p.classList.contains('tree-node')) p.classList.remove('collapsed');
        p = p.parentElement;
      }}
    }});
    all[0].scrollIntoView({{ behavior: 'smooth', block: 'center', inline: 'center' }});
    status.textContent = 'Tìm thấy ' + all.length + ' kết quả cho "' + q + '"';
  }}
  // Tự báo chiều cao thật của trang cho khung Streamlit bên ngoài để không bị cắt/thừa
  function reportHeight() {{
    const h = document.body.scrollHeight;
    if (window.frameElement) {{ window.frameElement.style.height = h + 'px'; }}
  }}
  window.addEventListener('load', reportHeight);
  window.addEventListener('resize', reportHeight);
  new MutationObserver(reportHeight).observe(document.body, {{ childList: true, subtree: true, attributes: true }});
</script>

</body>
</html>
"""


def build_full_html(data: dict) -> str:
    chi_blocks_html = "".join(build_chi_block(c) for c in data.get("chi", []))
    nhap_html = build_nhap(data.get("nhap_vu_toc"))
    return TEMPLATE.format(
        ho=esc(data.get("ho", "")),
        thuy_to=esc(data.get("thuy_to", "")),
        ghi_chu_chung=esc(data.get("ghi_chu_chung", "")),
        chi_blocks=chi_blocks_html,
        nhap_vu_toc=nhap_html,
    )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Gia phả Vũ tộc", page_icon="🌳", layout="wide")
st.markdown(
    "<style>.block-container{padding:0 !important;max-width:100% !important;}"
    "header[data-testid='stHeader']{background:transparent;}</style>",
    unsafe_allow_html=True,
)

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

full_html = build_full_html(data)
st.iframe(full_html, width="stretch", height="content")

st.download_button(
    "⬇️ Tải xuống gia_pha_tree.json hiện tại",
    data=json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"),
    file_name="gia_pha_tree.json",
    mime="application/json",
)
