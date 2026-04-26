from pydantic import BaseModel
from typing import Optional

class CannonAction(BaseModel):
    agent: str = "cannon"
    vuln_type: str                    # "sqli" | "xss" | "broken_auth"
    file_path: str = "app.py"
    line_number: int
    explanation: str = ""
    proof_of_concept: str = ""
    confidence: float = 0.5

class WallAction(BaseModel):
    agent: str = "wall"
    file_path: str = "app.py"
    patched_code: str
    explanation: str = ""
    lines_changed: list[int] = []

class GameState(BaseModel):
    stage: int
    original_code: str
    round: int
    phase: str = "attack"
    cannon_report: Optional[dict] = None
    wall_patch: Optional[str] = None
    scores: dict = {"cannon": 0.0, "wall": 0.0}
    done: bool = False
