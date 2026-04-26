# ui/demo.py — V2 (Red vs Blue self-play leaderboard)
import gradio as gr
import json
import os
from datetime import datetime
from client.client import CannonWallClient

client = CannonWallClient()

# --- Persistent leaderboard (simple JSON file, reset-safe) ---
_LEADERBOARD_PATH = "leaderboard.json"

def _load_leaderboard() -> list:
    if os.path.exists(_LEADERBOARD_PATH):
        with open(_LEADERBOARD_PATH) as f:
            return json.load(f)
    return []

def _save_leaderboard(records: list):
    with open(_LEADERBOARD_PATH, "w") as f:
        json.dump(records, f, indent=2)

def _leaderboard_table(records: list) -> str:
    if not records:
        return "No episodes recorded yet."
    header = "| # | Time | Stage | Cannon | Wall | Winner |\n|---|---|---|---|---|---|\n"
    rows = ""
    for i, r in enumerate(reversed(records[-20:]), 1):
        winner = "🔴 Cannon" if r["cannon"] > r["wall"] else ("🔵 Wall" if r["wall"] > r["cannon"] else "⚖️ Tie")
        rows += f"| {i} | {r['time']} | {r['stage']} | {r['cannon']:.3f} | {r['wall']:.3f} | {winner} |\n"
    return header + rows


# --- Episode actions ---
def start_round(stage):
    obs = client.reset(stage=int(stage))
    source = obs.get("source_code", "")
    return source, f"✅ Round started — Stage {stage} loaded.", ""

def get_scores():
    s = client.state()
    scores = s.get("scores", {})
    stage  = s.get("stage", 1)
    rnd    = s.get("round", 1)
    cannon = scores.get("cannon", 0)
    wall   = scores.get("wall", 0)

    # Record to leaderboard when round advances past 1
    if rnd > 1:
        records = _load_leaderboard()
        records.append({
            "time":   datetime.utcnow().strftime("%H:%M:%S"),
            "stage":  stage,
            "cannon": round(cannon, 3),
            "wall":   round(wall, 3),
        })
        _save_leaderboard(records)

    return (
        f"🔴 Cannon: {cannon:.3f} | 🔵 Wall: {wall:.3f} | "
        f"Round: {rnd} | Stage: {stage}"
    )

def refresh_leaderboard():
    records = _load_leaderboard()
    cannon_total = sum(r["cannon"] for r in records) if records else 0
    wall_total   = sum(r["wall"]   for r in records) if records else 0
    n = len(records)
    summary = (
        f"**Total episodes:** {n}  |  "
        f"🔴 Cannon avg: {cannon_total/n:.3f}  |  "
        f"🔵 Wall avg: {wall_total/n:.3f}"
        if n > 0 else "No episodes yet."
    )
    return summary, _leaderboard_table(records)


# --- Gradio UI ---
with gr.Blocks(title="🔴🔵 Cannon & Wall — RedBlue Arena") as demo:
    gr.Markdown("# 🔴🔵 Cannon & Wall — RedBlue Arena")
    gr.Markdown(
        "_A self-improving attacker vs defender RL environment. "
        "Start an episode, run agents via the API, then refresh scores._"
    )

    with gr.Tab("▶️ Run Episode"):
        stage_dd  = gr.Dropdown([1, 2, 3], value=1, label="Curriculum Stage")
        start_btn = gr.Button("🚀 Start Round", variant="primary")
        source_box = gr.Textbox(label="📄 Source Code", lines=22, interactive=False)
        status_box = gr.Textbox(label="Status")
        output_box = gr.Textbox(label="Agent Output")
        start_btn.click(
            start_round,
            inputs=[stage_dd],
            outputs=[source_box, status_box, output_box],
        )

    with gr.Tab("📊 Live Scores"):
        score_btn = gr.Button("🔄 Refresh Scores")
        score_box = gr.Textbox(label="Current Episode Scores", interactive=False)
        score_btn.click(get_scores, outputs=[score_box])

    with gr.Tab("🏆 Leaderboard"):
        gr.Markdown(
            "Live win-rate tracker across all episodes. "
            "Scores persist across resets."
        )
        lb_btn     = gr.Button("🔄 Refresh Leaderboard")
        lb_summary = gr.Markdown()
        lb_table   = gr.Markdown()
        lb_btn.click(refresh_leaderboard, outputs=[lb_summary, lb_table])
        # Auto-load on tab open
        demo.load(refresh_leaderboard, outputs=[lb_summary, lb_table])

    with gr.Tab("🔌 API Reference"):
        gr.Markdown("""
## Endpoints
| Method | Path | Description |
|---|---|---|
| POST | `/reset?stage=1` | Start new episode, returns source code |
| POST | `/step` | Send agent action, returns reward + breakdown |
| GET  | `/state` | Read current episode state |
| GET  | `/docs` | FastAPI Swagger UI |

## Cannon action schema
```json
{
  "agent": "cannon",
  "vuln_type": "sqli",
  "line_number": 16,
  "explanation": "Username parameter interpolated directly into SQL",
  "proof_of_concept": "' OR 1=1-- "
}
```

## Wall action schema
```json
{
  "agent": "wall",
  "patched_code": "...full patched app.py...",
  "explanation": "Replaced f-string query with parameterized execute()"
}
```
        """)

if __name__ == "__main__":
    demo.launch(server_port=7861)