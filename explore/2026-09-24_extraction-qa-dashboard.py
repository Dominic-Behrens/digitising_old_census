"""Browse unaccepted 1911 census cell candidates beside their source crops.

Inputs: output/render_abs_1911_source_regions/regions.jsonl and
        output/extract_abs_1911_source_regions/{cells,issues,table_coverage,status}.
Output: explore/output/2026-09-24_extraction-qa-dashboard/review.sqlite
        (rebuildable read-only browsing cache; no review decisions are saved).
Run from repo root: python explore/2026-09-24_extraction-qa-dashboard.py
"""

import argparse
import csv
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sqlite3
from urllib.parse import parse_qs, urlsplit
import zlib

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "output/extract_abs_1911_source_regions"
MANIFEST = ROOT / "output/render_abs_1911_source_regions/regions.jsonl"
IMAGE_ROOT = (ROOT / "output/render_abs_1911_source_regions/images").resolve()
CACHE = ROOT / "explore/output/2026-09-24_extraction-qa-dashboard/review.sqlite"
INPUTS = [MANIFEST, *(SOURCE / name for name in
          ("cells.csv", "issues.csv", "table_coverage.csv", "status.json"))]
CELL_FIELDS = ("row_id", "row_label", "resolved_row_label", "row_label_origin",
               "row_label_source_pdf_page", "source_row_text", "table_id",
               "column_index", "column_label", "resolved_column_label",
               "column_label_origin", "column_label_source_pdf_page",
               "raw_value", "legibility", "qa_status", "provider")

