"""
Gia phả Vũ tộc — ứng dụng Streamlit (bản xem cây)

Dùng ĐÚNG cùng một bộ code sinh HTML như file vu_gia_pha_cay.html độc lập,
rồi nhúng thẳng vào trang Streamlit bằng iframe — đảm bảo giao diện luôn
y hệt nhau, không lệch màu/lệch CSS giữa 2 bản.
"""

import html
import json
import re
import unicodedata
from pathlib import Path

import streamlit as st

DATA_FILE = Path(__file__).parent / "gia_pha_tree.json"


def esc(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    return html.escape(s, quote=True)


def linkify_phone(escaped_text: str) -> str:
    """Biến số điện thoại Việt Nam (đã escape HTML) thành liên kết tel: bấm gọi được."""
    def repl(m):
        digits = re.sub(r"\D", "", m.group(0))
        return f'<a href="tel:+84{digits[1:]}" class="phone-link" target="_top">{m.group(0)}</a>'
    return re.sub(r"0\d{2,3}[.\s]?\d{3}[.\s]?\d{3,4}", repl, escaped_text)


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

    ngay_sinh = node.get("ngay_sinh")
    nam_mat = node.get("nam_mat")
    meta_html = ""
    if ngay_sinh or nam_mat:
        meta_html = (
            f'<div class="person-meta">Sinh: {esc(str(ngay_sinh or "Đang cập nhật"))} '
            f'&nbsp;·&nbsp; Mất: {esc(str(nam_mat or "Đang cập nhật"))}</div>'
        )

    return f'''<div class="tree-node conf-{conf}" data-name="{name}">
        <div class="node-card" onclick="toggleNode(this)">
            {doi_badge}
            <span class="node-name">{name}</span>
            <span class="conf-dot" title="{esc(conf_label)}"></span>
        </div>
        {meta_html}
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
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif:wght@400;600;700&family=Noto+Serif+SC:wght@500;700&display=swap" rel="stylesheet">
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
    padding: 32px 20px 30px;
    color: var(--paper);
  }}
  .hoanh-phi {{
    font-family: "Noto Serif SC", "Noto Serif", serif;
    font-weight: 700;
    font-size: clamp(1.4rem, 3.2vw, 2rem);
    letter-spacing: 0.5em;
    color: var(--gold-bright);
    text-indent: 0.5em; /* bù lại letter-spacing thừa ở cuối chữ cuối */
    margin-bottom: 14px;
  }}
  .hero-inner {{
    display: flex;
    align-items: flex-start;
    justify-content: center;
    gap: clamp(10px, 3vw, 40px);
  }}
  .cau-doi {{
    writing-mode: vertical-rl;
    font-family: "Noto Serif SC", "Noto Serif", serif;
    font-weight: 700;
    font-size: clamp(0.62rem, 2.8vw, 1.25rem);
    letter-spacing: clamp(0.12em, 1.6vw, 0.35em);
    color: var(--gold-bright);
    padding-top: 4px;
    flex-shrink: 0;
  }}
  .hero-center {{ flex: 1; min-width: 0; }}
  .thuy-to-block {{
    display: inline-block;
    margin-top: 22px;
    padding: 10px 28px;
    border-top: 1px solid var(--gold-bright);
    border-bottom: 1px solid var(--gold-bright);
  }}
  .thuy-to-label {{
    letter-spacing: 0.3em;
    font-size: 0.75rem;
    color: var(--gold-bright);
    margin-bottom: 6px;
  }}
  h1.ho-title {{
    font-size: clamp(2rem, 6vw, 3.4rem);
    margin: 0;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }}
  .dia-diem {{
    margin-top: 10px;
    font-size: 0.95rem;
    color: #e9d9b0;
    text-align: center;
  }}
  .thuy-to-name {{
    font-size: 1.5rem;
    color: #f6e9c9;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
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
  .search-hint {{
    text-align: center;
    color: #b39a6d;
    font-size: 0.72rem;
    margin-top: 6px;
  }}
  .person-meta {{
    font-size: 0.68rem;
    color: #8a7a5c;
    margin: 2px 0 0 4px;
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
    max-width: min(1000px, 92%);
    margin: 0 auto 40px;
    background: #fbf5e6;
    border: 1px solid var(--gold);
    border-radius: 6px;
    padding: 14px 18px;
    font-size: 0.85rem;
    color: #4a3a24;
    line-height: 1.5;
    text-align: center;
  }}
  .phone-link {{
    color: var(--seal);
    font-weight: 700;
    text-decoration: underline;
    text-underline-offset: 2px;
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
  <div class="hoanh-phi">{hoanh_phi}</div>
  <div class="hero-inner">
    <div class="cau-doi cau-doi-trai">{cau_doi_trai}</div>
    <div class="hero-center">
      <h1 class="ho-title">Gia phả {ho}</h1>
      <div class="dia-diem">{dia_diem}</div>
      <div class="thuy-to-block">
        <div class="thuy-to-label">THỦY TỔ</div>
        <div class="thuy-to-name">{thuy_to}</div>
      </div>
    <div class="search-bar">
    <input type="text" id="search-input" placeholder="Tìm tên trong gia phả…" onkeydown="if(event.key==='Enter') searchName()">
    <button onclick="searchName()">Tìm</button>
  </div>
  <div id="search-status"></div>
    </div>
    <div class="cau-doi cau-doi-phai">{cau_doi_phai}</div>
  </div>
  <div class="search-hint">Hướng dẫn: Gõ Họ Tên để tìm (hiện dữ liệu chưa có tên đệm; khi bổ sung tên đệm, tìm kiếm vẫn nhận diện gần đúng theo một phần tên).</div>
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
        dia_diem=esc(data.get("dia_diem", "")),
        hoanh_phi=esc(data.get("hoanh_phi", "")),
        cau_doi_phai=esc(data.get("cau_doi_phai", "")),
        cau_doi_trai=esc(data.get("cau_doi_trai", "")),
        ghi_chu_chung=linkify_phone(esc(data.get("ghi_chu_chung", ""))),
        chi_blocks=chi_blocks_html,
        nhap_vu_toc=nhap_html,
    )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Gia phả Vũ tộc", page_icon="🌳", layout="wide")

# Nút "lên đầu trang" — chèn bằng script thật (qua iframe ẩn) để chắc chắn sự
# kiện click được gắn đúng cách, thay vì dựa vào thuộc tính onclick trong
# st.markdown (có thể bị Streamlit lược bỏ khi render).
st.iframe(
    """
    <script>
    (function() {
        const doc = window.parent.document;
        if (doc.getElementById('back-to-top-btn')) return;  // tránh chèn trùng khi rerun
        const btn = doc.createElement('button');
        btn.id = 'back-to-top-btn';
        btn.innerHTML = '&#8593;';
        btn.title = 'Lên đầu trang';
        btn.setAttribute('aria-label', 'Lên đầu trang');
        btn.style.cssText = [
            'position:fixed', 'left:20px', 'bottom:90px', 'width:52px', 'height:52px',
            'border-radius:50%', 'background:#7d2828', 'color:#f6e9c9',
            'border:2px solid #d9a544', 'font-size:1.4rem', 'cursor:pointer',
            'box-shadow:0 3px 10px rgba(0,0,0,0.35)', 'z-index:999999',
            'display:flex', 'align-items:center', 'justify-content:center'
        ].join(';');
        btn.addEventListener('mouseenter', function(){ btn.style.background = '#5c1c1c'; });
        btn.addEventListener('mouseleave', function(){ btn.style.background = '#7d2828'; });
        btn.addEventListener('click', function() {
            const candidates = [
                doc.querySelector('section.main'),
                doc.querySelector('[data-testid="stAppViewContainer"]'),
                doc.querySelector('[data-testid="stMain"]'),
                doc.scrollingElement,
                doc.documentElement,
                doc.body
            ];
            candidates.forEach(function(el) {
                if (el && typeof el.scrollTo === 'function') {
                    el.scrollTo({ top: 0, behavior: 'smooth' });
                }
            });
        });
        doc.body.appendChild(btn);
    })();
    </script>
    """,
    width=1,
    height="content",
)
st.markdown(
    "<style>.block-container{padding:0 !important;max-width:100% !important;}"
    "header[data-testid='stHeader']{background:transparent;}"
    "#MainMenu{visibility:hidden;}"
    "footer{visibility:hidden;}"
    "div[data-testid='stToolbar']{visibility:hidden;}"
    ".placeholder-wrap{max-width:760px;margin:32px auto;padding:0 20px;"
    "font-family:'Noto Serif',Georgia,serif;}"
    ".placeholder-card{background:#f1e7cf;border:1px solid #b8892b;"
    "border-radius:10px;padding:28px 28px;}"
    ".placeholder-card h2{color:#7d2828;margin:0 0 10px;font-size:1.4rem;}"
    ".placeholder-card p{color:#2b2016;line-height:1.6;margin:0 0 14px;}"
    ".placeholder-badge{display:inline-block;background:#e4d5ae;color:#7d2828;"
    "border:1px solid #b8892b;border-radius:20px;padding:4px 14px;"
    "font-size:0.82rem;font-weight:600;}"
    "</style>",
    unsafe_allow_html=True,
)

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)


def placeholder_tab(title, description, badge="🚧 Đang xây dựng"):
    st.markdown(
        f"""
        <div class="placeholder-wrap">
            <div class="placeholder-card">
                <h2>{esc(title)}</h2>
                <p>{esc(description)}</p>
                <span class="placeholder-badge">{esc(badge)}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


TABS = [
    "🌳 Cây gia phả",
    "👤 Hồ sơ thành viên",
    "📅 Giỗ chạp & sự kiện",
    "🔍 Thống kê & tra cứu",
    "🔒 Phân quyền & bảo mật",
    "💰 Quỹ dòng họ",
    "💬 Diễn đàn nội bộ",
    "✏️ Thêm / Sửa / Xóa",
]
tabs = st.tabs(TABS)

with tabs[0]:
    full_html = build_full_html(data)
    st.iframe(full_html, width="stretch", height="content")
    st.markdown('<div class="placeholder-wrap" style="margin-top:0;">', unsafe_allow_html=True)
    st.download_button(
        "⬇️ Tải xuống gia_pha_tree.json hiện tại",
        data=json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"),
        file_name="gia_pha_tree.json",
        mime="application/json",
    )
    st.markdown("</div>", unsafe_allow_html=True)

with tabs[1]:
    placeholder_tab(
        "Hồ sơ thành viên",
        "Lưu trữ thông tin cá nhân từng người: ngày sinh, quê quán, tiểu sử, "
        "hình ảnh, nghề nghiệp, thành tích và vị trí mộ phần. Ngày sinh/năm mất "
        "đã có chỗ hiển thị trong cây (hiện để 'Đang cập nhật' vì chưa có dữ liệu) "
        "— trang hồ sơ chi tiết đầy đủ hơn sẽ có ở bản sau.",
    )

with tabs[2]:
    placeholder_tab(
        "Nhắc lịch giỗ chạp, sự kiện",
        "Tự động thông báo ngày giỗ (theo âm lịch và dương lịch), sinh nhật, "
        "hoặc các buổi họp mặt, lễ hội của dòng họ.",
    )

with tabs[3]:
    placeholder_tab(
        "Thống kê & tra cứu",
        "Tra cứu nhanh thông tin thành viên theo tên, đời thứ mấy, chi phái, "
        "hoặc tìm đường đi giữa các mối quan hệ họ hàng (vd: hai người là "
        "họ hàng đời thứ mấy với nhau). Tìm theo tên đơn giản hiện đã có sẵn "
        "ở tab Cây gia phả.",
    )

with tabs[4]:
    placeholder_tab(
        "Phân quyền & bảo mật",
        "Cho phép nhiều thành viên trong họ cùng xem hoặc đóng góp dữ liệu, "
        "nhưng có cơ chế phân quyền chỉnh sửa để bảo vệ thông tin riêng tư "
        "(ai được xem, ai được sửa).",
    )

with tabs[5]:
    placeholder_tab(
        "Quản lý quỹ dòng họ",
        "Theo dõi thu chi tài chính, đóng góp xây dựng từ đường, quỹ khuyến "
        "học, hoặc các hoạt động thiện nguyện của dòng họ.",
    )

with tabs[6]:
    placeholder_tab(
        "Diễn đàn / Truyền thông nội bộ",
        "Nơi con cháu ở xa cập nhật tin tức, gửi lời chúc mừng, chia sẻ hình "
        "ảnh sinh hoạt chung của gia đình.",
    )

with tabs[7]:
    placeholder_tab(
        "Thêm / Sửa / Xóa (Quản trị)",
        "Thêm người mới, sửa tên/thông tin, hoặc xóa một người khỏi cây — mỗi "
        "thao tác đều cần xem trước và xác nhận trước khi lưu. Tính năng này "
        "từng có ở bản thử nghiệm trước, sẽ đưa trở lại có kiểm soát quyền "
        "truy cập ở phiên bản sau (dành riêng cho admin).",
        badge="🚧 Đang cập nhật — sẽ có ở bản sau",
    )

