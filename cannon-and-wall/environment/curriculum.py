from pathlib import Path

STAGES = {
    1: {
        "file": "environment/vulnerable_app/stage_1/app.py",
        "vulns": ["sqli", "xss", "broken_auth"],
        "description": "Single-file login form — all three OWASP vulns visible",
    },
    2: {
        "file": "environment/vulnerable_app/stage_2/app.py",
        "vulns": ["sqli", "xss"],
        "description": "Split routes (/auth + /search) — two vulns, minor naming obfuscation",
    },
    3: {
        "file": "environment/vulnerable_app/stage_3/app.py",
        "vulns": ["sqli", "xss", "broken_auth"],
        "description": "Chained + obfuscated — query via join, XSS in attr, cookie auth bypass",
    },
}

def next_stage(current: int, scores: dict) -> int:
    """Escalate when Wall is consistently strong (raw reward > 8 / 25)."""
    if scores.get("wall", 0) > 8:
        return min(current + 1, max(STAGES.keys()))
    return current

def get_stage_source(stage: int) -> str:
    path = Path(STAGES[stage]["file"])
    if not path.exists():
        raise FileNotFoundError(f"Stage {stage} app not found at {path}")
    return path.read_text()