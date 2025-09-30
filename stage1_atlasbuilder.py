import docx, re, json, html
from pathlib import Path

# ---------- Paths ----------
DOCX_PATH = Path("/mnt/data/Stage 1 Coding.docx")
HTML_OUT = Path("/mnt/data/stage1_atlas.html")
JSON_OUT = Path("/mnt/data/stage1_data.json")

# ---------- Load DOCX ----------
doc = docx.Document(str(DOCX_PATH))

# ---------- Regex Patterns ----------
timestamp_pat = re.compile(r'^\d{2}:\d{2}:\d{2}')  # e.g., 00:03:35
speaker_pat = re.compile(r'^(Morgan\s+Cooley|Morgen\s+Cooley|Participant\s+\d+)\s*:', re.IGNORECASE)
bullet_char_pat = re.compile(r'^[\*\u2022\-]\s+')

# ---------- Data Containers ----------
blocks = []  # list of {timestamps, transcript_lines: [ {id, speaker, text} ], annotations: [ {text, ref_quote_id} ]}
current_block = None

quote_counter = 1
last_quote_id = None
last_kind = None  # 'transcript' or 'annotation'

def start_new_block(ts):
    return {"timestamps": ts, "transcript_lines": [], "annotations": []}

# ---------- Parse Document ----------
for para in doc.paragraphs:
    raw = para.text
    text = raw.strip()
    if not text:
        continue

    # Timestamp line starts a block
    if timestamp_pat.match(text):
        if current_block:
            blocks.append(current_block)
        current_block = start_new_block(text)
        last_kind = None
        continue

    # Create a generic block if we haven't seen a timestamp yet
    if current_block is None:
        current_block = start_new_block("No timestamp")

    # Decide if this is an annotation:
    is_list_style = False
    if para.style is not None:
        style_name = para.style.name or ""
        is_list_style = ("List" in style_name)

    is_bullet_char = bool(bullet_char_pat.match(text))

    # Speaker line?
    if speaker_pat.match(text):
        spk, rest = text.split(":", 1)
        spk = spk.strip()
        line_text = rest.strip()
        current_block["transcript_lines"].append({"id": quote_counter, "speaker": spk, "text": line_text})
        last_quote_id = quote_counter
        quote_counter += 1
        last_kind = "transcript"
        continue

    # Annotation (word list style or explicit bullet char)
    if is_list_style or is_bullet_char:
        if is_bullet_char:
            # strip bullet char
            text = bullet_char_pat.sub("", text, count=1).strip()
        current_block["annotations"].append({"text": text, "ref_quote_id": last_quote_id})
        last_kind = "annotation"
        continue

    # Otherwise continuation of previous kind
    if last_kind == "transcript" and current_block["transcript_lines"]:
        current_block["transcript_lines"][-1]["text"] += " " + text
    elif last_kind == "annotation" and current_block["annotations"]:
        current_block["annotations"][-1]["text"] += " " + text
    else:
        # default: if we have any transcript, continue it; else treat as annotation
        if current_block["transcript_lines"]:
            current_block["transcript_lines"][-1]["text"] += " " + text
            last_kind = "transcript"
        else:
            current_block["annotations"].append({"text": text, "ref_quote_id": last_quote_id})
            last_kind = "annotation"

# Push last
if current_block:
    blocks.append(current_block)

# Remove empty initial "No timestamp" block if it has neither transcript nor annotations
if blocks and blocks[0]["timestamps"] == "No timestamp" and not blocks[0]["transcript_lines"] and not blocks[0]["annotations"]:
    blocks = blocks[1:]

# ---------- Build Derived Structures ----------
# Raw: keep per-line
raw_data = []
for b in blocks:
    if b["transcript_lines"]:
        raw_data.append({
            "timestamps": b["timestamps"],
            "lines": b["transcript_lines"]
        })

# Build lookup for quote id
quote_lookup = {}
for b in blocks:
    for line in b["transcript_lines"]:
        quote_lookup[line["id"]] = {"timestamps": b["timestamps"], "speaker": line["speaker"], "text": line["text"]}

# Annotation list
annotation_data = []
for b in blocks:
    for a in b["annotations"]:
        ref = quote_lookup.get(a["ref_quote_id"]) if a["ref_quote_id"] else None
        annotation_data.append({
            "annotation": a["text"],
            "ref_quote_id": a["ref_quote_id"],
            "ref": ref
        })

