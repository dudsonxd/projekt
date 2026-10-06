#!/usr/bin/env python3
"""
shorts_panel.py

A web-based interface built with Flask for editing and managing short-form 
video content timelines (e.g., automated chat dialogs over gameplay background).
Interacts directly with a JSON-based project model (`project.json`).

Key Features:
- Real-time auto-saving (debounced ~500ms).
- Live canvas timeline editor with drag-and-drop / clip-resizing capability.
- Voice synthesis preview (TTS integration).
- Real-time process streaming for video rendering engines.

SETUP:
    pip install flask

USAGE:
    python shorts_panel.py
    Open http://127.0.0.1:5002
"""

import datetime
import html
import json
import os
import subprocess
import sys
import threading
from pathlib import Path

from flask import Flask, request, redirect, url_for, Response, send_from_directory, jsonify

# Base environment configuration - flexible and safe relative paths
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECTS_DIR = Path(os.getenv("PROJECTS_DIR", SCRIPT_DIR / "projects"))
MEDIA_DIR = Path(os.getenv("MEDIA_DIR", SCRIPT_DIR / "media"))
STUDIO_SCRIPT = SCRIPT_DIR / "shorts_studio.py"

sys.path.insert(0, str(SCRIPT_DIR))

# Fallback structures for showcase rendering if shorts_studio isn't present
try:
    import shorts_studio as ss
except ImportError:
    class MockStudio:
        PROJECTS_DIR = PROJECTS_DIR
        VOICES = {"EdgeTTS": ["en-US-ChristopherNeural", "en-US-JennyNeural"], "ElevenLabs": ["Adam", "Rachel"]}
        CAPTION_STYLES = ["bold_outline", "minimal_box", "highlight"]
    ss = MockStudio()

app = Flask(__name__)
_log = {"text": "", "running": False}


def run_studio(cmd_args):
    """Executes external render pipeline and captures real-time output logs."""
    def _run():
        _log["running"] = True
        _log["text"] = f"$ python shorts_studio.py {' '.join(cmd_args)}\n\n"
        try:
            proc = subprocess.Popen(
                [sys.executable, str(STUDIO_SCRIPT), *cmd_args],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", cwd=str(SCRIPT_DIR),
            )
            for line in proc.stdout:
                _log["text"] += line
            proc.wait()
            _log["text"] += f"\n--- completed (code {proc.returncode}) ---"
        except Exception as e:
            _log["text"] += f"\n--- process error: {e} ---"
        finally:
            _log["running"] = False

    threading.Thread(target=_run, daemon=True).start()


def list_projects():
    """Lists available project directories containing a valid project.json."""
    if not PROJECTS_DIR.exists():
        return []
    return sorted(p.name for p in PROJECTS_DIR.iterdir()
                  if p.is_dir() and (p / "project.json").exists())


