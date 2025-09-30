import re, json, html
from collections import OrderedDict
from pathlib import Path

# Paths
PDF_PATH = Path("/mnt/data/VT_BOX_Coding Themes & Quotes (1).pdf")
HTML_OUT = Path("/mnt/data/quote_atlas.html")
JSON_OUT = Path("/mnt/data/quotes.json")

# ---------- 1) Extract text from PDF ----------
def extract_text_from_pdf(pdf_path: Path) -> str:
    text = ""
    try:
        from pdfminer.high_level import extract_text as pdfminer_extract_text
        text = pdfminer_extract_text(str(pdf_path)) or ""
    except Exception:
        text = ""
    if not text.strip():
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(pdf_path))
            txts = []
            for p in reader.pages:
                t = p.extract_text() or ""
                txts.append(t)
            text = "\n".join(txts)
        except Exception:
            text = ""
    return text

raw_text = extract_text_from_pdf(PDF_PATH)
if not raw_text.strip():
    try:
        import pypdf
        reader = pypdf.PdfReader(str(PDF_PATH))
        raw_text = "\n".join([page.extract_text() or "" for page in reader.pages])
    except Exception:
        raw_text = ""

if not raw_text.strip():
    HTML_OUT.write_text("""<!doctype html><meta charset="utf-8">
<title>Quote Atlas (Error)</title>
<h1>Quote Atlas</h1>
<p>Could not extract text from the provided PDF.</p>""", encoding="utf-8")
    result_files = [str(HTML_OUT)]
