# /// script
# requires-python = ">=3.10"
# dependencies = ["pymupdf>=1.24"]
# ///
"""Local manual QA workbench for the 1911 census page mapping.

Inputs: reviewed mapping issues/pages/index in output/build_abs_1911_table_spans/;
        original census PDFs in data/raw/ (read only).
Output: explore/output/2026-09-20_census-qa-dashboard/<batch>_review_decisions.csv.
Run from repo root: uv run explore/2026-09-20_census-qa-dashboard.py
Decisions are a separate review layer; this tool does not change the mapping.
"""

import argparse
import csv
import io
import json
import pathlib
import re
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

import pymupdf

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIELDS = ["doc_id", "pdf_page", "decision", "table_numbers", "notes", "updated_at"]
HTML = r'''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Census page check</title>
<style>
*{box-sizing:border-box}
[hidden]{display:none!important}
body{margin:0;font:16px system-ui,sans-serif;color:#25362f;background:#f4f5f1}
button,input,textarea{font:inherit}
button{cursor:pointer;border:1px solid #c7d0c9;border-radius:7px;padding:10px 14px;background:white;color:inherit}
button:hover{background:#edf2ed}button:disabled{opacity:.5;cursor:default}
header{height:76px;padding:16px 24px;display:flex;align-items:center;justify-content:space-between;background:white;border-bottom:1px solid #dce2dc}
h1{font-size:19px;margin:0}#progress{font-size:13px;color:#637368;margin-top:4px}
nav{display:flex;gap:8px}
main{display:grid;grid-template-columns:minmax(0,1fr) 340px;height:calc(100vh - 76px)}
.viewer{display:flex;flex-direction:column;min-width:0;min-height:0}
.scan-tools{padding:8px 18px;display:flex;flex-wrap:wrap;gap:8px;align-items:center;font-size:13px;color:#637368}
.scan-tools button{padding:5px 12px;font-size:13px}
#scanWrap{overflow:auto;padding:0 18px 18px;flex:1}
#scan{display:block;width:100%;background:white;box-shadow:0 1px 5px #0002}
#scan.loading{opacity:.35}
#contextNotice{padding:10px 18px;background:#fff0d7;font-size:13px}
aside{padding:28px 24px;background:white;border-left:1px solid #dce2dc;overflow:auto}
h2{font-size:22px;margin:0 0 10px}p{line-height:1.5}
.muted{font-size:13px;color:#637368}
label{display:block;font-weight:600;margin:22px 0 8px}
input,textarea{width:100%;padding:11px;border:1px solid #bbc8bd;border-radius:6px;color:inherit;background:white}
textarea{height:92px;resize:vertical}
#save{width:100%;background:#22624b;color:white;border-color:#22624b;margin-top:20px;font-weight:600}
#skip{display:block;width:100%;border:0;margin-top:8px}
#message{font-size:13px;line-height:1.5;min-height:20px;color:#22624b}
#message.error{color:#a12d20}
details{border-top:1px solid #e3e7e1;padding-top:18px;margin-top:24px;font-size:13px;line-height:1.5}
summary{cursor:pointer;color:#526959}
.context-buttons{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}
.context-buttons button{font-size:12px;padding:6px 9px}
#tables p{margin:10px 0}#tables button{padding:3px 6px;font-size:12px;margin-right:6px}
a{color:#22624b}
@media(max-width:750px){header{height:auto;gap:10px;padding:14px}main{height:auto;grid-template-columns:1fr}.viewer{height:65vh}aside{border-left:0;padding:22px}h1{font-size:16px}nav button{padding:8px}}
</style>
<header><div><h1 id="heading">Census page check</h1><div id="progress">Loading…</div></div><nav aria-label="Review items"><button id="back">← Previous review</button><button id="next">Next review →</button></nav></header>
<main>
<section class="viewer" aria-label="Page scan">
  <div class="scan-tools" aria-label="PDF navigation"><button id="prevPage">← Previous PDF page</button><span id="viewLabel"></span><button id="nextPage">Next PDF page →</button><button id="target" hidden>Return to review page</button><button id="zoom">Zoom in</button></div>
  <div id="contextNotice" hidden></div>
  <div id="scanWrap"><img id="scan" alt="Census page to review" hidden><p id="imageError" hidden>Scan could not load. <button id="retry">Retry</button></p></div>
</section>
<aside>
  <h2>Which table is this?</h2>
  <p class="muted" id="hint">Read the table number on the scan.</p>
  <form id="review">
    <label for="tableNumbers">Table number</label>
    <input id="tableNumbers" placeholder="e.g. 68" autocomplete="off">
    <label for="notes">Notes <span class="muted">(if needed)</span></label>
    <textarea id="notes" placeholder="Anything worth noting?"></textarea>
    <button id="save" type="submit">Save & next →</button>
    <button id="skip" type="button">Not sure — skip for now</button>
    <button id="exclude" type="button">This is not a table page</button>
    <button id="unnumbered" type="button" hidden>Unnumbered data table — next</button>
  </form>
  <p id="message" role="status" aria-live="polite"></p>
  <details id="help">
    <summary>Need more context?</summary>
    <p id="evidence"></p>
    <p class="muted" id="candidates"></p>
    <p class="muted">Model notes are not verified. PDF page numbers start at 1.</p>
    <div id="contents" class="context-buttons"></div>
    <div id="tables"></div>
    <p>Multiple tables? Separate numbers with <b>|</b>. A number outside the index needs a note.</p>
    <p><a href="/api/export">Download saved decisions</a></p>
    <p class="muted">Decisions are saved separately. Source data stays unchanged.</p>
  </details>
</aside>
</main>
<script>
let data, rows, index=0, viewPage, dirty=false, saving=false, enlarged=false;
const $=id=>document.getElementById(id);
const key=r=>r.doc_id+':'+r.pdf_page;
const resolved=r=>['accept_model','correct_match','exclude_page','unnumbered_table'].includes(data.decisions[key(r)]?.decision);
const label=r=>r.doc_id.split('_part_')[1].replace(/^[a-z]+_/, '').replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase());

function showPage(n){
  const r=rows[index], doc=data.documents[r.doc_id];
  if(n<1||n>doc.page_count)return;
  viewPage=n;
  $('viewLabel').textContent=`PDF page ${n} of ${doc.page_count}`;
  $('prevPage').disabled=n===1;
  $('nextPage').disabled=n===doc.page_count;
  $('contextNotice').hidden=n===Number(r.pdf_page);
  $('target').hidden=n===Number(r.pdf_page);
  $('contextNotice').textContent=`Context only — your answer is for PDF page ${r.pdf_page}.`;
  $('scan').hidden=false;
  $('scan').classList.add('loading');
  $('imageError').hidden=true;
  $('scan').src='/api/image?doc='+encodeURIComponent(r.doc_id)+'&page='+n;
  $('scanWrap').scrollTo(0,0);
}

function choose(n){
  if(saving||n<0||n>=rows.length)return;
  if(dirty&&!confirm('Leave without saving your changes?'))return;
  index=n;dirty=false;
  const r=rows[index], d=data.decisions[key(r)], doc=data.documents[r.doc_id];
  const count=rows.filter(resolved).length;
  $('heading').textContent=label(r)+' · PDF page '+r.pdf_page;
  $('progress').textContent=`Review ${index+1} of ${rows.length} · ${count} checked`;
  $('back').disabled=index===0;
  $('next').disabled=index===rows.length-1;
  $('hint').textContent=data.batch==='coverage'
    ? 'Check for data tables, including unnumbered ones. Covers, contents and blanks can be marked “No data table”.'
    : r.review_reason+' Current mapping: '+(r.final_table_numbers||'none')+' (unverified).';
  $('tableNumbers').value=d?.table_numbers??r.final_table_numbers;
  $('notes').value=d?.notes||'';
  $('message').className='';
  $('message').textContent=d?(d.decision==='exclude_page'?'Saved: not a table page.':'Previously saved. You can change your answer.'):'';
  $('evidence').textContent=r.evidence_notes;
  $('candidates').textContent='Index candidates: '+r.candidates;
  $('help').open=false;
  $('contents').replaceChildren();
  for(const page of doc.contents_pages){
    const b=document.createElement('button');
    b.textContent='Contents · '+page;b.onclick=()=>showPage(page);
    $('contents').append(b);
  }
  $('tables').replaceChildren();
  for(const t of doc.tables.filter(t=>r.candidates.split(' | ').includes(t.table_number))){
    const p=document.createElement('p'), b=document.createElement('button');
    b.textContent='Table '+t.table_number;
    b.onclick=()=>showPage(Number(t.start_page_index_estimate)+1);
    p.append(b,document.createTextNode(t.table_title+' (estimated start)'));
    $('tables').append(p);
  }
  enlarged=false;$('scan').style.width='100%';$('zoom').textContent='Zoom in';
  showPage(Number(r.pdf_page));
}

async function save(decision){
  if(saving)return;
  saving=true;
  $('review').inert=true;$('exclude').disabled=true;
  $('message').className='';$('message').textContent='Saving…';
  try{
    const r=rows[index];
    const response=await fetch('/api/decision',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
      doc_id:r.doc_id,pdf_page:r.pdf_page,decision,
      table_numbers:['exclude_page','unnumbered_table'].includes(decision)?'':$('tableNumbers').value,
      notes:$('notes').value.trim()||(data.batch==='coverage'
        ? (decision==='exclude_page'?'No data table: front matter, contents or blank.'
          :decision==='unnumbered_table'?'Data table visible without a table number.':''):'')
    })});
    const body=await response.json();
    if(!response.ok)throw Error(body.error);
    data.decisions[key(r)]=body;dirty=false;saving=false;
    let next=-1;
    for(let step=1;step<=rows.length;step++){
      const candidate=(index+step)%rows.length;
      if(!resolved(rows[candidate])){next=candidate;break;}
    }
    choose(next<0?index:next);
    $('message').textContent=next<0?'All pages in this batch checked. Your decisions are saved.':'Saved. Here’s the next unchecked page.';
  }catch(e){
    $('message').className='error';$('message').textContent=e.message;
  }finally{
    saving=false;$('review').inert=false;$('exclude').disabled=false;
  }
}

$('review').onsubmit=e=>{e.preventDefault();save('correct_match');};
$('review').oninput=()=>dirty=true;
$('exclude').onclick=()=>save('exclude_page');
$('unnumbered').onclick=()=>save('unnumbered_table');
$('back').onclick=()=>choose(index-1);
$('next').onclick=()=>choose(index+1);
$('skip').onclick=()=>choose((index+1)%rows.length);
$('prevPage').onclick=()=>showPage(viewPage-1);
$('nextPage').onclick=()=>showPage(viewPage+1);
$('target').onclick=()=>showPage(Number(rows[index].pdf_page));
$('retry').onclick=()=>showPage(viewPage);
$('zoom').onclick=()=>{
  enlarged=!enlarged;$('scan').style.width=enlarged?'175%':'100%';
  $('zoom').textContent=enlarged?'Fit page':'Zoom in';
};
$('scan').onload=()=>$('scan').classList.remove('loading');
$('scan').onerror=()=>{$('scan').hidden=true;$('imageError').hidden=false;};
window.onbeforeunload=e=>{if(dirty){e.preventDefault();e.returnValue='';}};
fetch('/api/data').then(async response=>{
  if(!response.ok)throw Error('Could not load review data');
  data=await response.json();rows=data.rows;
  if(data.batch==='coverage'){
    document.querySelector('h2').textContent='Any data tables here?';
    $('exclude').textContent='No data table — next';
    $('unnumbered').hidden=false;
    $('tableNumbers').placeholder='If numbered, enter e.g. 1 | 2';
  }
  if(!rows.length){
    $('heading').textContent='Review complete';
    $('progress').textContent='No outstanding checks in this batch';
    document.querySelector('nav').hidden=true;
    document.querySelector('.viewer').hidden=true;
    document.querySelector('main').style.gridTemplateColumns='1fr';
    document.querySelector('h2').textContent='All done';
    $('hint').textContent='Your saved decisions are retained.';
    $('review').hidden=true;$('help').hidden=true;
    $('message').replaceChildren(Object.assign(document.createElement('a'),{
      href:'/api/export',textContent:'Download saved decisions'
    }));
    return;
  }
  choose(Math.max(0,rows.findIndex(r=>!resolved(r))));
}).catch(e=>{$('progress').textContent=e.message;});
</script></html>'''


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def mapping_review_rows(batch):
    """Queue uncovered pages or mapping gaps, with neighbouring PDF context."""
    source = ROOT / "output/build_abs_1911_table_spans"
    if batch == "coverage":
        return [{
            "doc_id": r["doc_id"], "pdf_page": r["pdf_page"],
            "final_table_numbers": "", "candidates": "",
            "review_reason": "Page outside the guided inventory.",
            "evidence_notes": r["details"],
        } for r in read_csv(source / "abs_1911_reviewed_issues.csv")
            if r["requires_review"].lower() == "true"
            and r["issue"] == "page_not_in_guided_inventory"]
    index = {(r["doc_id"], r["table_number"]): r
             for r in read_csv(source / "abs_1911_reviewed_table_index.csv")}
    mapped = {(r["doc_id"], r["pdf_page"]): r
              for r in read_csv(source / "abs_1911_reviewed_pages.csv")}
    issues = [r for r in read_csv(source / "abs_1911_reviewed_issues.csv")
              if r["requires_review"].lower() == "true"
              and r["issue"] in {"indexed_table_without_mapped_pages", "non_contiguous_table_assignment"}]
    issues.sort(key=lambda r: r["issue"] != "indexed_table_without_mapped_pages")
    queued = {}
    for issue in issues:
        table = index[(issue["doc_id"], issue["table_number"])]
        if issue["issue"] == "indexed_table_without_mapped_pages":
            pages = [int(table["start_page_index_estimate"]) + 1]
            reason = f"Missing Table {issue['table_number']}: the contents places it near this page. Check all visible tables."
        else:
            assigned = sorted(int(p) for p in issue["pdf_page"].split(" | "))
            pages = sorted({p for left, right in zip(assigned, assigned[1:])
                            if right > left + 1 for p in range(left, right + 1)})
            reason = f"Table {issue['table_number']} has a gap in its mapped pages. Check the gap and its adjoining pages."
        for page in pages:
            key = (issue["doc_id"], str(page))
            if key not in queued:
                current = mapped.get(key, {})
                queued[key] = {
                    "doc_id": key[0], "pdf_page": key[1],
                    "final_table_numbers": current.get("final_table_numbers", ""),
                    "candidates": current.get("candidate_table_numbers", ""),
                    "review_reason": "",
                    "evidence_notes": "Current mapping: " + (current.get("final_table_numbers") or "none")
                        + ". Check neighbouring scans; do not assume the missing table is on every gap page.",
                }
            row = queued[key]
            candidates = [n for n in row["candidates"].split(" | ") if n]
            if issue["table_number"] not in candidates:
                candidates.append(issue["table_number"])
            row["candidates"] = " | ".join(candidates)
            row["review_reason"] = " ".join(filter(None, [row["review_reason"], reason]))
            row["evidence_notes"] += f" Table {issue['table_number']}: {table['table_title']}. Previously mapped pages: {issue['pdf_page'] or 'none'}."
    return list(queued.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", choices=["mapping", "coverage"], default="mapping")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--output-dir", type=pathlib.Path,
                        default=pathlib.Path("explore/output/2026-09-20_census-qa-dashboard"))
    args = parser.parse_args()
    output = ROOT / args.output_dir / f"{args.batch}_review_decisions.csv"
    rows = mapping_review_rows(args.batch)
    targets = {(r["doc_id"], r["pdf_page"]): r for r in rows}
    doc_ids = {r["doc_id"] for r in rows}
    documents = {}
    for t in read_csv(ROOT / "data/intermediate/table_index/abs_1911_numbered_table_index.csv"):
        if t["doc_id"] not in doc_ids:
            continue
        if t["doc_id"] not in documents:
            documents[t["doc_id"]] = {"path": t["local_path"].replace("\\", "/"),
                "page_count": int(t["page_count"]), "contents_pages": [int(p)+1 for p in t["contents_page_indexes"].split(" | ") if p], "tables": []}
        documents[t["doc_id"]]["tables"].append({k: t[k] for k in ("table_number", "table_title", "start_page_index_estimate")})
    decisions = {r["doc_id"]+":"+r["pdf_page"]: r for r in read_csv(output)} if output.exists() else {}
    lock = threading.Lock()
    render_lock = threading.Lock()

    def csv_bytes():
        f = io.StringIO(newline="")
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(decisions.values())
        return f.getvalue().encode("utf-8")

    class Handler(BaseHTTPRequestHandler):
        def send_body(self, body, content_type="application/json", status=200):
            if isinstance(body, (dict, list)):
                body = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            if content_type.startswith("text/csv"):
                self.send_header("Content-Disposition", 'attachment; filename="review_decisions.csv"')
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            url = urlsplit(self.path)
            if url.path == "/":
                return self.send_body(HTML.encode(), "text/html; charset=utf-8")
            if url.path == "/api/data":
                with lock:
                    return self.send_body({"batch": args.batch, "rows": rows, "documents": documents, "decisions": decisions, "output": str(args.output_dir / output.name)})
            if url.path == "/api/export":
                with lock:
                    return self.send_body(csv_bytes(), "text/csv; charset=utf-8")
            if url.path == "/api/image":
                params = parse_qs(url.query)
                try:
                    doc = documents[params["doc"][0]]
                    page = int(params["page"][0])
                    if not 1 <= page <= doc["page_count"]:
                        raise ValueError("Page out of range")
                except (KeyError, ValueError):
                    return self.send_body({"error": "Unknown document or page"}, status=400)
                try:
                    # PyMuPDF must not render concurrently across request threads.
                    with render_lock, pymupdf.open(ROOT / doc["path"]) as pdf:
                        image = pdf[page-1].get_pixmap(matrix=pymupdf.Matrix(2, 2)).tobytes("png")
                    return self.send_body(image, "image/png")
                except Exception as e:
                    print(f"Image render failed: {e}", flush=True)
                    return self.send_body({"error": "Could not render PDF page"}, status=500)
            self.send_body({"error": "Not found"}, status=404)

        def do_POST(self):
            if self.path != "/api/decision":
                return self.send_body({"error": "Not found"}, status=404)
            # Browser writes must originate from this local app, not another site.
            origin = self.headers.get("Origin")
            if origin and origin != "http://" + self.headers.get("Host", ""):
                return self.send_body({"error": "Origin not allowed"}, status=403)
            if self.headers.get("Content-Type") != "application/json":
                return self.send_body({"error": "JSON required"}, status=415)
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 16000:
                    raise ValueError("Invalid request size")
                value = json.loads(self.rfile.read(length))
                if not isinstance(value, dict) or not all(isinstance(value.get(k), str) for k in FIELDS[:-1]):
                    raise ValueError("Invalid review fields")
                target = targets.get((value["doc_id"], value["pdf_page"]))
                if target is None:
                    raise ValueError("Unknown review target")
                decision = value["decision"]
                allowed = {"accept_model", "correct_match", "exclude_page", "needs_manual_extraction_check"}
                if args.batch == "coverage":
                    allowed.add("unnumbered_table")
                if decision not in allowed:
                    raise ValueError("Choose a review decision")
                text = value["table_numbers"].strip()
                if text and not re.fullmatch(r"[1-9][0-9]*(?:\s*[|,]\s*[1-9][0-9]*)*", text):
                    raise ValueError("Use table numbers separated by | or commas")
                numbers = list(dict.fromkeys(re.findall(r"\d+", text)))
                if decision in {"accept_model", "correct_match"} and not numbers:
                    raise ValueError("Enter confirmed table number(s)")
                if decision == "accept_model" and set(numbers) != set(re.findall(r"\d+", target["final_table_numbers"])):
                    raise ValueError("To change the model suggestion, choose Assign table number(s)")
                if decision in {"exclude_page", "unnumbered_table"} and numbers:
                    raise ValueError("This decision cannot have table assignments")
                known = {t["table_number"] for t in documents[value["doc_id"]]["tables"]}
                if (set(numbers)-known or decision in {"exclude_page", "unnumbered_table", "needs_manual_extraction_check"}) and not value["notes"].strip():
                    raise ValueError("Add an evidence note for this decision")
                record = {k: value[k].strip() for k in FIELDS[:-1]}
                record["table_numbers"] = " | ".join(numbers)
                record["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            except (ValueError, TypeError) as e:
                return self.send_body({"error": str(e)}, status=400)
            with lock:
                key = record["doc_id"]+":"+record["pdf_page"]
                previous = decisions.get(key)
                decisions[key] = record
                try:
                    output.parent.mkdir(parents=True, exist_ok=True)
                    temp = output.with_suffix(".tmp")
                    temp.write_bytes(csv_bytes())
                    temp.replace(output)
                except OSError:
                    if previous is None:
                        decisions.pop(key)
                    else:
                        decisions[key] = previous
                    return self.send_body({"error": "Could not save to disk; decision not recorded"}, status=500)
            self.send_body(record)

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"QA dashboard ready: http://localhost:{args.port}", flush=True)
    print(f"Review decisions: {output}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