HTML = r'''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>1911 extraction QA</title>
<style>
*{box-sizing:border-box}body{margin:0;font:15px system-ui,sans-serif;color:#25342e;background:#f4f6f3}
header{padding:18px 24px;background:#fff;border-bottom:1px solid #dae2d9}h1{font-size:23px;margin:0 0 5px}
p{margin:5px 0;line-height:1.4}.muted{color:#53645b;font-size:13px}.warn{color:#8a3d12}
.controls{display:flex;flex-wrap:wrap;gap:10px;align-items:end;padding:16px 24px;background:#fff;border-bottom:1px solid #dae2d9}
label{display:grid;gap:4px;font-size:13px;font-weight:600}select,button{font:inherit;color:inherit;background:#fff;border:1px solid #bbc9be;border-radius:6px;padding:8px}
select{max-width:300px}button{cursor:pointer}button:hover{background:#e9f1e8}button:disabled{opacity:.5}
.layout{display:grid;grid-template-columns:250px minmax(0,1fr);min-height:70vh}
nav{border-right:1px solid #dae2d9;background:#fff;padding:12px;max-height:calc(100vh - 220px);overflow:auto}
nav button{display:block;width:100%;text-align:left;margin:4px 0;font-size:13px;border:0}nav button.active{background:#dcece0;font-weight:700}
nav .pager{display:flex;gap:5px;position:sticky;top:0;background:#fff;padding-bottom:8px}.pager button{width:50%;border:1px solid #bbc9be;text-align:center}
main{min-width:0;padding:18px 24px}.panel{background:#fff;border:1px solid #dae2d9;border-radius:8px;padding:16px;margin-bottom:16px}
.images{display:grid;gap:12px}.images img{display:block;max-width:none;width:100%;height:auto;background:#fff}
.scan{overflow:auto;border:1px solid #dae2d9}.scan img{min-width:900px}.images details{font-size:13px}
.tablewrap{overflow:auto;max-height:60vh}table{border-collapse:collapse;white-space:nowrap;font-size:13px}th,td{border:1px solid #e0e5de;padding:5px 8px;text-align:left}th{position:sticky;top:0;background:#eef3ed}tr.flag{background:#fff2e4}td.value{font-variant-numeric:tabular-nums;font-weight:600}
.issue{border-left:3px solid #bb6b2b;padding:4px 9px;margin:6px 0;background:#fff6e9;overflow-wrap:anywhere}
@media(max-width:780px){.layout{grid-template-columns:1fr}nav{max-height:190px;border-right:0;border-bottom:1px solid #dae2d9}main{padding:12px}}
</style>
<header><h1>1911 census · extraction QA</h1><p id="summary" class="muted">Loading snapshot…</p>
<p class="warn">Model cells are unaccepted candidates. QA flags are leads, not a measured error rate or a certification.</p></header>
<div class="controls"><label>Volume / part<select id="doc"><option value="">All 14 PDFs</option></select></label>
<label>QA flag<select id="issue"><option value="">Regions with candidate cells</option></select></label>
<label>Table<select id="table"><option value="">All tables</option></select></label>
<button id="random">Random region</button><span id="count" class="muted"></span></div>
<div class="layout"><nav><div class="pager"><button id="prev">← Previous</button><button id="next">Next →</button></div><div id="regions"></div></nav>
<main><div id="notice" class="muted">Select a region to compare its crop and cells.</div><section id="detail" hidden>
<div class="panel"><h2 id="title"></h2><p id="meta" class="muted"></p><p id="source" class="muted"></p></div>
<div class="panel images"><details id="heading"><summary>Printed heading context (show/hide)</summary><div class="scan"><img id="headerImage" alt="Printed column heading crop"></div></details><div class="scan"><img id="cropImage" alt="Marked original census source rows"></div></div>
<div class="panel"><h3>Candidate transcription</h3><p class="muted">The left rN marks were added to locate rows, not printed labels. Linked labels come from another source location; they are not model output for this crop. Scroll sideways for wide tables.</p><div class="tablewrap"><table><thead><tr><th>Row</th><th>Local row label</th><th>Linked row label</th><th>Column</th><th>Local heading</th><th>Linked heading</th><th>Raw mark</th><th>QA</th></tr></thead><tbody id="cells"></tbody></table></div></div>
<div class="panel"><h3>QA leads <span id="issueCount"></span></h3><div id="issues"></div></div>
</section></main></div>
<script>
const $=id=>document.getElementById(id);let offset=0,chosen='',items=[];
const initialRegion=decodeURIComponent(location.hash.slice(1));
const text=(tag,value)=>{const el=document.createElement(tag);el.textContent=value??'';return el};
async function get(path){const r=await fetch(path);if(!r.ok)throw Error((await r.json()).error||r.statusText);return r.json()}
function nice(s){const m=s.match(/^1911_census_volume_(ii|iii)_part_([ivx]+)_(.*)$/);return m?`Volume ${m[1].toUpperCase()} · Part ${m[2].toUpperCase()} · ${m[3].replaceAll('_',' ').replace(/\b[a-z]/g,c=>c.toUpperCase())}`:s}
async function setup(){
 const s=await get('/api/summary');$('summary').textContent=`Snapshot ${s.timestamp||'unknown'} · ${s.completed_regions??'?'} / ${s.total_regions??'?'} regions returned · ${s.failed_regions??'?'} failed · ${s.remaining_regions??'?'} remaining · ${s.candidate_cells??'?'} candidate cells · 0 accepted tables`;
 for(const doc of s.documents)$('doc').add(new Option(nice(doc),doc));
 for(const issue of s.issues)$('issue').add(new Option(`${issue.issue} (${issue.n})`,issue.issue));
 await tables();await list();}
async function tables(){const rows=await get('/api/tables?doc='+encodeURIComponent($('doc').value));const select=$('table'),before=select.value;select.replaceChildren(new Option('All tables',''));for(const r of rows)select.add(new Option(`${r.table_id.split('::').at(-1)} · ${r.table_title} (${r.returned_regions}/${r.regions} regions, ${r.status})`,r.table_id));select.value=before;}
function query(extra=''){const params=new URLSearchParams({doc:$('doc').value,issue:$('issue').value,table:$('table').value,offset:String(offset)});return '/api/regions?'+params+extra}
async function list(){const data=await get(query());items=data.rows;$('count').textContent=`${data.total.toLocaleString()} matching regions`;$('prev').disabled=offset===0;$('next').disabled=offset+items.length>=data.total;
 const box=$('regions');box.replaceChildren();for(const r of items){const b=text('button',`PDF p${r.pdf_page} · ${r.region_id.split('::').at(-1)} · ${r.cell_count} cells · ${r.issue_count} flags`);b.title=r.region_id;b.className=r.region_id===chosen?'active':'';b.onclick=()=>show(r.region_id);box.append(b)}
 if(items.length){if(!items.some(r=>r.region_id===chosen))chosen=items[0].region_id;await show(chosen)}else{$('detail').hidden=true;$('notice').hidden=false;$('notice').textContent='No regions match these filters.'}}
async function show(id){chosen=id;const d=await get('/api/region?id='+encodeURIComponent(id));$('detail').hidden=false;$('notice').hidden=true;$('title').textContent=`${nice(d.doc_id)} · PDF page ${d.pdf_page} · ${id.split('::').at(-1)}`;
 $('meta').textContent=`Table IDs: ${d.table_ids.join(', ')||'unresolved'} · ${d.cell_count} candidate cells · ${d.issue_count} QA flags`;
 $('source').textContent=d.source_pdf;const src='/api/image?id='+encodeURIComponent(id);$('cropImage').src=src+'&kind=crop';$('heading').hidden=!d.header_image_path;if(d.header_image_path)$('headerImage').src=src+'&kind=header';
 const flagged=new Set(d.issues.filter(x=>x.row_id).map(x=>x.row_id)),tbody=$('cells');tbody.replaceChildren();for(const c of d.cells){const tr=document.createElement('tr');if(flagged.has(c.row_id)||c.qa_status==='needs_source_review')tr.className='flag';
 const linkedRow=c.resolved_row_label&&c.resolved_row_label!==c.row_label?c.resolved_row_label:'—',linkedColumn=c.resolved_column_label&&c.resolved_column_label!==c.column_label?c.resolved_column_label:'—';
 for(const value of [c.row_id.split('::').at(-1),c.row_label||'—',linkedRow,c.column_index,c.column_label||'—',linkedColumn,c.raw_value,c.qa_status])tr.append(text('td',value));
 tr.children[2].title=linkedRow==='—'?'':`${c.row_label_origin} · PDF p${c.row_label_source_pdf_page}`;
 tr.children[5].title=linkedColumn==='—'?'':`${c.column_label_origin} · PDF p${c.column_label_source_pdf_page}`;
 tr.children[6].className='value';tbody.append(tr)}
 $('issueCount').textContent=`(${d.issues.length})`;const box=$('issues');box.replaceChildren();for(const issue of d.issues){const p=text('p',`${issue.row_id?issue.row_id.split('::').at(-1)+' · ':''}${issue.issue}${issue.details?' — '+issue.details:''}`);p.className='issue';box.append(p)}if(!d.issues.length)box.append(text('p','No automated flag. This does not mean the cells are correct.'));
 for(const b of $('regions').querySelectorAll('button'))b.classList.toggle('active',b.title===id);history.replaceState(null,'','#'+encodeURIComponent(id));}
$('doc').onchange=async()=>{offset=0;chosen='';await tables();await list()};$('issue').onchange=$('table').onchange=()=>{offset=0;chosen='';list()};$('prev').onclick=()=>{offset=Math.max(0,offset-30);chosen='';list()};$('next').onclick=()=>{offset+=30;chosen='';list()};
$('random').onclick=async()=>{const d=await get(query('&random=1'));if(d.rows.length){const r=d.rows[0],box=$('regions'),b=text('button',`Random · PDF p${r.pdf_page} · ${r.region_id.split('::').at(-1)}`);b.title=r.region_id;b.onclick=()=>show(r.region_id);box.prepend(b);await show(r.region_id)}};
setup().then(async()=>{if(initialRegion){try{await show(initialRegion)}catch{}}}).catch(e=>{$('summary').textContent=e.message});
</script></html>'''


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        yield from csv.DictReader(stream)