else:
    # ---------- 2) Normalize and split ----------
    raw_text = raw_text.replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in raw_text.split("\n")]
    norm_lines = []
    for ln in lines:
        if ln or (norm_lines and norm_lines[-1]):
            norm_lines.append(ln)

    # ---------- 3) Parse ----------
    theme_pat = re.compile(r'^Theme\s+(\d+(?:\.\d+)?):\s*(.+?)\s*$', re.IGNORECASE)
    part_pat  = re.compile(r'^(Participant\s*\d+)\s*[:：]\s*(.*)$', re.IGNORECASE)
    quote_lead = re.compile(r'^[“"\'(].*')

    data = OrderedDict()
    current_theme = None
    current_sub = None

    def ensure_theme(num, title=""):
        if num not in data:
            data[num] = {"title": title, "quotes": [], "subs": OrderedDict()}
        else:
            if title and len(title) > len(data[num]["title"]):
                data[num]["title"] = title

    def ensure_sub(num, title=""):
        if not current_theme:
            return
        subs = data[current_theme]["subs"]
        if num not in subs:
            subs[num] = {"title": title, "quotes": []}
        else:
            if title and len(title) > len(subs[num]["title"]):
                subs[num]["title"] = title

    def add_quote(text, participant=None):
        if not current_theme:
            return
        q = text.strip()
        if not q:
            return
        if participant and not q.lower().startswith(participant.lower()):
            q = f"{participant}: {q}"
        if current_sub:
            tgt = data[current_theme]["subs"][current_sub]["quotes"]
        else:
            tgt = data[current_theme]["quotes"]
        if not tgt or tgt[-1] != q:
            tgt.append(q)

    i = 0
    while i < len(norm_lines):
        ln = norm_lines[i]

        m = theme_pat.match(ln)
        if m:
            num = m.group(1)
            title = m.group(2).strip()
            # NEW: grab continuation lines for long headers
            j = i + 1
            while j < len(norm_lines):
                ln2 = norm_lines[j]
                if theme_pat.match(ln2) or part_pat.match(ln2):
                    break
                if ln2:
                    title += " " + ln2.strip()
                j += 1
            i = j

            if "." in num:
                parent = num.split(".")[0]
                ensure_theme(parent)
                current_theme = parent
                current_sub = num
                ensure_sub(current_sub, title)
            else:
                current_theme = num
                current_sub = None
                ensure_theme(current_theme, title)
            continue

        mp = part_pat.match(ln)
        if mp and current_theme:
            participant = mp.group(1)
            text_blob = mp.group(2)
            i += 1
            while i < len(norm_lines):
                ln2 = norm_lines[i]
                if theme_pat.match(ln2) or part_pat.match(ln2):
                    break
                if re.match(r'^\s*Theme\s+\d', ln2, re.IGNORECASE):
                    break
                if ln2:
                    text_blob += " " + ln2
                i += 1
            add_quote(text_blob, participant=participant)
            continue

        if quote_lead.match(ln) and current_theme:
            text_blob = ln
            i += 1
            while i < len(norm_lines):
                ln2 = norm_lines[i]
                if theme_pat.match(ln2) or part_pat.match(ln2) or quote_lead.match(ln2):
                    break
                if ln2:
                    text_blob += " " + ln2
                i += 1
            add_quote(text_blob)
            continue

        i += 1

    def esc(s): return html.escape(s, quote=True)

    flat = []
    for tnum, t in data.items():
        ttitle = t["title"]
        for q in t["quotes"]:
            flat.append({"theme": f"{tnum}: {ttitle}", "sub": "", "quote": q})
        for snum, s in t["subs"].items():
            stitle = s["title"]
            for q in s["quotes"]:
                flat.append({"theme": f"{tnum}: {ttitle}", "sub": f"{snum}: {stitle}", "quote": q})

    # HTML skeleton
    html_head = """<!doctype html><html><head><meta charset="utf-8">
<title>Quote Atlas</title>
<style>
body{font:16px/1.5 system-ui, sans-serif; margin:0; color:#111;}
header{position:sticky;top:0;background:#fff;border-bottom:1px solid #eee;padding:12px 16px;z-index:10;display:flex;gap:12px;align-items:center}
#q{flex:1;padding:10px;border:1px solid #ddd;border-radius:10px;}
.container{display:flex;gap:24px;margin:16px}
.toc{width:280px;max-height:calc(100vh - 90px);overflow:auto;position:sticky;top:70px;border-right:1px solid #f0f0f0;padding-right:12px;}
.toc h3{margin:.5rem 0}
.toc a{display:block;padding:6px 0;color:#333;text-decoration:none}
.toc a:hover{color:#000;text-decoration:underline}
main{flex:1;min-width:0}
.theme{border:1px solid #eee;border-radius:12px;margin:12px 0;background:#fff;overflow:hidden}
.theme > summary{cursor:pointer;padding:14px 16px;font-weight:600;background:#fafafa;}
.subtheme{margin:12px 0 12px 16px;border-left:3px solid #eee;padding-left:10px}
.subtheme > summary{cursor:pointer;padding:10px 12px;font-weight:600;background:#fff;border-radius:8px}
.quote{margin:6px 0;padding:8px 12px;background:#fbfbfb;border:1px solid #f2f2f2;border-radius:8px}
.small{color:#666;font-size:13px}
.count{color:#666;font-size:13px;margin-left:6px}
button.copy{float:right;border:1px solid #ddd;background:#fff;border-radius:8px;padding:4px 8px;cursor:pointer}
button.copy:hover{background:#f7f7f7}
</style>
</head><body>
<header>
  <strong>Quote Atlas</strong>
  <input id="q" placeholder="Search (keyword or Participant #)..."/>
  <span class="small">Press Enter to filter; Clear to reset.</span>
</header>
<div class="container">
  <nav class="toc">
    <h3>Themes</h3>
"""
    toc = []
    for tnum, t in data.items():
        ttitle = esc(t["title"])
        toc.append(f'<a href="#theme-{tnum}">Theme {tnum}: {ttitle}</a>')
    toc_html = "\n".join(toc) + "\n</nav><main>\n"

    body_sections = []
    for tnum, t in data.items():
        ttitle = esc(t["title"])
        theme_id = f"theme-{tnum}"
        tcount = len(t["quotes"]) + sum(len(s["quotes"]) for s in t["subs"].values())
        section = [f'<details class="theme" id="{theme_id}" open><summary>Theme {tnum}: {ttitle} <span class="count">{tcount} quotes</span></summary>']
        for q in t["quotes"]:
            q_esc = esc(q)
            section.append(f'<div class="quote"><button class="copy" onclick="navigator.clipboard.writeText(this.nextElementSibling.innerText)">Copy</button><div>{q_esc}</div></div>')
        for snum, s in t["subs"].items():
            stitle = esc(s["title"])
            scount = len(s["quotes"])
            section.append(f'<details class="subtheme" open><summary>Subtheme {snum}: {stitle} <span class="count">{scount} quotes</span></summary>')
            for q in s["quotes"]:
                q_esc = esc(q)
                section.append(f'<div class="quote"><button class="copy" onclick="navigator.clipboard.writeText(this.nextElementSibling.innerText)">Copy</button><div>{q_esc}</div></div>')
            section.append('</details>')
        section.append('</details>')
        body_sections.append("\n".join(section))

    html_tail = """
</main></div>
<footer>Generated automatically from your PDF.</footer>
<script>
const input = document.getElementById('q');
input.addEventListener('keydown', (e)=>{ if(e.key==='Enter') filter(); });
function filter(){
  const q = input.value.trim().toLowerCase();
  const quotes = document.querySelectorAll('.quote');
  if(!q) { quotes.forEach(el=>el.style.display=''); return; }
  quotes.forEach(el=>{
    const txt = el.innerText.toLowerCase();
    el.style.display = txt.includes(q) ? '' : 'none';
  });
  document.querySelectorAll('.theme').forEach(theme=>{
    const visibleQuotes = theme.querySelectorAll('.quote:not([style*="display: none"])').length;
    theme.open = visibleQuotes > 0;
    theme.querySelectorAll('.subtheme').forEach(sub=>{
      const vis = sub.querySelectorAll('.quote:not([style*="display: none"])').length;
      sub.open = vis > 0;
    });
  });
}
</script>
</body></html>
"""
    final_html = html_head + toc_html + "\n".join(body_sections) + html_tail
    HTML_OUT.write_text(final_html, encoding="utf-8")

    with JSON_OUT.open("w", encoding="utf-8") as f:
        json.dump({"themes": data, "flat": flat}, f, ensure_ascii=False, indent=2)

    result_files = [str(HTML_OUT), str(JSON_OUT)]

result_files
