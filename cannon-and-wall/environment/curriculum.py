from pathlib import Path

STAGES = {
    1: {"file": "environment/vulnerable_app/stage_1/app.py",
        "vulns": ["sqli"], "description": "Single SQLi in login form"},
    2: {"file": "environment/vulnerable_app/stage_1/app.py",
        "vulns": ["xss"], "description": "Single XSS in comment box"},
    3: {"file": "environment/vulnerable_app/stage_1/app.py",
        "vulns": ["sqli", "xss", "broken_auth"], "description": "All three vulns"}
}

def next_stage(current: int, scores: dict) -> int:
    if scores.get("wall", 0) > 8:
        return min(current + 1, max(STAGES.keys()))
    return current

def get_stage_source(stage: int) -> str:
    return Path(STAGES[stage]["file"]).read_text()