def signature():
    return json.dumps({"version": 3, "inputs": [
        (str(p.relative_to(ROOT)), p.stat().st_size, p.stat().st_mtime_ns)
        for p in INPUTS]}, separators=(",", ":"))


def prepare_cache():
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    stamp = signature()
    if CACHE.exists():
        with sqlite3.connect(CACHE) as db:
            if db.execute("SELECT value FROM metadata WHERE key='inputs'").fetchone() == (stamp,):
                return
    temp = CACHE.with_suffix(".tmp")
    temp.unlink(missing_ok=True)
    with sqlite3.connect(temp) as db:
        db.executescript("""
            CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE regions (region_id TEXT PRIMARY KEY, doc_id TEXT, pdf_page INTEGER,
                source_pdf TEXT, table_ids TEXT, image_path TEXT, header_image_path TEXT,
                cell_count INTEGER DEFAULT 0, issue_count INTEGER DEFAULT 0, cells BLOB);
            CREATE TABLE issues (region_id TEXT, row_id TEXT, issue TEXT, details TEXT);
            CREATE TABLE tables (table_id TEXT PRIMARY KEY, doc_id TEXT, table_title TEXT,
                status TEXT, regions INTEGER, returned_regions INTEGER, candidate_cells INTEGER,
                qa_issues INTEGER);
            CREATE TABLE region_tables (region_id TEXT, table_id TEXT);
        """)
        with MANIFEST.open(encoding="utf-8") as stream:
            for line in stream:
                r = json.loads(line)
                db.execute("INSERT INTO regions(region_id,doc_id,pdf_page,source_pdf,table_ids,image_path,header_image_path) VALUES(?,?,?,?,?,?,?)",
                           (r["region_id"], r["doc_id"], r["pdf_page"], r["source_pdf"],
                            json.dumps(r["table_ids"]), r["image_path"], r["header_image_path"]))
                db.executemany("INSERT INTO region_tables VALUES(?,?)",
                               ((r["region_id"], table_id) for table_id in r["table_ids"]))
        db.execute("CREATE INDEX region_table_index ON region_tables(table_id,region_id)")
        print("Indexing candidate cells (one pass)…", flush=True)
        previous, cells = None, []
        def flush():
            if previous is not None:
                blob = zlib.compress(json.dumps(cells, ensure_ascii=False, separators=(",", ":")).encode())
                db.execute("UPDATE regions SET cell_count=?,cells=? WHERE region_id=?", (len(cells), blob, previous))
        for row in read_csv(SOURCE / "cells.csv"):
            rid = row["region_id"]
            if previous is not None and rid != previous:
                flush()
                cells = []
            previous = rid
            cells.append([row[k] for k in CELL_FIELDS])
        flush()
        db.executemany("INSERT INTO issues VALUES(?,?,?,?)",
                       ((r["region_id"], r["row_id"], r["issue"], r["details"])
                        for r in read_csv(SOURCE / "issues.csv")))
        db.execute("CREATE INDEX issue_filter ON issues(issue,region_id)")
        db.execute("CREATE INDEX issue_region ON issues(region_id)")
        db.execute("UPDATE regions SET issue_count=(SELECT count(*) FROM issues WHERE issues.region_id=regions.region_id)")
        db.executemany("INSERT INTO tables VALUES(?,?,?,?,?,?,?,?)",
                       ((r["table_id"], r["table_id"].split("::")[0], r["table_title"], r["status"],
                         int(r["regions"]), int(r["returned_regions"]), int(r["candidate_cells"]),
                         int(r["qa_issues"])) for r in read_csv(SOURCE / "table_coverage.csv")))
        db.execute("INSERT INTO metadata VALUES('inputs',?)", (stamp,))
        db.execute("INSERT INTO metadata VALUES('status',?)", ((SOURCE / "status.json").read_text(encoding="utf-8"),))
    if signature() != stamp:
        temp.unlink(missing_ok=True)
        raise RuntimeError("Extraction outputs changed during indexing; restart after replay finishes")
    temp.replace(CACHE)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    prepare_cache()

    class Handler(BaseHTTPRequestHandler):
        def send_body(self, body, mime="application/json", code=200):
            if isinstance(body, (dict, list)):
                body = json.dumps(body, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            url = urlsplit(self.path)
            q = parse_qs(url.query)
            one = lambda key: q.get(key, [""])[0]
            if url.path == "/":
                return self.send_body(HTML.encode(), "text/html; charset=utf-8")
            with sqlite3.connect(CACHE.as_uri() + "?mode=ro", uri=True) as db:
                db.row_factory = sqlite3.Row
                if url.path == "/api/summary":
                    status = json.loads(db.execute("SELECT value FROM metadata WHERE key='status'").fetchone()[0])
                    status["documents"] = [r[0] for r in db.execute("SELECT DISTINCT doc_id FROM regions ORDER BY doc_id")]
                    status["issues"] = [dict(r) for r in db.execute("""
                        SELECT CASE WHEN instr(issue,':')>0 THEN substr(issue,1,instr(issue,':')-1)
                                    ELSE issue END issue,count(*) n FROM issues
                        GROUP BY 1 ORDER BY n DESC""")]
                    return self.send_body(status)
                if url.path == "/api/tables":
                    doc = one("doc")
                    rows = db.execute("SELECT * FROM tables WHERE (?='' OR doc_id=?) ORDER BY doc_id,table_id", (doc, doc))
                    return self.send_body([dict(r) for r in rows])
                if url.path == "/api/regions":
                    doc, issue, table = one("doc"), one("issue"), one("table")
                    try:
                        offset = int(one("offset") or 0)
                        if not 0 <= offset <= 16603:
                            raise ValueError
                    except ValueError:
                        return self.send_body({"error": "Invalid offset"}, code=400)
                    where = ["(?='' OR r.doc_id=?)", "(?='' OR EXISTS(SELECT 1 FROM region_tables t WHERE t.region_id=r.region_id AND t.table_id=?))",
                             "(?='' OR EXISTS(SELECT 1 FROM issues i WHERE i.region_id=r.region_id AND (i.issue=? OR i.issue LIKE ?||':%')))"]
                    if not issue:
                        where.append("r.cell_count>0")
                    sql = " FROM regions r WHERE " + " AND ".join(where)
                    params = (doc, doc, table, table, issue, issue, issue)
                    total = db.execute("SELECT count(*)" + sql, params).fetchone()[0]
                    order = " ORDER BY random() LIMIT 1" if one("random") == "1" else " ORDER BY r.doc_id,r.pdf_page,r.region_id LIMIT 30 OFFSET ?"
                    rows = db.execute("SELECT r.region_id,r.doc_id,r.pdf_page,r.cell_count,r.issue_count" + sql + order,
                                      params if one("random") == "1" else (*params, offset))
                    return self.send_body({"total": total, "rows": [dict(r) for r in rows]})
                if url.path in {"/api/region", "/api/image"}:
                    rid = one("id")
                    region = db.execute("SELECT * FROM regions WHERE region_id=?", (rid,)).fetchone()
                    if region is None:
                        return self.send_body({"error": "Unknown region"}, code=404)
                    if url.path == "/api/image":
                        path = region["header_image_path"] if one("kind") == "header" else region["image_path"]
                        if not path:
                            return self.send_body({"error": "No heading crop"}, code=404)
                        file = (ROOT / path).resolve()
                        if not file.is_relative_to(IMAGE_ROOT) or not file.is_file():
                            return self.send_body({"error": "Source crop missing"}, code=404)
                        return self.send_body(file.read_bytes(), "image/jpeg")
                    cells = []
                    if region["cells"]:
                        cells = [dict(zip(CELL_FIELDS, values)) for values in
                                 json.loads(zlib.decompress(region["cells"]))]
                    issues = [dict(r) for r in db.execute("SELECT row_id,issue,details FROM issues WHERE region_id=?", (rid,))]
                    return self.send_body({"region_id": rid, "doc_id": region["doc_id"],
                                           "pdf_page": region["pdf_page"], "source_pdf": region["source_pdf"],
                                           "table_ids": json.loads(region["table_ids"]),
                                           "header_image_path": region["header_image_path"],
                                           "cell_count": region["cell_count"], "issue_count": region["issue_count"],
                                           "cells": cells, "issues": issues})
            return self.send_body({"error": "Not found"}, code=404)

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Extraction QA dashboard ready: http://localhost:{args.port}", flush=True)
    print("Read-only snapshot; restart after a new extraction replay.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