# ---------- Write JSON ----------
with JSON_OUT.open("w", encoding="utf-8") as f:
    json.dump({"raw": raw_data, "annotations": annotation_data}, f, ensure_ascii=False, indent=2)

# ---------- Build HTML ----------
def esc(s):
    return html.escape(s, quote=True) if s is not None else ""

html_head = """<!doctype html><html><head><meta charset="utf-8">
<title>Stage 1 Atlas</title>
<style>
body{font:16px/1.5 system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin:0; color:#111;}
header{position:sticky;top:0;background:#fff;border-bottom:1px solid #eee;padding:12px 16px;z-index:10;display:flex;gap:12px;align-items:center;flex-wrap:wrap}
#q{flex:1;min-width:260px;padding:10px;border:1px solid #ddd;border-radius:10px;}
.container{margin:16px}
.toggle{margin-right:12px;cursor:pointer;}
.block{margin:12px 0;padding:12px;border:1px solid #eee;border-radius:10px;background:#fafafa}
.line{padding:6px 10px;margin:6px 0;background:#fff;border:1px solid #ddd;border-radius:8px}
.line .speaker{font-weight:600;margin-right:6px}
.annotation{margin:10px 0;padding:10px;border:1px solid #ccd;background:#eef;border-radius:10px}
.small{color:#666;font-size:13px}
.link{font-size:12px;margin-left:8px}
.count{color:#666;font-size:12px;margin-left:8px}
</style>
</head><body>
<header>
<strong>Stage 1 Atlas</strong>
<input id="q" placeholder="Search (keyword, speaker, or annotation)..."/>
<span class="small">Press Enter to filter; Clear to reset.</span>
<label class="toggle"><input type="radio" name="mode" value="raw" checked> Raw Transcript</label>
<label class="toggle"><input type="radio" name="mode" value="annotations"> Annotation Atlas</label>
</header>
<div class="container" id="content"></div>
<script>
"""

# Inline JSON directly into JS
html_data_var = "const data = " + json.dumps({"raw": raw_data, "annotations": annotation_data}, ensure_ascii=False) + ";"

html_script = """
let mode = "raw";
const content = document.getElementById('content');
const input = document.getElementById('q');

function esc(s){ return s==null ? "" : s.replace(/[&<>"']/g, m=>({"&":"&amp;","<":"&lt;","&gt;":"&gt;","\\"":"&quot;","'":"&#39;"}[m])); }

function render(){
  content.innerHTML = "";
  const q = input.value.trim().toLowerCase();
  if(mode === "raw"){
    data.raw.forEach(b=>{
      const wrapper = document.createElement('div');
      wrapper.className = 'block';
      const count = b.lines.length;
      wrapper.innerHTML = `<div><strong>${esc(b.timestamps)}</strong><span class='count'>${count} lines</span></div>`;
      b.lines.forEach(line=>{
        const div = document.createElement('div');
        div.className = 'line';
        div.id = 'q-' + line.id;
        div.innerHTML = `<span class='speaker'>${esc(line.speaker)}:</span> ${esc(line.text)}`;
        wrapper.appendChild(div);
      });
      if(!q || wrapper.innerText.toLowerCase().includes(q)){
        content.appendChild(wrapper);
      }
    });
  } else {
    data.annotations.forEach(a=>{
      const card = document.createElement('div');
      card.className = 'annotation';
      const ann = esc(a.annotation);
      let ref = a.ref;
      let refHtml = "";
      if(ref){
        refHtml = `<div class='small'>Ref: ${esc(ref.timestamps)} — <strong>${esc(ref.speaker)}</strong> <a class='link' href='#q-${a.ref_quote_id}'>Jump to quote ↗</a></div>
                   <div class='line'><span class='speaker'>${esc(ref.speaker)}:</span> ${esc(ref.text)}</div>`;
      } else {
        refHtml = `<div class='small'>Ref: (no prior quote found)</div>`;
      }
      card.innerHTML = `<div><strong>Note:</strong> ${ann}</div>` + refHtml;
      if(!q || card.innerText.toLowerCase().includes(q)){
        content.appendChild(card);
      }
    });
  }
}
render();

input.addEventListener('keydown', (e)=>{ if(e.key==='Enter') render(); });
document.querySelectorAll('input[name="mode"]').forEach(r=>{
  r.addEventListener('change', (e)=>{ mode = e.target.value; render(); });
});
</script>
</body></html>"""

HTML_OUT.write_text(html_head + html_data_var + html_script, encoding="utf-8")

[str(HTML_OUT), str(JSON_OUT), len(raw_data), len(annotation_data)]