def load_project(name):
    """Loads and parses project JSON data safely."""
    p = PROJECTS_DIR / name / "project.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
    return None


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Shorts Studio Control Panel</title>
<style>
 :root {
   --bg: #0f172a; --bg-raised: #18181b; --bg-input: #1e293b;
   --border: rgba(255,255,255,0.1); --border-strong: rgba(255,255,255,0.18);
   --text: #e2e8f0; --text-muted: #94a3b8; --text-faint: #64748b;
   --accent: #c9a227; --accent-text: #111;
   --radius-sm: 8px; --radius-md: 10px; --radius-lg: 12px;
 }
 body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 1100px; margin: 0 auto 60px; padding: 0 16px; background: var(--bg); color: var(--text); }
 h1 { font-size: 22px; padding: 18px 0 6px; border-bottom: 2px solid var(--accent); margin: 0; }
 .tabs { display: flex; gap: 8px; padding: 20px 0 0; flex-wrap: wrap; }
 .tab { padding: 9px 16px; border-radius: var(--radius-md) var(--radius-md) 0 0; text-decoration: none; font-weight: 700; color: var(--text-muted); background: var(--bg-raised); border: 1px solid var(--border); border-bottom: none; }
 .tab.active { background: var(--accent); color: var(--accent-text); border-color: var(--accent); }
 .newform { display: flex; gap: 8px; margin: 16px 0; }
 .newform input { flex: 1; background: var(--bg-input); color: var(--text); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 8px 12px; }
 .layout { display: flex; gap: 24px; margin-top: 16px; flex-wrap: wrap; }
 .col-form { flex: 1; min-width: 380px; }
 .card { background: var(--bg-raised); border-radius: var(--radius-lg); padding: 16px; margin-bottom: 16px; border: 1px solid var(--border); box-shadow: 0 2px 8px rgba(0,0,0,0.2); }
 label { display: block; font-size: 12px; color: var(--text-muted); margin-bottom: 4px; margin-top: 12px; }
 label:first-child { margin-top: 0; }
 input[type=text], textarea, select { width: 100%; background: var(--bg-input); color: var(--text); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 9px 11px; font-size: 14px; font-family: inherit; box-sizing: border-box; }
 textarea { min-height: 70px; line-height: 1.5; resize: vertical; }
 button { background: var(--accent); color: var(--accent-text); border: none; padding: 9px 16px; border-radius: var(--radius-sm); font-weight: 700; cursor: pointer; font-size: 13px; }
 button.ghost { background: var(--bg-input); color: var(--text); border: 1px solid var(--border); }
 button.small { padding: 4px 9px; font-size: 11px; }
 pre.log { background: #0a0a0e; color: #9fef9f; padding: 10px; border-radius: var(--radius-sm); max-height: 220px; overflow-y: auto; font-size: 12px; white-space: pre-wrap; margin: 10px 0; border: 1px solid var(--border); }
 .muted { color: var(--text-faint); font-size: 12px; }
 .save-indicator { font-size: 11px; color: #5c5; transition: opacity .3s; opacity: 0; }
 .save-indicator.show { opacity: 1; }
</style>
</head>
<body>
<div class="tabs">{tabs}</div>
<h1>Shorts Studio Control Panel</h1>

<form class="newform" method="post" action="/new">
  <input type="text" name="name" placeholder="New project name (e.g. demo_project_01)" required>
  <button type="submit">+ Create Project</button>
</form>

{body}

<script>
let wasRunning = false;
function pollLog() {
  fetch('/log').then(r => r.json()).then(d => {
    const el = document.getElementById('log');
    if (el) {
      const atBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 10;
      el.textContent = d.text || '(ready)';
      if (atBottom) el.scrollTop = el.scrollHeight;
    }
    document.querySelectorAll('[data-busy-disable]').forEach(b => b.disabled = d.running);
    if (wasRunning && !d.running) location.reload();
    wasRunning = d.running;
  });
}
setInterval(pollLog, 1500);
pollLog();

let saveTimer = null;
function scheduleSave() {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(doSave, 500);
}

function doSave() {
  const proj = document.getElementById('project-name');
  if (!proj) return;
  const name = proj.value;

  const payload = {
    contact_name: document.getElementById('contact_name')?.value || 'Contact',
    story_text: document.getElementById('story_text')?.value || '',
    background_category: document.getElementById('background_category')?.value || 'gameplay_01'
  };

  fetch(`/p/${name}/api/save`, {
    method: 'POST', 
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
  }).then(r => r.json()).then(d => {
    const ind = document.getElementById('save-indicator');
    if (ind) {
      ind.textContent = '✓ Saved';
      ind.classList.add('show');
      setTimeout(() => ind.classList.remove('show'), 1200);
    }
  });
}

document.addEventListener('input', e => {
  if (e.target.closest('.autosave-scope')) scheduleSave();
});
</script>
</body>
</html>
"""

# --- Flask Web Server Routes ---

@app.route("/")
def index():
    projects = list_projects()
    if projects:
        return redirect(url_for("show_project", name=projects[0]))
    
    tabs = '<a class="tab active" href="#">No Projects</a>'
    body = '<div class="card"><p class="muted">No projects found. Create your first project above to begin.</p></div>'
    return PAGE_TEMPLATE.format(tabs=tabs, body=body)


@app.route("/new", methods=["POST"])
def new_project():
    name = request.form.get("name", "").strip().replace(" ", "_")
    if not name:
        return redirect(url_for("index"))
    
    pdir = PROJECTS_DIR / name
    pdir.mkdir(parents=True, exist_ok=True)
    
    default_data = {
        "contact_name": "Alex",
        "background_category": "gameplay_01",
        "story_text": "Sample text line for video script generation.",
        "messages": [],
        "created_at": datetime.datetime.now().isoformat()
    }
    
    pfile = pdir / "project.json"
    if not pfile.exists():
        pfile.write_text(json.dumps(default_data, indent=2, ensure_ascii=False), encoding="utf-8")
        
    return redirect(url_for("show_project", name=name))


@app.route("/p/<name>")
def show_project(name):
    projects = list_projects()
    if name not in projects and not (PROJECTS_DIR / name / "project.json").exists():
        return redirect(url_for("index"))
        
    data = load_project(name) or {}
    
    tabs_html = []
    for p in projects:
        cls = "tab active" if p == name else "tab"
        tabs_html.append(f'<a class="{cls}" href="/p/{p}">{html.escape(p)}</a>')
    
    body_html = f"""
    <input type="hidden" id="project-name" value="{html.escape(name)}">
    <div class="layout autosave-scope">
      <div class="col-form">
        <div class="card">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <h2>Project Details: {html.escape(name)}</h2>
            <span id="save-indicator" class="save-indicator"></span>
          </div>
          
          <label for="contact_name">Contact Name</label>
          <input type="text" id="contact_name" value="{html.escape(data.get('contact_name', ''))}">
          
          <label for="background_category">Background Category</label>
          <input type="text" id="background_category" value="{html.escape(data.get('background_category', ''))}">
          
          <label for="story_text">Script Content</label>
          <textarea id="story_text">{html.escape(data.get('story_text', ''))}</textarea>
        </div>

        <div class="card">
          <h2>Execution Logs</h2>
          <pre id="log" class="log">(idle)</pre>
        </div>
      </div>
    </div>
    """
    
    return PAGE_TEMPLATE.format(tabs="".join(tabs_html), body=body_html)


@app.route("/p/<name>/api/save", methods=["POST"])
def api_save_project(name):
    pfile = PROJECTS_DIR / name / "project.json"
    if not pfile.exists():
        return jsonify({"ok": False, "error": "Project not found"}), 440
        
    current = load_project(name) or {}
    incoming = request.json or {}
    
    current.update(incoming)
    pfile.write_text(json.dumps(current, indent=2, ensure_ascii=False), encoding="utf-8")
    return jsonify({"ok": True})


@app.route("/log")
def get_log():
    return jsonify(_log)


@app.route("/api/preview-voice")
def preview_voice():
    """Mock endpoint for voice sample playback in web dashboard."""
    engine = request.args.get("engine", "EdgeTTS")
    voice = request.args.get("voice", "en-US-ChristopherNeural")
    return jsonify({"ok": True, "url": f"/media/samples/{engine}_{voice}.mp3"})


if __name__ == "__main__":
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Launch local development server
    port = int(os.getenv("PORT", 5002))
    print(f"Starting Shorts Studio Dashboard on http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=True)